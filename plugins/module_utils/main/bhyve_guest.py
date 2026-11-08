from ansible.module_utils.basic import AnsibleModule

from ansible_collections.oxlorg.opnsense.plugins.module_utils.base.bhyve import \
    BhyveModule
from ansible_collections.oxlorg.opnsense.plugins.module_utils.helper.bhyve import \
    BhyveError, apply_autostart, build_guest_conf, conf_diff, is_valid_name, \
    parse_datastore, plan_disks, plan_running, render_conf, switch_names


class Guest(BhyveModule):
    def __init__(self, module: AnsibleModule, result: dict):
        BhyveModule.__init__(self=self, module=module, result=result)
        self.dir = None
        self.path = None
        self.conf_path = None
        self.exists = False
        self.existing = {}
        self.desired = {}
        self.disks = []
        self.running_now = False
        self.running_actions = []
        self.autostart_before = []
        self.autostart_after = []

    # check

    def check(self) -> None:
        if not is_valid_name(self.p['name']):
            raise BhyveError(f"'{self.p['name']}' is not a valid guest name")

        self.dir = self.h.vm_dir()
        self.path = f"{self.dir}/{self.p['name']}"
        self.conf_path = f"{self.path}/{self.p['name']}.conf"
        self.exists = self.h.exists(self.conf_path)
        self.existing = self.h.read_conf(self.conf_path)
        self.running_now = self.h.is_running(self.p['name'])

        self._check_autostart()

        if self.p['state'] == 'absent':
            self._check_absent()
            return

        self._check_present()

    def _check_absent(self) -> None:
        self.r['diff']['before'] = {'state': 'present' if self.exists else 'absent'}
        self.r['diff']['after'] = {'state': 'absent'}
        self.r['changed'] = self.exists or self.autostart_before != self.autostart_after

    def _check_present(self) -> None:
        if not self.exists:
            self._check_creatable()

        self._check_switches()
        self.desired = build_guest_conf(existing=self.existing, params=self.p)
        self._check_image()

        if self.p['disks'] is not None:
            self.disks = plan_disks(self.desired, self.p['disks'], self._disk_sizes())

        diff = conf_diff(self.existing, self.desired)
        conf_changed = len(diff['before']) > 0 or len(diff['after']) > 0

        self.running_actions = plan_running(
            running_now=self.running_now,
            running_wanted=self.p['running'],
            conf_changed=conf_changed,
            restart_on_change=self.p['restart_on_change'],
        )

        if conf_changed and self.running_now and self.running_actions == []:
            self.m.warn(
                f"guest '{self.p['name']}' is running and keeps its current "
                "configuration until it is restarted - set 'restart_on_change' "
                'to apply it right away'
            )

        self.r['diff']['before'] = {
            **diff['before'],
            'state': 'present' if self.exists else 'absent',
            'running': self.running_now,
            'autostart': self.p['name'] in self.autostart_before,
        }
        self.r['diff']['after'] = {
            **diff['after'],
            'state': 'present',
            'running': self.running_now if self.p['running'] is None else self.p['running'],
            'autostart': self.p['name'] in self.autostart_after,
        }
        self.r['changed'] = (
            not self.exists
            or conf_changed
            or len(self.running_actions) > 0
            or self.autostart_before != self.autostart_after
            or any(disk['action'] != 'keep' for disk in self.disks)
        )

    def _check_creatable(self) -> None:
        if self.p['disks'] is None or len(self.p['disks']) == 0:
            raise BhyveError(
                f"guest '{self.p['name']}' does not exist yet - declare at least "
                "one entry in 'disks' to create it"
            )

    def _check_switches(self) -> None:
        """Refuses nics on switches that do not exist, which would fail at boot."""
        if self.p['nics'] is None:
            return

        known = switch_names(self.h.system_conf())

        for nic in self.p['nics']:
            if nic['switch'] not in known:
                raise BhyveError(
                    f"'{nic['switch']}' is not a switch on this host - create it "
                    f"with the 'bhyve_switch' module first. "
                    f"Available: {', '.join(known) if known else 'none'}"
                )

    def _check_image(self) -> None:
        if self.p['image'] is None:
            return

        if not self.h.exists(self.p['image']):
            raise BhyveError(f"image '{self.p['image']}' does not exist on the host")

    def _check_autostart(self) -> None:
        self.autostart_before = (self.h.sysrc_get('vm_list') or '').split()

        if self.p['state'] == 'absent':
            self.autostart_after = apply_autostart(
                self.autostart_before, self.p['name'], enabled=False,
            )
            return

        if self.p['autostart'] is None:
            self.autostart_after = self.autostart_before
            return

        self.autostart_after = apply_autostart(
            self.autostart_before, self.p['name'], enabled=self.p['autostart'],
        )

    def _disk_sizes(self) -> dict:
        """The current size of each declared disk's image file, by position."""
        return {
            index: self.h.size_of(f"{self.path}/{self.desired[f'disk{index}_name']}")
            for index in range(len(self.p['disks']))
        }

    # process

    def process(self) -> None:
        if self.p['state'] == 'absent':
            self._destroy()
            return

        if not self.r['changed'] or self.m.check_mode:
            return

        if not self.exists:
            self._create_guest_dir()

        self.h.write(self.conf_path, render_conf(self.desired))
        self._apply_disks()
        self._apply_autostart()

        for action in self.running_actions:
            if action == 'stop':
                self.h.stop_guest(self.p['name'], timeout=self.p['stop_timeout'])

            else:
                self.h.vm(['start', self.p['name']])

    def _create_guest_dir(self) -> None:
        """Creates the guest's home, as a dataset of its own where vm-bhyve uses zfs."""
        scheme, location = parse_datastore(self.h.vm_dir_spec())

        if scheme == 'zfs':
            self.h.run(['zfs', 'create', f"{location}/{self.p['name']}"])

        else:
            self.h.make_dir(self.path)

    def _apply_disks(self) -> None:
        for disk in self.disks:
            if disk['action'] == 'keep':
                continue

            image_path = f"{self.path}/{disk['name']}"

            if disk['action'] == 'create' and disk['index'] == 0 and self.p['image'] is not None:
                self._seed_from_image(image_path, disk['size'])

            self.h.run(['truncate', '-s', disk['size'], image_path])

    def _seed_from_image(self, image_path: str, size: int) -> None:
        """Copies the declared image onto a disk that has none yet.

        Only ever done while the disk is missing, so re-running the module never
        overwrites a guest that has since written to it. Deleting the disk is the
        deliberate act that asks for the guest to be installed again.
        """
        if self.h.size_of(self.p['image']) > size:
            raise BhyveError(
                f"image '{self.p['image']}' is larger than the {size} bytes declared "
                'for the disk it seeds'
            )

        self.h.copy(self.p['image'], image_path)

    def _apply_autostart(self) -> None:
        if self.autostart_before == self.autostart_after:
            return

        self.h.sysrc_set('vm_list', ' '.join(self.autostart_after))

    def _destroy(self) -> None:
        if not self.r['changed'] or self.m.check_mode:
            return

        self._apply_autostart()

        if not self.exists:
            return

        self.h.stop_guest(self.p['name'], timeout=self.p['stop_timeout'])
        self.h.vm(['destroy', '-f', self.p['name']])
