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
    from ansible_collections.oxlorg.opnsense.plugins.module_utils.main.bhyve_general import General

except MODULE_EXCEPTIONS:
    module_dependency_error()

# DOCUMENTATION = 'https://ansible-opnsense.oxl.app/modules/bhyve_general.html'
# EXAMPLES = 'https://ansible-opnsense.oxl.app/modules/bhyve_general.html'


def run_module():
    module_args = dict(
        enabled=dict(
            type='bool', required=False, default=True,
            description='Whether this host should run bhyve guests at all. '
                        "Disabling only stops vm-bhyve from starting; it neither "
                        'removes packages nor touches existing guests',
        ),
        dir=dict(
            type='str', required=False, aliases=['datastore', 'vm_dir'],
            description="Where guests are stored, as a vm-bhyve datastore "
                        "specification - either a path or 'zfs:<dataset>'. A missing "
                        'dataset is created. If omitted, the configured datastore is '
                        'left alone',
        ),
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

    bhyve_module_wrapper(General(module=module, result=result))
    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
