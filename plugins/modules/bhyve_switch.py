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
    from ansible_collections.oxlorg.opnsense.plugins.module_utils.main.bhyve_switch import Switch

except MODULE_EXCEPTIONS:
    module_dependency_error()

# DOCUMENTATION = 'https://ansible-opnsense.oxl.app/modules/bhyve_switch.html'
# EXAMPLES = 'https://ansible-opnsense.oxl.app/modules/bhyve_switch.html'


def run_module():
    module_args = dict(
        name=dict(
            type='str', required=True, aliases=['switch'],
            description='Name guests use to reference this switch',
        ),
        bridge=dict(
            type='str', required=False,
            description='Existing bridge interface the switch attaches to. The '
                        "bridge itself belongs to OPNsense's interface configuration "
                        "- see the 'interface_bridge' module - and is never created "
                        'or changed here',
        ),
        **STATE_ONLY_MOD_ARG,
    )

    module = AnsibleModule(
        argument_spec=module_args,
        required_if=[('state', 'present', ['bridge'])],
        supports_check_mode=True,
    )

    result = dict(
        changed=False,
        diff={
            'before': {},
            'after': {},
        }
    )

    bhyve_module_wrapper(Switch(module=module, result=result))
    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
