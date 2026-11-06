.. _modules_udpbroadcastrelay:

.. include:: ../_include/head.rst

====================
UDP Broadcast Relay
====================

**STATE**: unstable

**TESTS**: `Playbook <https://github.com/O-X-L/ansible-opnsense/blob/latest/tests/udpbroadcastrelay.yml>`_

**API Docs**: `Plugin - UDPBroadcastRelay <https://github.com/opnsense/plugins/tree/master/net/udpbroadcastrelay>`_

**Service Docs**: `UDP Broadcast Relay <https://docs.opnsense.org/manual/how-tos/udpbroadcastrelay.html>`_

----

Requirements
************

The '`os-udpbroadcastrelay <https://github.com/opnsense/plugins/tree/master/net/udpbroadcastrelay>`_' plugin needs to be installed:

.. code-block:: yaml

    - name: Installing plugin
      oxlorg.opnsense.package:
        name: 'os-udpbroadcastrelay'
        action: 'install'

----

Info
****

The service relays broadcast and multicast traffic between the configured interfaces.
Typical use-cases are service-discovery protocols that do not cross layer-3 boundaries -
like SSDP/DLNA (*UDP 1900*), Unifi device-discovery (*UDP 10001*) or Sonos.

Each relay is a separate daemon-instance, identified by its 'instance_id'.

Both the 'instance_id' and the 'listen_port' have to be **unique** across all relays.
The service will refuse to save a relay that collides with an existing one.

The daemon is **IPv4-only** - it cannot join IPv6 multicast-groups.
Use `Avahi <https://docs.opnsense.org/manual/how-tos/avahi.html>`_ if you need to reflect mDNS over IPv6.

Web-UI
======

Menu: 'Services - UDP Broadcast Relay'

Definition
**********

..  csv-table:: Definition
    :header: "Parameter", "Type", "Required", "Default", "Aliases", "Comment"
    :widths: 15 10 10 10 10 45

    "instance_id","int","true","\-","instance, id","Unique ID of the relay instance. Integer between 1 and 63. Also used to tag the relayed packets so they can be matched by firewall-rules"
    "interfaces","list","false for deletion, else true","[]","ints, i","Interfaces to relay between. At least two are needed"
    "listen_port","int","false for deletion, else true","\-","port, p","UDP port to listen on and relay. Integer between 1 and 65535. For example 1900 for SSDP/DLNA or 10001 for Unifi device-discovery"
    "multicast_address","list","false","[]","multicast, mca","Multicast IPv4-Addresses to relay in addition to broadcasts. For example '239.255.255.250' for SSDP/DLNA"
    "source_address","string","false","''","source, src","Spoof the source IPv4-Address of the relayed packets. Use '1.1.1.1' to spoof the address of the outgoing interface"
    "revert_ttl","boolean","false","false","ttl","Revert the TTL of the relayed packets to its original value. Needed by clients that drop packets with a decremented TTL"
    "description","string","false","''","desc","Description for the relay"
    "match_fields","list","false","['instance_id']","\-","Fields that are used to match configured relays with the running config - if any of those fields are changed, the module will think it's a new relay. At least one of: 'instance_id', 'listen_port', 'description'"
    "state","string","false","'present'","st","State of the relay. One of: 'present', 'absent'"
    "enabled","boolean","false","true","en","If the relay should be en- or disabled"
    "reload","boolean","false","false","apply", .. include:: ../_include/param_reload.rst

.. include:: ../_include/param_basic.rst

----

Usage
*****

Adding, changing, removing or toggling a relay makes the service re-write its config
and reload on its own - so you do **not** need to set 'reload'.

All relay-attributes have to be supplied whenever the relay should be 'present' -
also when you only want to en- or disable it.

Note that the relayed traffic still has to be **allowed by firewall-rules** on the
target interfaces.

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
          target: 'udpbroadcastrelay'

      tasks:
        - name: Example
          oxlorg.opnsense.udpbroadcastrelay:
            instance_id: 1
            interfaces: ['lan', 'opt1']
            listen_port: 1900
            # multicast_address: []
            # source_address: ''
            # revert_ttl: false
            # description: ''
            # match_fields: ['instance_id']
            # enabled: true
            # debug: false
            # state: 'present'
            # reload: false

        - name: Relaying SSDP/DLNA between LAN and IoT
          oxlorg.opnsense.udpbroadcastrelay:
            instance_id: 2
            description: 'SSDP'
            interfaces: ['lan', 'opt1']
            listen_port: 1900
            multicast_address: ['239.255.255.250']

        - name: Relaying Unifi device-discovery
          oxlorg.opnsense.udpbroadcastrelay:
            instance_id: 3
            description: 'Unifi Discovery'
            interfaces: ['lan', 'opt1']
            listen_port: 10001
            multicast_address: ['239.255.255.250']

        - name: Disabling the SSDP relay
          oxlorg.opnsense.udpbroadcastrelay:
            instance_id: 2
            description: 'SSDP'
            interfaces: ['lan', 'opt1']
            listen_port: 1900
            multicast_address: ['239.255.255.250']
            enabled: false

        - name: Listing
          oxlorg.opnsense.list:
          #  target: 'udpbroadcastrelay'
          register: existing_entries

        - name: Printing
          ansible.builtin.debug:
            var: existing_entries.data

        - name: Removing the SSDP relay
          oxlorg.opnsense.udpbroadcastrelay:
            instance_id: 2
            state: 'absent'
