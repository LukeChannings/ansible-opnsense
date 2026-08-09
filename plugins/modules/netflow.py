#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (C) 2026, Luke Channings <contact@lukechannings.com>
# GNU General Public License v3.0+ (see https://www.gnu.org/licenses/gpl-3.0.txt)

# see: https://docs.opnsense.org/manual/reporting.html

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.oxlorg.opnsense.plugins.module_utils.base.handler import \
    module_dependency_error, MODULE_EXCEPTIONS

try:
    from ansible_collections.oxlorg.opnsense.plugins.module_utils.base.wrapper import module_wrapper
    from ansible_collections.oxlorg.opnsense.plugins.module_utils.defaults.main import \
        OPN_MOD_ARGS, RELOAD_MOD_ARG
    from ansible_collections.oxlorg.opnsense.plugins.module_utils.main.netflow import General

except MODULE_EXCEPTIONS:
    module_dependency_error()

# DOCUMENTATION = 'https://ansible-opnsense.oxl.app/modules/netflow.html'
# EXAMPLES = 'https://ansible-opnsense.oxl.app/modules/netflow.html'


def run_module():
    module_args = dict(
        enabled=dict(
            type='bool', required=False, default=True, aliases=['en'],
            description='If the NetFlow capture should be running. Disabling it empties the '
                        'captured-interface list, which is how OPNsense stops the capture, '
                        'and leaves every other setting in place',
        ),
        interfaces=dict(
            type='list', elements='str', required=False, default=[], aliases=['ints', 'listen'],
            description='Interfaces to capture NetFlow data on, as interface-ids like '
                        "'lan' or 'opt2'. At least one is required while 'enabled'",
        ),
        egress_only=dict(
            type='list', elements='str', required=False, default=[],
            aliases=['wan_interfaces', 'egress'],
            description='Interfaces carrying WAN traffic, so NAT-ed traffic is not counted '
                        'twice. Must be a subset of the captured interfaces',
        ),
        version=dict(
            type='str', required=False, default='v9', choices=['v5', 'v9'],
            aliases=['netflow_version'],
            description='NetFlow protocol-version to send',
        ),
        targets=dict(
            type='list', elements='str', required=False, default=[],
            aliases=['destinations', 'collectors'],
            description="Collectors to send the NetFlow data to, as '<ipv4>:<port>' or "
                        "'[<ipv6>]:<port>'. At least one is required while 'enabled' - "
                        "'capture_local' counts",
        ),
        capture_local=dict(
            type='bool', required=False, default=False,
            aliases=['collect', 'local_collector'],
            description='Collect the NetFlow data on the firewall itself, for use with '
                        "Insight. This implicitly adds '127.0.0.1:2056' to the targets",
        ),
        active_timeout=dict(
            type='int', required=False, default=1800, aliases=['timeout_active'],
            description='Seconds after which a long-running flow is split into smaller parts',
        ),
        inactive_timeout=dict(
            type='int', required=False, default=15, aliases=['timeout_inactive'],
            description='Seconds after which an idle flow is expired',
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
