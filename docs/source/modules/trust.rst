.. _modules_trust:

.. include:: ../_include/head.rst

=====================
Trust (Certificates)
=====================

**STATE**: unstable

**TESTS**: `Playbook <https://github.com/O-X-L/ansible-opnsense/blob/latest/tests/trust.yml>`_

**API Docs**: `Core - Trust <https://docs.opnsense.org/development/api/core/trust.html>`_

**Service Docs**: `Certificate Management <https://docs.opnsense.org/manual/certificates.html>`_

----

Info
****

The trust-store is part of the OPNsense core, so there is no plugin to install.

Two modules cover it:

* **trust_ca** - the certificate authorities under 'System - Trust - Authorities'
* **trust_cert** - the certificates under 'System - Trust - Certificates'

Both import existing key-material - typically an internal CA and the leaf
certificates issued by it - so services like HAProxy, OpenVPN, IPsec and the
web-interface itself can reference them.

Scope
=====

The OPNsense model behind both endpoints is mode-switched by an 'action' field.
Besides importing, it can also *generate* key-material: an internal CA, an OCSP
signing certificate, an internal certificate, a signing-request, or a re-issue
of an existing certificate.

**Only the import is implemented.** The generating modes have no desired state
to converge on - re-running them would mint a new key every time - and each
mode makes a different subset of fields required. 'action' is therefore
accepted with a single valid value ('existing' for authorities, 'import' for
certificates) so that the unsupported modes fail fast and can be added later
without breaking the interface.

Note that 'action' is *always* sent. The models own default is 'internal', so
an update that left it out could make OPNsense **replace the certificate and
its key** with a freshly generated pair.

Certificates are the desired state
==================================

Everything the trust-store keeps besides the description and the key-material
is **derived from the certificate itself** whenever it is read back: the
common-name and the rest of the distinguished name, the subject-alternative
names, the key-type, the digest, the OCSP-URI, the validity dates and the
purpose. They are outputs, not inputs - so these modules do not offer them as
parameters. Change the certificate and they follow.

The link between a certificate and its authority works the same way: OPNsense
matches the issuer against every CA in the store on each write and sets
'caref' itself. Import the CA first and the certificates attach to it
automatically - importing them the other way around works too, as the CA import
re-links the existing certificates.

Private keys
============

'private_key' is marked 'no_log' and is redacted from the diff-output and from
everything the 'debug' mode prints - the request-payload and the API-response
included. A rotated key is still reported as a change; with 'debug' enabled the
module names the changed field without printing either value.

A key that is **not** provided is left alone rather than removed, so a play that
only renews the certificate cannot silently drop the key that belongs to it.
Passing an empty string removes a stored key explicitly.

OPNsense refuses a certificate whose private key does not belong to it, so
replacing a certificate that has a key stored means providing the matching key
in the same task.

Deletion
========

Deleting an authority that still has certificates hanging off it - or a
certificate that a service is currently using - orphans those references.
Both modules refuse to do it and name what is in the way. Set 'force' to
delete anyway.

Web-UI
======

Menu: 'System - Trust'

----

Definition
**********

oxlorg.opnsense.trust_ca
========================

..  csv-table:: Definition
    :header: "Parameter", "Type", "Required", "Default", "Aliases", "Comment"
    :widths: 15 10 10 10 10 45

    "description","string","true","\-","desc, name","Name of the certificate authority as shown in the web-interface. Used to match this config to existing entries"
    "certificate","string","false for deletion, else true","\-","crt, cert, crt_payload","The PEM-encoded X509 certificate of the certificate authority"
    "private_key","string","false","\-","prv, key, prv_payload","The PEM-encoded private key of the certificate authority. Only needed if the firewall should be able to issue certificates from it. If not provided, an already stored private key is kept - pass '' to remove it"
    "action","string","false","'existing'","\-","Only importing an existing certificate authority is supported. One of: 'existing'"
    "force","boolean","false","false","\-","Allow removing a certificate authority that is still referenced by certificates or services. Those references will be orphaned"
    "state","string","false","'present'","st","State of the certificate authority. One of: 'present', 'absent'"
    "reload","boolean","false","false","apply", .. include:: ../_include/param_reload.rst

.. include:: ../_include/param_basic.rst

----

oxlorg.opnsense.trust_cert
==========================

..  csv-table:: Definition
    :header: "Parameter", "Type", "Required", "Default", "Aliases", "Comment"
    :widths: 15 10 10 10 10 45

    "description","string","true","\-","desc, name","Name of the certificate as shown in the web-interface. Used to match this config to existing entries"
    "certificate","string","false for deletion, else true","\-","crt, cert, crt_payload","The PEM-encoded X509 certificate"
    "private_key","string","false","\-","prv, key, prv_payload","The PEM-encoded private key belonging to the certificate. Needed for any certificate the firewall itself uses. If not provided, an already stored private key is kept - pass '' to remove it"
    "action","string","false","'import'","\-","Only importing an existing certificate is supported. One of: 'import'"
    "force","boolean","false","false","\-","Allow removing a certificate that is currently in use by a service"
    "state","string","false","'present'","st","State of the certificate. One of: 'present', 'absent'"
    "reload","boolean","false","false","apply", .. include:: ../_include/param_reload.rst

.. include:: ../_include/param_basic.rst

----

Usage
*****

Both endpoints re-write the systems trust-store as part of every change, so
'reload' is only needed to re-apply it by hand. The *services* that use a
certificate do not pick a replaced one up on their own - restart or reload
those separately.

Entries are matched on their description, so it has to be unique within the
authorities respectively the certificates. Changing it creates a second entry
rather than renaming the first.

----

Examples
********

.. code-block:: yaml

    - hosts: firewalls
      connection: local
      gather_facts: false
      module_defaults:
        group/oxlorg.opnsense.all:
          firewall: 'opnsense.template.opnsense.oxl.app'
          api_credential_file: '/home/guy/.secret/opn.key'

        oxlorg.opnsense.list:
          target: 'trust_cert'

      tasks:
        - name: Example
          oxlorg.opnsense.trust_ca:
            description: 'Example Root CA'
            certificate: "{{ lookup('ansible.builtin.file', 'pki/ca.crt') }}"
            # private_key: ''
            # action: 'existing'
            # force: false
            # debug: false
            # state: 'present'
            # reload: false

        - name: Importing an internal certificate authority - public part only
          oxlorg.opnsense.trust_ca:
            description: 'Example Root CA'
            certificate: "{{ lookup('ansible.builtin.file', 'pki/ca.crt') }}"

        - name: Importing a server certificate issued by it
          oxlorg.opnsense.trust_cert:
            description: 'web.example.com'
            certificate: "{{ lookup('ansible.builtin.file', 'pki/web.crt') }}"
            private_key: "{{ lookup('ansible.builtin.file', 'pki/web.key') }}"
          no_log: true

        - name: Renewing it - the stored private key is kept
          oxlorg.opnsense.trust_cert:
            description: 'web.example.com'
            certificate: "{{ lookup('ansible.builtin.file', 'pki/web.crt') }}"

        - name: Listing
          oxlorg.opnsense.list:
          #  target: 'trust_cert'
          register: existing_entries

        - name: Printing
          ansible.builtin.debug:
            var: existing_entries.data

        - name: Removing the certificate
          oxlorg.opnsense.trust_cert:
            description: 'web.example.com'
            state: 'absent'

        - name: Removing the authority - fails while certificates still reference it
          oxlorg.opnsense.trust_ca:
            description: 'Example Root CA'
            state: 'absent'
