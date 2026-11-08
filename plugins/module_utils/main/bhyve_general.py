from shutil import rmtree
from tempfile import mkdtemp

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.oxlorg.opnsense.plugins.module_utils.base.bhyve import \
    BhyveModule
from ansible_collections.oxlorg.opnsense.plugins.module_utils.helper.bhyve import \
    BhyveError, parse_datastore

# 'bhyve-firmware' pulls in 'edk2-bhyve', the uefi firmware guests boot with
PACKAGES = ['vm-bhyve', 'grub2-bhyve', 'bhyve-firmware']

# the repositories a package may be installed from. The last entry re-enables the
# FreeBSD-ports repository that OPNsense ships disabled, for this one transaction
# only - see ADR-0002. OPNsense keeps its higher priority, so its own builds still
# win wherever both repositories carry a package.
REPO_DIRS = ['/etc/pkg', '/usr/local/etc/pkg/repos']
REPO_OVERLAY = 'FreeBSD-ports: { enabled: yes }\n'


class General(BhyveModule):
    def __init__(self, module: AnsibleModule, result: dict):
        BhyveModule.__init__(self=self, module=module, result=result)
        self.missing_packages = []
        self.before = {}
        self.after = {}

    def check(self) -> None:
        if self.p['dir'] is not None:
            parse_datastore(self.p['dir'])

        self.missing_packages = [
            package for package in PACKAGES
            if self.h.run(['pkg', 'info', '-e', package], check_rc=False)[0] != 0
        ]

        self.before = {
            'enabled': self._enabled(),
            'dir': self.h.sysrc_get('vm_dir'),
            'packages_missing': self.missing_packages,
        }
        self.after = {
            'enabled': self.p['enabled'],
            'dir': self.p['dir'] if self.p['dir'] is not None else self.before['dir'],
            'packages_missing': [] if self.p['enabled'] else self.missing_packages,
        }

        self.r['diff']['before'] = self.before
        self.r['diff']['after'] = self.after
        self.r['changed'] = self.before != self.after

    def _enabled(self) -> bool:
        return (self.h.sysrc_get('vm_enable') or '').upper() in ['YES', 'TRUE', 'ON', '1']

    def process(self) -> None:
        if not self.p['enabled']:
            self._disable()
            return

        if not self.r['changed']:
            return

        if self.m.check_mode:
            return

        # the order matters: every 'vm' command refuses to run while vm_enable is
        # not set, and it needs a datastore directory to exist once it does
        self._install_packages()
        self.h.sysrc_set('vm_enable', 'YES')

        if self.p['dir'] is not None:
            self._create_datastore()
            self.h.sysrc_set('vm_dir', self.p['dir'])

        if not self.h.sysrc_get('vm_dir'):
            raise BhyveError(
                "vm-bhyve has no datastore configured - pass 'dir' to say where "
                'guests should be stored'
            )

        self.h.vm(['init'])

    def _disable(self) -> None:
        if not self.before['enabled']:
            return

        self.r['changed'] = True

        if not self.m.check_mode:
            self.h.sysrc_set('vm_enable', 'NO')

    def _create_datastore(self) -> None:
        scheme, location = parse_datastore(self.p['dir'])

        if scheme != 'zfs':
            return

        if self.h.run(['zfs', 'list', location], check_rc=False)[0] == 0:
            return

        self.h.run(['zfs', 'create', '-p', location])

    def _install_packages(self) -> None:
        if len(self.missing_packages) == 0:
            return

        overlay = mkdtemp(prefix='ansible-bhyve-repos.')

        try:
            self.h.write(f'{overlay}/zz-ansible-bhyve.conf', REPO_OVERLAY)
            self.h.run([
                'pkg',
                '-o', f"REPOS_DIR={','.join([*REPO_DIRS, overlay])}",
                '-o', 'ASSUME_ALWAYS_YES=yes',
                'install', '-y', *self.missing_packages,
            ])

        finally:
            rmtree(overlay, ignore_errors=True)
