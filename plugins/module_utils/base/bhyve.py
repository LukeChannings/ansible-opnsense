from os import path as os_path
from os import stat as os_stat
from tempfile import mkstemp

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.oxlorg.opnsense.plugins.module_utils.helper.bhyve import \
    BhyveError, parse_conf, parse_datastore

VM_CMD = '/usr/local/sbin/vm'


class BhyveHost:
    """Everything the bhyve modules do to the OPNsense host they run on.

    Unlike the api-modules of this collection these run on the firewall itself
    (see ADR-0001), so the configuration files are read and written directly and
    only the tools that own state of their own - 'vm', 'sysrc', 'zfs', 'pkg' -
    are shelled out to.
    """

    def __init__(self, module: AnsibleModule):
        self.m = module

    def run(self, cmd: list, check_rc: bool = True) -> tuple:
        rc, stdout, stderr = self.m.run_command([str(arg) for arg in cmd])

        if check_rc and rc != 0:
            raise BhyveError(
                f"failed to run '{' '.join(str(arg) for arg in cmd)}': "
                f'{stderr.strip() or stdout.strip()}'
            )

        return rc, stdout, stderr

    def vm(self, args: list, check_rc: bool = True) -> tuple:
        return self.run([VM_CMD, *args], check_rc=check_rc)

    # files

    @staticmethod
    def exists(file_path: str) -> bool:
        return os_path.exists(file_path)

    @staticmethod
    def size_of(file_path: str) -> int:
        """Size of a disk image in bytes, or None if it does not exist yet."""
        if not os_path.exists(file_path):
            return None

        return os_stat(file_path).st_size

    @staticmethod
    def read(file_path: str) -> str:
        if not os_path.exists(file_path):
            return ''

        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()

    def read_conf(self, file_path: str) -> dict:
        return parse_conf(self.read(file_path))

    def write(self, file_path: str, content: str) -> None:
        handle, tmp_path = mkstemp(dir=os_path.dirname(file_path))

        with open(handle, 'w', encoding='utf-8') as file:
            file.write(content)

        self.m.atomic_move(tmp_path, file_path)

    # interfaces

    def bridges(self) -> list:
        """The bridge interfaces of the host, which switches attach to.

        Bridges belong to OPNsense's own interface configuration - see the
        'interface_bridge' module - so they are only ever read here.
        """
        return self.run(['ifconfig', '-g', 'bridge'])[1].split()

    # rc.conf

    def sysrc_get(self, key: str) -> str:
        rc, stdout, _ = self.run(['sysrc', '-n', key], check_rc=False)

        if rc != 0:
            return None

        return stdout.strip()

    def sysrc_set(self, key: str, value: str) -> None:
        self.run(['sysrc', f'{key}={value}'])

    # datastore

    def datastore_path(self, spec: str) -> str:
        """Resolves a datastore specification to the directory vm-bhyve uses."""
        scheme, location = parse_datastore(spec)

        if scheme != 'zfs':
            return location

        rc, stdout, _ = self.run(
            ['zfs', 'list', '-H', '-o', 'mountpoint', location], check_rc=False
        )

        if rc != 0:
            raise BhyveError(f"dataset '{location}' of the datastore does not exist")

        return stdout.strip()

    def vm_dir(self) -> str:
        """The directory of the default datastore, as configured in rc.conf.

        Fails the task when vm-bhyve has not been set up, rather than letting the
        caller work on a host where no 'vm' command would run at all.
        """
        if (self.sysrc_get('vm_enable') or '').upper() not in ['YES', 'TRUE', 'ON', '1']:
            raise BhyveError(
                "vm-bhyve is not enabled on this host - run the 'bhyve_general' "
                'module against it first'
            )

        spec = self.sysrc_get('vm_dir')
        if not spec:
            raise BhyveError(
                "vm-bhyve has no datastore configured - run the 'bhyve_general' "
                'module against it first'
            )

        resolved = self.datastore_path(spec)
        if not os_path.isdir(resolved):
            raise BhyveError(
                f"the vm-bhyve datastore '{spec}' is not a directory on this host - "
                "run the 'bhyve_general' module against it first"
            )

        return resolved

    def system_conf(self) -> dict:
        """The host-wide vm-bhyve configuration, which holds the switches."""
        return self.read_conf(f'{self.vm_dir()}/.config/system.conf')


class BhyveModule:
    """Shared shape of the bhyve modules: check what is, then make it so."""

    def __init__(self, module: AnsibleModule, result: dict):
        self.m = module
        self.p = module.params
        self.r = result
        self.h = BhyveHost(module)

    def check(self) -> None:
        raise NotImplementedError

    def process(self) -> None:
        raise NotImplementedError


def bhyve_module_wrapper(instance: BhyveModule) -> None:
    """Runs a bhyve module, turning its failures into a failed task."""
    try:
        instance.check()
        instance.process()

    except BhyveError as error:
        instance.m.fail_json(msg=str(error), **instance.r)
