#!/usr/bin/python
# -*- coding: utf-8 -*-

# GNU General Public License v3.0+ (see https://www.gnu.org/licenses/gpl-3.0.txt)

# see: https://github.com/opnsense/plugins/tree/master/net/udpbroadcastrelay

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.oxlorg.opnsense.plugins.module_utils.base.handler import \
    module_dependency_error, MODULE_EXCEPTIONS

try:
    from ansible_collections.oxlorg.opnsense.plugins.module_utils.base.wrapper import module_wrapper
    from ansible_collections.oxlorg.opnsense.plugins.module_utils.defaults.main import \
        OPN_MOD_ARGS, RELOAD_MOD_ARG
    from ansible_collections.oxlorg.opnsense.plugins.module_utils.defaults.udpbroadcastrelay import \
        UBR_MOD_ARGS
    from ansible_collections.oxlorg.opnsense.plugins.module_utils.main.udpbroadcastrelay import Relay

except MODULE_EXCEPTIONS:
    module_dependency_error()


# DOCUMENTATION = 'https://ansible-opnsense.oxl.app/modules/udpbroadcastrelay.html'
# EXAMPLES = 'https://ansible-opnsense.oxl.app/modules/udpbroadcastrelay.html'


def run_module():
    module_args = dict(
        **UBR_MOD_ARGS,
        **RELOAD_MOD_ARG,
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

    module_wrapper(Relay(module=module, result=result))
    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
