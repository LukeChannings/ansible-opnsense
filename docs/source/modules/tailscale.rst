.. _modules_tailscale:

.. include:: ../_include/head.rst

==========
Tailscale
==========

**STATE**: unstable

**TESTS**: `Playbook tailscale_general <https://github.com/O-X-L/ansible-opnsense/blob/latest/tests/tailscale_general.yml>`_,
`Playbook tailscale_subnet <https://github.com/O-X-L/ansible-opnsense/blob/latest/tests/tailscale_subnet.yml>`_

**API Docs**: `Plugin - Tailscale <https://github.com/opnsense/plugins/tree/master/security/tailscale>`_

**Service Docs**: `Tailscale <https://tailscale.com/kb>`_

----

Requirements
************

The '`os-tailscale <https://github.com/opnsense/plugins/tree/master/security/tailscale>`_' plugin needs to be installed:

.. code-block:: yaml

    - name: Installing plugin
      oxlorg.opnsense.package:
        name: 'os-tailscale'
        action: 'install'

----

Info
****

Tailscale joins the firewall to a WireGuard-based mesh network (a *tailnet*).
The plugin drives the 'tailscaled' daemon and the 'tailscale up' flags it is
started with.

Two modules cover the plugins settings-object:

* **tailscale_general** - the daemon and its 'tailscale up' flags. A single
  settings-object, so the module can neither create nor delete anything - it
  always updates what is there
* **tailscale_subnet** - the subnet-routes this node advertises to the tailnet

Enrollment
==========

Joining the tailnet needs a pre-auth key ('tskey-auth-…'). That is a
join-once **secret** and enrolling a node is not an idempotent settings-write,
so it is deliberately **not** covered by these modules - keep it in the
web-UI under 'VPN - Tailscale - Authentication'.

Exit node
=========

'advertise_exit_node' offers *this* node as an exit-node - it still has to be
approved in the tailnet admin-console before other nodes may use it.

'use_exit_node' does the opposite and routes this nodes traffic through
*another* peer. The plugin builds its choices from the live tailnet, so the
module accepts either the peers Tailscale-IP or its hostname, and fails with
the list of available exit-nodes if neither matches. An empty value means
'None'.

Subnet routes
=============

'tailscale_subnet' entries become the '--advertise-routes' flag. They also have
to be approved in the tailnet admin-console. Routes are matched on their
'subnet', so re-running a play updates the description in place instead of
duplicating the route.

By default the traffic routed into those subnets is source-NATed to the
firewalls own address. 'disable_snat' turns that off - the hosts inside the
subnet then need a route back to the tailnet themselves.

Web-UI
======

Menu: 'VPN - Tailscale'

----

Definition
**********

oxlorg.opnsense.tailscale_general
=================================

..  csv-table:: Definition
    :header: "Parameter", "Type", "Required", "Default", "Aliases", "Comment"
    :widths: 15 10 10 10 10 45

    "enabled","boolean","false","false","en","If the tailscaled daemon should be run"
    "login_timeout","int","false","10","timeout","Seconds the node waits for the control-plane to authenticate it before giving up. Integer between 1 and 3600"
    "listen_port","int","false","41641","port","UDP port tailscaled listens on for incoming WireGuard traffic. Integer between 1 and 65535"
    "accept_dns","boolean","false","true","dns","Accept the DNS-configuration advertised by the tailnet (MagicDNS). Disable this if the firewall runs its own resolver"
    "advertise_exit_node","boolean","false","false","exit_node","Offer this node to the tailnet as an exit-node. Still has to be approved in the tailnet admin-console"
    "use_exit_node","string","false","''","exit_node_peer","Route all traffic through another nodes exit-node. Either its Tailscale-IP or its hostname as the tailnet knows it. Empty means 'None'"
    "accept_subnet_routes","boolean","false","false","accept_routes","Accept the subnet-routes advertised by other nodes of the tailnet"
    "enable_ssh","boolean","false","false","ssh","Serve SSH over the tailnet, authenticated and authorized by the tailnets ACL instead of the firewalls own SSH-daemon"
    "disable_snat","boolean","false","false","no_snat","Stop source-NATing the traffic that is routed into the advertised subnets. The subnet-hosts then need a route back to the tailnet"
    "reload","boolean","false","false","apply", .. include:: ../_include/param_reload.rst

