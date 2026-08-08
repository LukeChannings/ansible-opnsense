.. _modules_crowdsec:

.. include:: ../_include/head.rst

=========
CrowdSec
=========

**STATE**: unstable

**TESTS**: `Playbook <https://github.com/O-X-L/ansible-opnsense/blob/latest/tests/crowdsec_general.yml>`_

**API Docs**: `Plugin - CrowdSec <https://github.com/opnsense/plugins/tree/master/security/crowdsec>`_

**Service Docs**: `CrowdSec <https://docs.crowdsec.net>`_

----

Requirements
************

The '`os-crowdsec <https://github.com/opnsense/plugins/tree/master/security/crowdsec>`_' plugin needs to be installed:

.. code-block:: yaml

    - name: Installing plugin
      oxlorg.opnsense.package:
        name: 'os-crowdsec'
        action: 'install'

----

Info
****

CrowdSec parses the firewalls logs, detects attacks and blocks the offending
sources. It is made up of three moving parts, each of which this module can
enable independently:

* the **agent** - the log-processor that reads the local logs and produces alerts
* the **local API** (LAPI) - stores the resulting decisions and serves them to bouncers
* the **firewall-bouncer** - pulls those decisions and maintains the
  'crowdsec_blocklists' (IPv4) and 'crowdsec6_blocklists' (IPv6) aliases

The plugin has a **single settings-object**, so this module always updates the
existing configuration - it can neither create nor delete anything.

Firewall rules
==============

While the firewall-bouncer is enabled the plugin registers four internal
block-rules - inbound and outbound, IPv4 and IPv6 - against its own blocklist
aliases. They are owned by the plugin and do not show up as
:ref:`oxlorg.opnsense.rule <modules_rule>` entries. 'rules_enabled' turns them
off if you would rather write your own rules against the aliases.

Enrollment key
==============

'enroll_key' registers the instance with the `CrowdSec console
<https://app.crowdsec.net>`_. It is a **secret**: pass it from a vault or lookup,
never in plaintext. The module marks it 'no_log' and replaces it in the diff-output,
so neither a normal nor a 'debug' run prints it.

Omitting it does **not** clear an existing key - the module keeps whatever is
configured. Set it to enrol or to rotate the key, or pass an empty string to
un-enrol. Note that every other optional field follows the usual behaviour and
*is* reset when omitted.

Local API
=========

'lapi_listen_address' and 'lapi_listen_port' configure a **locally running** local
API. By default the plugin also rewrites the agents and bouncers URLs and
credentials to match. Set 'lapi_manual_configuration' if you maintain those by
hand, for example to point them at a local API on another host.

Web-UI
======

Menu: 'Services - CrowdSec - Settings'

Definition
**********

..  csv-table:: Definition
    :header: "Parameter", "Type", "Required", "Default", "Aliases", "Comment"
    :widths: 15 10 10 10 10 45

    "agent_enabled","boolean","false","true","agent","Run the log-processor that parses local logs and detects attacks"
    "lapi_enabled","boolean","false","true","lapi","Run the local API that stores decisions and serves them to bouncers"
    "firewall_bouncer_enabled","boolean","false","true","bouncer, firewall_bouncer","Run the firewall-bouncer that feeds the decisions into the 'crowdsec_blocklists' and 'crowdsec6_blocklists' aliases"
    "lapi_manual_configuration","boolean","false","false","lapi_manual","Leave the agents and bouncers local-API URLs and credentials alone"
    "lapi_listen_address","string","false","'127.0.0.1'","lapi_address","IPv4- or IPv6-Address the local API should listen on"
    "lapi_listen_port","int","false","8080","lapi_port","TCP port the local API should listen on. Integer between 1 and 65535"
    "rules_enabled","boolean","false","true","rules","Register the internal block-rules that drop traffic from and to the CrowdSec blocklist-aliases"
    "rules_log","boolean","false","false","\-","Log packets matched by the internal block-rules"
    "rules_tag","string","false","\-","tag","Firewall-tag to set on packets matched by the internal block-rules. Numbers and letters only, at most 63 characters"
    "enroll_key","string","false","\-","enrollment_key","Enrollment key of the CrowdSec console the instance should be registered with. Numbers and letters only, at most 63 characters. If omitted the existing key is kept; pass '' to clear it"
    "crowdsec_firewall_verbose","boolean","false","false","bouncer_verbose","Run the firewall-bouncer in verbose mode"
    "reload","boolean","false","false","apply", .. include:: ../_include/param_reload.rst

.. include:: ../_include/param_basic.rst

----

Usage
*****

The plugin does **not** re-template and restart the services on its own, so you need
to set 'reload' (or run the :ref:`oxlorg.opnsense.reload <modules_reload>` module with
'target: crowdsec') for a change to reach the running daemons. The reconfigure also
regenerates 'config.yaml' and 'config-firewall-bouncer.yaml' and performs the console
enrollment.

----

Examples
********

.. code-block:: yaml

    - hosts: localhost
      gather_facts: no
      module_defaults:
        group/oxlorg.opnsense.all:
          firewall: 'opnsense.template.opnsense.oxl.app'
          api_credential_file: '/home/guy/.secret/opn.key'

        oxlorg.opnsense.list:
          target: 'crowdsec_general'

      tasks:
        - name: Example
          oxlorg.opnsense.crowdsec_general:
            # agent_enabled: true
            # lapi_enabled: true
            # firewall_bouncer_enabled: true
            # lapi_manual_configuration: false
            # lapi_listen_address: '127.0.0.1'
            # lapi_listen_port: 8080
            # rules_enabled: true
            # rules_log: false
            # rules_tag: ''
            # enroll_key: ''
            # crowdsec_firewall_verbose: false
            # debug: false
            # reload: false

        - name: Blocking and logging, tagged for later matching
          oxlorg.opnsense.crowdsec_general:
            rules_log: true
            rules_tag: 'crowdsec'
            reload: true

        - name: Enrolling with the console
          oxlorg.opnsense.crowdsec_general:
            enroll_key: "{{ lookup('ansible.builtin.env', 'CROWDSEC_ENROLL_KEY') }}"
            reload: true

        - name: Bouncing only - agent and local API run on another host
          oxlorg.opnsense.crowdsec_general:
            agent_enabled: false
            lapi_enabled: false
            lapi_manual_configuration: true
            reload: true

        - name: Listing
          oxlorg.opnsense.list:
          #  target: 'crowdsec_general'
          register: existing_entries

        - name: Printing
          ansible.builtin.debug:
            var: existing_entries.data

        - name: Disabling CrowdSec
          oxlorg.opnsense.crowdsec_general:
            agent_enabled: false
            lapi_enabled: false
            firewall_bouncer_enabled: false
            reload: true
