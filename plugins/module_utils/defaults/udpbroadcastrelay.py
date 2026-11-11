from ansible_collections.oxlorg.opnsense.plugins.module_utils.defaults.main import \
    STATE_MOD_ARG


UBR_MATCH_FIELDS = dict(
    match_fields=dict(
        type='list', required=False, elements='str',
        description='Fields that are used to match configured relays with the running config - '
                    "if any of those fields are changed, the module will think it's a new relay",
        choices=['instance_id', 'listen_port', 'description'],
        default=['instance_id'],
    )
)
UBR_MOD_ARGS = dict(
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
    **UBR_MATCH_FIELDS,
    **STATE_MOD_ARG,
)
