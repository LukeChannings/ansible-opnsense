#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (C) 2026, Luke Channings <contact@lukechannings.com>
# GNU General Public License v3.0+ (see https://www.gnu.org/licenses/gpl-3.0.txt)

# see: https://github.com/opnsense/plugins/tree/master/net/tailscale

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.oxlorg.opnsense.plugins.module_utils.base.handler import \
    module_dependency_error, MODULE_EXCEPTIONS

try:
    from ansible_collections.oxlorg.opnsense.plugins.module_utils.base.wrapper import module_wrapper
    from ansible_collections.oxlorg.opnsense.plugins.module_utils.defaults.main import \
        OPN_MOD_ARGS, STATE_MOD_ARG, RELOAD_MOD_ARG
    from ansible_collections.oxlorg.opnsense.plugins.module_utils.main.tailscale_subnet import Subnet

except MODULE_EXCEPTIONS:
    module_dependency_error()

# DOCUMENTATION = 'https://ansible-opnsense.oxl.app/modules/tailscale.html'
# EXAMPLES = 'https://ansible-opnsense.oxl.app/modules/tailscale.html'


def run_module():
    module_args = dict(
        subnet=dict(
            type='str', required=False, aliases=['network', 'route', 'net'],
            description='Network in CIDR-notation to advertise to the tailnet. '
                        'The netmask is mandatory and the host-bits have to be unset',
        ),
        description=dict(type='str', required=False, default='', aliases=['desc']),
        match_fields=dict(
            type='list', required=False, elements='str',
            description='Fields that are used to match configured routes with the running config - '
                        "if any of those fields are changed, the module will think it's a new route",
            choices=['subnet', 'description'],
            default=['subnet'],
        ),
        **RELOAD_MOD_ARG,
        **STATE_MOD_ARG,
        **OPN_MOD_ARGS,
    )

    result = dict(
        changed=False,
        diff={
            'before': {},
            'after': {},
        }
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
    )

    module_wrapper(Subnet(module=module, result=result))
    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
