#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (C) 2026, Luke Channings <contact@lukechannings.com>
# GNU General Public License v3.0+ (see https://www.gnu.org/licenses/gpl-3.0.txt)

# see: https://github.com/opnsense/plugins/tree/master/sysutils/node_exporter

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.oxlorg.opnsense.plugins.module_utils.base.handler import \
    module_dependency_error, MODULE_EXCEPTIONS

try:
    from ansible_collections.oxlorg.opnsense.plugins.module_utils.base.wrapper import module_wrapper
    from ansible_collections.oxlorg.opnsense.plugins.module_utils.defaults.main import \
        EN_ONLY_MOD_ARG, OPN_MOD_ARGS, RELOAD_MOD_ARG
    from ansible_collections.oxlorg.opnsense.plugins.module_utils.main.nodeexporter import General

except MODULE_EXCEPTIONS:
    module_dependency_error()

# DOCUMENTATION = 'https://ansible-opnsense.oxl.app/modules/nodeexporter.html'
# EXAMPLES = 'https://ansible-opnsense.oxl.app/modules/nodeexporter.html'


def _collector_arg(name: str, description: str, default: bool = True) -> dict:
    return {name: dict(
        type='bool', required=False, default=default,
        description=f'Enable the {description} collector',
    )}


def run_module():
    module_args = dict(
        listen_address=dict(
            type='str', required=False, default='0.0.0.0', aliases=['address', 'listen'],
            description='IPv4- or IPv6-Address the exporter should listen on. '
                        "'0.0.0.0' listens on all interfaces",
        ),
        listen_port=dict(
            type='int', required=False, default=9100, aliases=['port', 'p'],
            description='TCP port the exporter should listen on',
        ),
        **_collector_arg('cpu', 'CPU-statistics'),
        **_collector_arg('exec', 'execution-statistics'),
        **_collector_arg('filesystem', 'filesystem-statistics'),
        **_collector_arg('loadavg', 'load-average-statistics'),
        **_collector_arg('meminfo', 'memory-statistics'),
        **_collector_arg('netdev', 'network-interface-statistics'),
        **_collector_arg('time', 'current-time-statistics'),
        **_collector_arg('devstat', 'device-statistics', default=False),
        **_collector_arg('ntp', 'NTP-statistics', default=False),
        **_collector_arg('zfs', 'ZFS-statistics'),
        **EN_ONLY_MOD_ARG,
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
