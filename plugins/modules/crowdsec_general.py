#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (C) 2026, Luke Channings <contact@lukechannings.com>
# GNU General Public License v3.0+ (see https://www.gnu.org/licenses/gpl-3.0.txt)

# see: https://github.com/opnsense/plugins/tree/master/security/crowdsec

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.oxlorg.opnsense.plugins.module_utils.base.handler import \
    module_dependency_error, MODULE_EXCEPTIONS

try:
    from ansible_collections.oxlorg.opnsense.plugins.module_utils.base.wrapper import module_wrapper
    from ansible_collections.oxlorg.opnsense.plugins.module_utils.defaults.main import \
        OPN_MOD_ARGS, RELOAD_MOD_ARG
    from ansible_collections.oxlorg.opnsense.plugins.module_utils.main.crowdsec_general import General

except MODULE_EXCEPTIONS:
    module_dependency_error()

# DOCUMENTATION = 'https://ansible-opnsense.oxl.app/modules/crowdsec_general.html'
# EXAMPLES = 'https://ansible-opnsense.oxl.app/modules/crowdsec_general.html'


def run_module():
    module_args = dict(
        agent_enabled=dict(
            type='bool', required=False, default=True, aliases=['agent'],
            description='Run the log-processor that parses local logs and detects attacks',
        ),
        lapi_enabled=dict(
            type='bool', required=False, default=True, aliases=['lapi'],
            description='Run the local API that stores decisions and serves them to bouncers',
        ),
        firewall_bouncer_enabled=dict(
            type='bool', required=False, default=True, aliases=['bouncer', 'firewall_bouncer'],
            description='Run the firewall-bouncer that feeds the decisions into the '
                        "'crowdsec_blocklists' and 'crowdsec6_blocklists' aliases",
        ),
        lapi_manual_configuration=dict(
            type='bool', required=False, default=False, aliases=['lapi_manual'],
            description="Leave the agents and bouncers local-API URLs and credentials alone. "
                        'Enable this if you point them at a remote local API by hand - '
                        "'lapi_listen_address' and 'lapi_listen_port' are then only used "
                        'by a locally running local API',
        ),
        lapi_listen_address=dict(
            type='str', required=False, default='127.0.0.1', aliases=['lapi_address'],
            description='IPv4- or IPv6-Address the local API should listen on',
        ),
        lapi_listen_port=dict(
            type='int', required=False, default=8080, aliases=['lapi_port'],
            description='TCP port the local API should listen on',
        ),
        rules_enabled=dict(
            type='bool', required=False, default=True, aliases=['rules'],
            description='Register the internal block-rules that drop traffic from and to the '
                        'CrowdSec blocklist-aliases',
        ),
        rules_log=dict(
            type='bool', required=False, default=False,
            description='Log packets matched by the internal block-rules',
        ),
        rules_tag=dict(
            type='str', required=False, aliases=['tag'],
            description='Firewall-tag to set on packets matched by the internal block-rules. '
                        'Numbers and letters only, at most 63 characters',
        ),
        enroll_key=dict(
            type='str', required=False, no_log=True, aliases=['enrollment_key'],
            description='Enrollment key of the CrowdSec console the instance should be '
                        'registered with. Numbers and letters only, at most 63 characters. '
                        "If omitted the existing key is kept; pass '' to clear it",
        ),
        crowdsec_firewall_verbose=dict(
            type='bool', required=False, default=False, aliases=['bouncer_verbose'],
            description='Run the firewall-bouncer in verbose mode',
        ),
        **RELOAD_MOD_ARG,
        **OPN_MOD_ARGS,
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

    module_wrapper(General(module=module, result=result))
    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