.. include:: ../_include/param_basic.rst

----

oxlorg.opnsense.tailscale_subnet
================================

..  csv-table:: Definition
    :header: "Parameter", "Type", "Required", "Default", "Aliases", "Comment"
    :widths: 15 10 10 10 10 45

    "subnet","string","false for deletion, else true","\-","network, route, net","Network in CIDR-notation to advertise to the tailnet. The netmask is mandatory and the host-bits have to be unset"
    "description","string","false","''","desc","Description for the advertised route"
    "match_fields","list","false","['subnet']","\-","Fields that are used to match configured routes with the running config - if any of those fields are changed, the module will think it's a new route. At least one of: 'subnet', 'description'"
    "state","string","false","'present'","st","State of the route. One of: 'present', 'absent'"
    "reload","boolean","false","false","apply", .. include:: ../_include/param_reload.rst

.. include:: ../_include/param_basic.rst

----

Usage
*****

Neither module restarts the daemon on its own - the plugin only re-templates
'tailscaled's flags and restarts it when the settings are *applied*. So set
'reload' on the last task of a play that changes anything, or use the
:ref:`reload module <modules_reload>` with the 'tailscale' target.

Note that a reload **restarts tailscaled** and therefore drops the tunnel for a
moment.

----

Examples
********

oxlorg.opnsense.tailscale_general
=================================

.. code-block:: yaml

    - hosts: firewalls
      connection: local
      gather_facts: false
      module_defaults:
        group/oxlorg.opnsense.all:
          firewall: 'opnsense.template.opnsense.oxl.app'
          api_credential_file: '/home/guy/.secret/opn.key'

        oxlorg.opnsense.list:
          target: 'tailscale_general'

      tasks:
        - name: Example
          oxlorg.opnsense.tailscale_general:
            enabled: true
            # login_timeout: 10
            # listen_port: 41641
            # accept_dns: true
            # advertise_exit_node: false
            # use_exit_node: ''
            # accept_subnet_routes: false
            # enable_ssh: false
            # disable_snat: false
            # debug: false
            # reload: false

        - name: Running as an exit-node and subnet-router with a local resolver
          oxlorg.opnsense.tailscale_general:
            enabled: true
            accept_dns: false
            advertise_exit_node: true
            accept_subnet_routes: true

        - name: Routing all traffic through another peers exit-node
          oxlorg.opnsense.tailscale_general:
            enabled: true
            use_exit_node: 'exit-node-de'
            reload: true

        - name: Listing
          oxlorg.opnsense.list:
          #  target: 'tailscale_general'
          register: existing_entries

        - name: Printing
          ansible.builtin.debug:
            var: existing_entries.data

----

oxlorg.opnsense.tailscale_subnet
================================

.. code-block:: yaml

    - hosts: firewalls
      connection: local
      gather_facts: false
      module_defaults:
        group/oxlorg.opnsense.all:
          firewall: 'opnsense.template.opnsense.oxl.app'
          api_credential_file: '/home/guy/.secret/opn.key'

        oxlorg.opnsense.list:
          target: 'tailscale_subnet'

      tasks:
        - name: Example
          oxlorg.opnsense.tailscale_subnet:
            subnet: '192.168.0.0/24'
            # description: ''
            # match_fields: ['subnet']
            # debug: false
            # state: 'present'
            # reload: false

        - name: Advertising the local networks
          oxlorg.opnsense.tailscale_subnet:
            subnet: "{{ item.net }}"
            description: "{{ item.desc }}"
          loop:
            - {net: '192.168.10.0/24', desc: 'LAN'}
            - {net: '192.168.20.0/24', desc: 'IoT'}
            - {net: 'fd00:10::/64', desc: 'LAN IPv6'}

        - name: Applying the changes
          oxlorg.opnsense.reload:
            target: 'tailscale'

        - name: Listing
          oxlorg.opnsense.list:
          #  target: 'tailscale_subnet'
          register: existing_entries

        - name: Printing
          ansible.builtin.debug:
            var: existing_entries.data

        - name: Removing the IoT route
          oxlorg.opnsense.tailscale_subnet:
            subnet: '192.168.20.0/24'
            state: 'absent'
