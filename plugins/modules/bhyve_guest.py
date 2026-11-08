#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (C) 2026, Luke Channings <contact@lukechannings.com>
# GNU General Public License v3.0+ (see https://www.gnu.org/licenses/gpl-3.0.txt)

# see: https://github.com/churchers/vm-bhyve

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.oxlorg.opnsense.plugins.module_utils.base.handler import \
    module_dependency_error, MODULE_EXCEPTIONS

try:
    from ansible_collections.oxlorg.opnsense.plugins.module_utils.base.bhyve import \
        bhyve_module_wrapper
    from ansible_collections.oxlorg.opnsense.plugins.module_utils.defaults.main import \
        STATE_ONLY_MOD_ARG
    from ansible_collections.oxlorg.opnsense.plugins.module_utils.helper.bhyve import \
        DISK_DEV_DEFAULT, DISK_TYPE_DEFAULT, NIC_TYPE_DEFAULT
    from ansible_collections.oxlorg.opnsense.plugins.module_utils.main.bhyve_guest import Guest

except MODULE_EXCEPTIONS:
    module_dependency_error()

# DOCUMENTATION = 'https://ansible-opnsense.oxl.app/modules/bhyve_guest.html'
# EXAMPLES = 'https://ansible-opnsense.oxl.app/modules/bhyve_guest.html'


def run_module():
    module_args = dict(
        name=dict(
            type='str', required=True, aliases=['guest'],
            description='Name of the guest',
        ),
        cpu=dict(
            type='int', required=False,
            description='Number of virtual cpus. Left as it is if omitted',
        ),
        memory=dict(
            type='str', required=False,
            description="Memory to give the guest, as a size like '2G'. "
                        'Left as it is if omitted',
        ),
        loader=dict(
            type='str', required=False, choices=['uefi', 'uefi-csm', 'bhyveload', 'grub'],
            description="How the guest is booted. 'uefi' is what a prebuilt raw image "
                        'usually wants. Left as it is if omitted',
        ),
        disks=dict(
            type='list', required=False, elements='dict',
            options=dict(
                size=dict(
                    type='str', required=True,
                    description="Size of the disk, like '20G'. A disk may grow, but "
                                'never shrink',
                ),
                type=dict(
                    type='str', required=False, default=DISK_TYPE_DEFAULT,
                    choices=['virtio-blk', 'ahci-hd', 'nvme'],
                    description='How the disk is attached to the guest',
                ),
                dev=dict(
                    type='str', required=False,
                    choices=['file', 'zvol', 'sparse-zvol'],
                    description=f"What backs the disk, '{DISK_DEV_DEFAULT}' for a new "
                                'one. A file lives in the guests directory; '
                                'a zvol is a volume below the guests dataset '
                                'and needs a zfs datastore. Zvols are thick unless '
                                "'sparse-zvol' is asked for. The backing of an existing "
                                'disk is kept when omitted and cannot be changed',
                ),
                volblocksize=dict(
                    type='str', required=False,
                    description="Block size of a zvol, like '128k'. Only ever applied "
                                'when the zvol is created - zfs cannot change it '
                                'afterwards. Ignored for file-backed disks',
                ),
            ),
            description='Disks of the guest, in order. The first one is the boot disk. '
                        'Disks can be added and grown; removing one from this list '
                        'fails rather than throwing its data away',
        ),
        nics=dict(
            type='list', required=False, elements='dict',
            options=dict(
                switch=dict(
                    type='str', required=True,
                    description="Switch the nic connects to - see the 'bhyve_switch' module",
                ),
                mac=dict(
                    type='str', required=False,
                    description='Mac-address to pin the nic to. If omitted, the one '
                                'vm-bhyve generated is kept',
                ),
                type=dict(
                    type='str', required=False, default=NIC_TYPE_DEFAULT,
                    choices=['virtio-net', 'e1000'],
                    description='How the nic is attached to the guest',
                ),
            ),
            description='Network interfaces of the guest, in order',
        ),
        image=dict(
            type='path', required=False,
            description='Path on the host to a prebuilt raw disk image. It seeds the '
                        'first disk whenever that disk has no image file yet, and is '
                        'ignored while the disk exists - so deleting the disk is what '
                        'asks for the guest to be installed again',
        ),
        running=dict(
            type='bool', required=False,
            description='Whether the guest should be running. Left as it is if omitted',
        ),
        autostart=dict(
            type='bool', required=False,
            description='Whether the guest starts with the host. Left as it is if omitted',
        ),
        restart_on_change=dict(
            type='bool', required=False, default=False,
            description='Restart a running guest so it picks up a changed configuration. '
                        'Without this the new configuration is written and applies at the '
                        'next start, so a routine run never interrupts a guest',
        ),
        stop_timeout=dict(
            type='int', required=False, default=90,
            description='Seconds a guest is given to shut down cleanly before it is '
                        'powered off',
        ),
        **STATE_ONLY_MOD_ARG,
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
    )

    result = dict(
        changed=False,
        diff={
            'before': {},
            'after': {},
        }
    )

    bhyve_module_wrapper(Guest(module=module, result=result))
    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
