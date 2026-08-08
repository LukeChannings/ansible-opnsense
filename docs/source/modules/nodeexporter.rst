.. _modules_nodeexporter:

.. include:: ../_include/head.rst

==============
Node Exporter
==============

**STATE**: unstable

**TESTS**: `Playbook <https://github.com/O-X-L/ansible-opnsense/blob/latest/tests/nodeexporter.yml>`_

**API Docs**: `Plugin - NodeExporter <https://github.com/opnsense/plugins/tree/master/sysutils/node_exporter>`_

**Service Docs**: `Prometheus node_exporter <https://github.com/prometheus/node_exporter>`_

----

Requirements
************

The '`os-node_exporter <https://github.com/opnsense/plugins/tree/master/sysutils/node_exporter>`_' plugin needs to be installed:

.. code-block:: yaml

    - name: Installing plugin
      oxlorg.opnsense.package:
        name: 'os-node_exporter'
        action: 'install'

----

Info
****

The service exposes host metrics - CPU, memory, filesystems, network-interfaces and
so on - over HTTP for `Prometheus <https://prometheus.io>`_ to scrape.

The plugin has a **single settings-object**, so this module always updates the
existing configuration - it can neither create nor delete anything.

Collectors
==========

A collector that is not enabled is passed to the daemon as '--no-collector.<name>',
so the settings-object has to spell out the full set on every write.

The defaults follow **node_exporter's own defaults**, not the OPNsense
model-defaults: 'cpu', 'exec', 'filesystem', 'loadavg', 'meminfo', 'netdev',
'time' and 'zfs' default to 'true', while the opt-in 'devstat' and 'ntp' default
to 'false'. Enabling the service without listing any collector therefore gives you
a useful exporter rather than a silent one.

Note that this differs from the web-UI, where a freshly installed plugin starts
with every collector unchecked.

The plugins data-model also carries an 'interrupts' toggle, but its config-template
never reads it - the value has no effect on the running service. This module does
**not** manage it, and because OPNsense only writes the keys it is given, an
'interrupts' value set through the web-UI is left untouched.

Web-UI
======

Menu: 'Services - Node Exporter'

Definition
**********

..  csv-table:: Definition
    :header: "Parameter", "Type", "Required", "Default", "Aliases", "Comment"
    :widths: 15 10 10 10 10 45

    "listen_address","string","false","'0.0.0.0'","address, listen","IPv4- or IPv6-Address the exporter should listen on. '0.0.0.0' listens on all interfaces"
    "listen_port","int","false","9100","port, p","TCP port the exporter should listen on. Integer between 1 and 65535"
    "cpu","boolean","false","true","\-","Enable the CPU-statistics collector"
    "exec","boolean","false","true","\-","Enable the execution-statistics collector"
    "filesystem","boolean","false","true","\-","Enable the filesystem-statistics collector"
    "loadavg","boolean","false","true","\-","Enable the load-average-statistics collector"
    "meminfo","boolean","false","true","\-","Enable the memory-statistics collector"
    "netdev","boolean","false","true","\-","Enable the network-interface-statistics collector"
    "time","boolean","false","true","\-","Enable the current-time-statistics collector"
    "devstat","boolean","false","false","\-","Enable the device-statistics collector"
    "ntp","boolean","false","false","\-","Enable the NTP-statistics collector"
    "zfs","boolean","false","true","\-","Enable the ZFS-statistics collector"
    "enabled","boolean","false","true","en","If the exporter should be en- or disabled"
    "reload","boolean","false","false","apply", .. include:: ../_include/param_reload.rst

.. include:: ../_include/param_basic.rst

----

Usage
*****

The plugin does **not** re-template and restart the service on its own, so you need
to set 'reload' (or run the :ref:`oxlorg.opnsense.reload <modules_reload>` module with
'target: nodeexporter') for a change to reach the running daemon.

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
          target: 'nodeexporter'

      tasks:
        - name: Example
          oxlorg.opnsense.nodeexporter:
            # listen_address: '0.0.0.0'
            # listen_port: 9100
            # cpu: true
            # exec: true
            # filesystem: true
            # loadavg: true
            # meminfo: true
            # netdev: true
            # time: true
            # zfs: true
            # devstat: false
            # ntp: false
            # enabled: true
            # debug: false
            # reload: false

        - name: Exporting the default collectors on the management-network only
          oxlorg.opnsense.nodeexporter:
            listen_address: '192.168.1.1'
            listen_port: 9100
            reload: true

        - name: Adding the opt-in collectors
          oxlorg.opnsense.nodeexporter:
            devstat: true
            ntp: true
            reload: true

        - name: Exporting nothing but memory- and filesystem-metrics
          oxlorg.opnsense.nodeexporter:
            cpu: false
            exec: false
            loadavg: false
            netdev: false
            time: false
            zfs: false
            reload: true

        - name: Listing
          oxlorg.opnsense.list:
          #  target: 'nodeexporter'
          register: existing_entries

        - name: Printing
          ansible.builtin.debug:
            var: existing_entries.data

        - name: Disabling the exporter
          oxlorg.opnsense.nodeexporter:
            enabled: false
            reload: true
