from ansible_collections.oxlorg.opnsense.plugins.module_utils.defaults.main import \
    STATE_MOD_ARG


TAILSCALE_SUBNET_MATCH_FIELDS = dict(
    match_fields=dict(
        type='list', required=False, elements='str',
        description='Fields that are used to match configured routes with the running config - '
                    "if any of those fields are changed, the module will think it's a new route",
        choices=['subnet', 'description'],
        default=['subnet'],
    )
)
TAILSCALE_SUBNET_MOD_ARGS = dict(
    subnet=dict(
        type='str', required=False, aliases=['network', 'route', 'net'],
        description='Network in CIDR-notation to advertise to the tailnet. '
                    'The netmask is mandatory and the host-bits have to be unset',
    ),
    description=dict(type='str', required=False, default='', aliases=['desc']),
    **TAILSCALE_SUBNET_MATCH_FIELDS,
    **STATE_MOD_ARG,
)
