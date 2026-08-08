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
        OPN_MOD_ARGS, RELOAD_MOD_ARG
    from ansible_collections.oxlorg.opnsense.plugins.module_utils.main.tailscale_general import General

except MODULE_EXCEPTIONS:
    module_dependency_error()

# DOCUMENTATION = 'https://ansible-opnsense.oxl.app/modules/tailscale.html'
# EXAMPLES = 'https://ansible-opnsense.oxl.app/modules/tailscale.html'


def run_module():
    module_args = dict(
        enabled=dict(
            type='bool', required=False, default=False, aliases=['en'],
            description='If the tailscaled daemon should be run',
        ),
        login_timeout=dict(
            type='int', required=False, default=10, aliases=['timeout'],
            description='Seconds the node waits for the control-plane to authenticate it '
                        'before giving up',
        ),
        listen_port=dict(
            type='int', required=False, default=41641, aliases=['port'],
            description='UDP port tailscaled listens on for incoming WireGuard traffic',
        ),
        accept_dns=dict(
            type='bool', required=False, default=True, aliases=['dns'],
            description='Accept the DNS-configuration advertised by the tailnet (MagicDNS). '
                        'Disable this if the firewall runs its own resolver',
        ),
        advertise_exit_node=dict(
            type='bool', required=False, default=False, aliases=['exit_node'],
            description='Offer this node to the tailnet as an exit-node. Still has to be '
                        'approved in the tailnet admin-console',
        ),
        use_exit_node=dict(
            type='str', required=False, default='', aliases=['exit_node_peer'],
            description='Route all traffic through another nodes exit-node. Either its '
                        'Tailscale-IP or its hostname as the tailnet knows it. '
                        "Empty means 'None'",
        ),
        accept_subnet_routes=dict(
            type='bool', required=False, default=False, aliases=['accept_routes'],
            description='Accept the subnet-routes advertised by other nodes of the tailnet',
        ),
        enable_ssh=dict(
            type='bool', required=False, default=False, aliases=['ssh'],
            description='Serve SSH over the tailnet, authenticated and authorized by the '
                        "tailnets ACL instead of the firewalls own SSH-daemon",
        ),
        disable_snat=dict(
            type='bool', required=False, default=False, aliases=['no_snat'],
            description='Stop source-NATing the traffic that is routed into the advertised '
                        'subnets. The subnet-hosts then need a route back to the tailnet',
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
