#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (C) 2025, Pascal Rath <contact+opnsense@OXL.at>
# GNU General Public License v3.0+ (see https://www.gnu.org/licenses/gpl-3.0.txt)

# see: https://docs.opnsense.org/development/api/plugins/quagga.html

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.oxlorg.opnsense.plugins.module_utils.base.handler import \
    module_dependency_error, MODULE_EXCEPTIONS

try:
    from ansible_collections.oxlorg.opnsense.plugins.module_utils.base.wrapper import module_wrapper
    from ansible_collections.oxlorg.opnsense.plugins.module_utils.defaults.main import \
        OPN_MOD_ARGS, STATE_MOD_ARG, RELOAD_MOD_ARG
    from ansible_collections.oxlorg.opnsense.plugins.module_utils.main.frr_ospf3_area import Area

except MODULE_EXCEPTIONS:
    module_dependency_error()


# DOCUMENTATION = 'https://ansible-opnsense.oxl.app/modules/frr_ospf.html'
# EXAMPLES = 'https://ansible-opnsense.oxl.app/modules/frr_ospf.html'


def run_module():
    module_args = dict(
        area=dict(
            type='str', required=True, aliases=['id', 'area_id'],
            description='Area in wildcard mask style like 0.0.0.0 and no decimal 0'
        ),
        ranges=dict(
            type='list', required=False, elements='str', default=[], aliases=['range'],
            description='IPv6 networks to summarize this area with'
        ),
        type=dict(
            type='str', required=False, default='normal',
            choices=['normal', 'nssa', 'nssa no-summary'],
            description='The type of this area'
        ),
        prefix_list_in=dict(
            type='str', required=False, aliases=['prefix_in'],
            description='Prefix-list to filter incoming routes of this area'
        ),
        prefix_list_out=dict(
            type='str', required=False, aliases=['prefix_out'],
            description='Prefix-list to filter outgoing routes of this area'
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

    module_wrapper(Area(module=module, result=result))
    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
