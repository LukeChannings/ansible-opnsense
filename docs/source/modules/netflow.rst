.. _modules_netflow:

.. include:: ../_include/head.rst

========
NetFlow
========

**STATE**: unstable

**TESTS**: `Playbook <https://github.com/O-X-L/ansible-opnsense/blob/latest/tests/netflow.yml>`_

**API Docs**: `Core - Diagnostics/Netflow <https://docs.opnsense.org/development/api/core/diagnostics.html>`_

**Service Docs**: `NetFlow / Insight <https://docs.opnsense.org/manual/reporting.html>`_

----

Info
****

NetFlow is part of the OPNsense core, so there is no plugin to install.

The firewall exports flow-records from the selected interfaces to one or more
collectors. The local collector - the one feeding the 'Reporting - Insight'
graphs - is just another collector that happens to run on the firewall itself.

There is a **single settings-object**, so this module always updates the existing
configuration - it can neither create nor delete anything. Every parameter is
written on every run, so an omitted parameter is reset to its default rather than
left alone.

Enabling and disabling
======================

The data-model has **no enabled-flag**. OPNsense captures whenever both
'interfaces' and 'targets' are non-empty, and stops as soon as one of them is
cleared - that is all the web-UI offers, and all its own 'isEnabled' endpoint
reports.

This module gives you the flag anyway. 'enabled: false' empties the
captured-interface list - and with it 'egress_only', which the model requires to
be a subset of it - and writes every other setting untouched, so the
destinations, protocol-version and timeouts survive a temporary stop and
'enabled: true' brings the capture straight back:

.. code-block:: yaml

    - name: Pausing the capture
      oxlorg.opnsense.netflow:
        enabled: false
        reload: true

It is the interface-list rather than the target-list that gets cleared, because
'capture_local' makes OPNsense re-add '127.0.0.1:2056' server-side - clearing the
targets would therefore not reliably stop anything.

Since 'enabled: true' promises a running capture, the module rejects it without
at least one interface and one target instead of quietly writing a configuration
that captures nothing. 'capture_local' counts as a target.

Reading the settings back through :ref:`oxlorg.opnsense.list <modules_list>`
reports the same derived 'enabled' value, so a GUI-driven stop is visible too.

The local collector
===================

Setting 'capture_local' makes OPNsense append '127.0.0.1:2056' to the targets
server-side. This module mirrors that, so the target-list you get back matches the
one you asked for and a re-run stays idempotent.

Turning 'capture_local' off again therefore drops that implicit target - list
'127.0.0.1:2056' in 'targets' yourself if you want to keep feeding a local
collector without Insight.

Egress-only interfaces
======================

'egress_only' marks the interfaces carrying WAN traffic so NAT-ed flows are not
counted twice. It has to be a **subset of 'interfaces'** - the model enforces
that itself, and rejects the write with 'WAN interfaces missing in listening
interfaces'. This module checks it up-front so the failure names the offending
interface and the parameter it belongs to.

Not managed
===========

The controller also offers 'isEnabled', 'status' and 'cacheStats' - read-only
diagnostics with no configuration to converge on - and 'reset', which flushes the
collected flow-data and erases every Insight graph. None of them are part of this
module; 'reset' is a destructive one-shot action, not a desired state, so drive it
with the :ref:`oxlorg.opnsense.raw <modules_raw>` module if you need it.

Web-UI
======

Menu: 'Reporting - NetFlow'

Definition
**********

..  csv-table:: Definition
    :header: "Parameter", "Type", "Required", "Default", "Aliases", "Comment"
    :widths: 15 10 10 10 10 45

    "enabled","boolean","false","true","en","If the NetFlow capture should be running. Disabling it empties the captured-interface list, which is how OPNsense stops the capture, and leaves every other setting in place"
    "interfaces","list","false","\-","ints, listen","Interfaces to capture NetFlow data on, as interface-ids like 'lan' or 'opt2'. At least one is required while 'enabled'"
    "egress_only","list","false","\-","wan_interfaces, egress","Interfaces carrying WAN traffic, so NAT-ed traffic is not counted twice. Must be a subset of the captured interfaces"
    "version","string","false","'v9'","netflow_version","NetFlow protocol-version to send. One of: 'v5', 'v9'"
    "targets","list","false","\-","destinations, collectors","Collectors to send the NetFlow data to, as '<ipv4>:<port>' or '[<ipv6>]:<port>'. At least one is required while 'enabled' - 'capture_local' counts"
    "capture_local","boolean","false","false","collect, local_collector","Collect the NetFlow data on the firewall itself, for use with Insight. This implicitly adds '127.0.0.1:2056' to the targets"
    "active_timeout","int","false","1800","timeout_active","Seconds after which a long-running flow is split into smaller parts. Integer between 1 and 86400"
    "inactive_timeout","int","false","15","timeout_inactive","Seconds after which an idle flow is expired. Integer between 1 and 86400"
    "reload","boolean","false","false","apply", .. include:: ../_include/param_reload.rst

.. include:: ../_include/param_basic.rst

----

Usage
*****

Saving the settings does **not** re-template and restart the capture, so you need
to set 'reload' (or run the :ref:`oxlorg.opnsense.reload <modules_reload>` module
with 'target: netflow') for a change to reach the running service.

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
          target: 'netflow'

      tasks:
        - name: Example
          oxlorg.opnsense.netflow:
            interfaces: ['lan', 'wan']
            targets: ['192.168.1.50:2055']
            # enabled: true
            # egress_only: []
            # version: 'v9'
            # capture_local: false
            # active_timeout: 1800
            # inactive_timeout: 15
            # debug: false
            # reload: false

        - name: Feeding the local Insight graphs from the LAN and WAN interfaces
          oxlorg.opnsense.netflow:
            interfaces: ['lan', 'wan']
            egress_only: ['wan']
            capture_local: true
            reload: true

        - name: Exporting to an external collector as well
          oxlorg.opnsense.netflow:
            interfaces: ['lan', 'wan']
            egress_only: ['wan']
            targets: ['192.168.1.50:2055', '[fd00::50]:2055']
            capture_local: true
            reload: true

        - name: Splitting long-running flows more aggressively
          oxlorg.opnsense.netflow:
            interfaces: ['lan', 'wan']
            egress_only: ['wan']
            targets: ['192.168.1.50:2055']
            active_timeout: 60
            inactive_timeout: 5
            reload: true

        - name: Listing
          oxlorg.opnsense.list:
          #  target: 'netflow'
          register: existing_entries

        - name: Printing
          ansible.builtin.debug:
            var: existing_entries.data

        - name: Pausing the capture, keeping the rest of the configuration
          oxlorg.opnsense.netflow:
            enabled: false
            targets: ['192.168.1.50:2055']
            reload: true
