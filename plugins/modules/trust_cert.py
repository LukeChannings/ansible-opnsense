#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (C) 2026, Luke Channings <contact@lukechannings.com>
# GNU General Public License v3.0+ (see https://www.gnu.org/licenses/gpl-3.0.txt)

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.oxlorg.opnsense.plugins.module_utils.base.handler import \
    module_dependency_error, MODULE_EXCEPTIONS

try:
    from ansible_collections.oxlorg.opnsense.plugins.module_utils.base.wrapper import module_wrapper
    from ansible_collections.oxlorg.opnsense.plugins.module_utils.defaults.main import \
        OPN_MOD_ARGS, STATE_ONLY_MOD_ARG, RELOAD_MOD_ARG
    from ansible_collections.oxlorg.opnsense.plugins.module_utils.main.trust_cert import Cert

except MODULE_EXCEPTIONS:
    module_dependency_error()

# DOCUMENTATION = 'https://ansible-opnsense.oxl.app/modules/trust.html'
# EXAMPLES = 'https://ansible-opnsense.oxl.app/modules/trust.html'


def run_module():
    module_args = dict(
        description=dict(
            type='str', required=True, aliases=['desc', 'name'],
            description='Name of the certificate as shown in the web-interface. '
                        'Used to match this config to existing entries',
        ),
        certificate=dict(
            type='str', required=False, aliases=['crt', 'cert', 'crt_payload'],
            description='The PEM-encoded X509 certificate',
        ),
        private_key=dict(
            type='str', required=False, no_log=True, aliases=['prv', 'key', 'prv_payload'],
            description='The PEM-encoded private key belonging to the certificate. Needed for any '
                        'certificate the firewall itself uses. If not provided, an already stored '
                        "private key is kept - pass '' to remove it",
        ),
        action=dict(
            type='str', required=False, default='import', choices=['import'],
            description='Only importing an existing certificate is supported. Creating an internal '
                        'certificate, a signing-request or re-issuing one is not implemented',
        ),
        force=dict(
            type='bool', required=False, default=False,
            description='Allow removing a certificate that is currently in use by a service',
        ),
        **RELOAD_MOD_ARG,
        **STATE_ONLY_MOD_ARG,
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

    module_wrapper(Cert(module=module, result=result))
    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
