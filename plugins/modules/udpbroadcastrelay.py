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
        OPN_MOD_ARGS, STATE_MOD_ARG, RELOAD_MOD_ARG
    from ansible_collections.oxlorg.opnsense.plugins.module_utils.main.udpbroadcastrelay import Relay

except MODULE_EXCEPTIONS:
    module_dependency_error()


# DOCUMENTATION = 'https://ansible-opnsense.oxl.app/modules/udpbroadcastrelay.html'
# EXAMPLES = 'https://ansible-opnsense.oxl.app/modules/udpbroadcastrelay.html'


def run_module():
    module_args = dict(
        instance_id=dict(
            type='int', required=False, aliases=['instance', 'id'],
            description='Unique ID of the relay instance. Also used to tag the relayed packets '
                        'so they can be matched by firewall-rules'
        ),
        interfaces=dict(
            type='list', required=False, elements='str', default=[], aliases=['ints', 'i'],
            description='Interfaces to relay between. At least two are needed'
        ),
        listen_port=dict(
            type='int', required=False, aliases=['port', 'p'],
            description='UDP port to listen on and relay. For example 1900 for SSDP/DLNA '
                        'or 10001 for Unifi device-discovery'
        ),
        multicast_address=dict(
            type='list', required=False, elements='str', default=[], aliases=['multicast', 'mca'],
            description='Multicast IPv4-Addresses to relay in addition to broadcasts. '
                        'For example 239.255.255.250 for SSDP/DLNA'
        ),
        source_address=dict(
            type='str', required=False, default='', aliases=['source', 'src'],
            description='Spoof the source IPv4-Address of the relayed packets. '
                        "Use '1.1.1.1' to spoof the address of the outgoing interface"
        ),
        revert_ttl=dict(
            type='bool', required=False, default=False, aliases=['ttl'],
            description='Revert the TTL of the relayed packets to its original value. '
                        'Needed by clients that drop packets with a decremented TTL'
        ),
        description=dict(type='str', required=False, default='', aliases=['desc']),
        match_fields=dict(
            type='list', required=False, elements='str',
            description='Fields that are used to match configured relays with the running config - '
                        "if any of those fields are changed, the module will think it's a new relay",
            choices=['instance_id', 'listen_port', 'description'],
            default=['instance_id'],
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

    module_wrapper(Relay(module=module, result=result))
    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
