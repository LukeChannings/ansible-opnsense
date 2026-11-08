.. _modules_bhyve:

.. include:: ../_include/head.rst

=====
bhyve
=====

**STATE**: unstable

**TESTS**: `Playbook <https://github.com/O-X-L/ansible-opnsense/blob/latest/tests/bhyve.yml>`_

**Service Docs**: `vm-bhyve <https://github.com/churchers/vm-bhyve>`_ |
`bhyve <https://docs.freebsd.org/en/books/handbook/virtualization/#virtualization-host-bhyve>`_

----

Info
****

These modules run virtual machines on the firewall itself, using
`vm-bhyve <https://github.com/churchers/vm-bhyve>`_.

.. warning::

    **These modules do not use the OPNsense API.**

    vm-bhyve has no REST API - it is a shell tool and a set of plain-text
    configuration files - and OPNsense ships no plugin that exposes one. These
    modules therefore run **on the firewall over SSH**, like any ordinary Ansible
    module, rather than against the API from your control node.

    That means they take **none of the basic API parameters** (:code:`firewall`,
    :code:`api_credential_file`, :code:`ssl_verify`, ..), they need a working SSH
    connection with :code:`become: true`, and they are **not** part of the
    :code:`group/oxlorg.opnsense.all` module-defaults group. Use
    :code:`group/oxlorg.opnsense.bhyve` for them instead.

The three modules split along the lines the tool itself uses:

* :code:`bhyve_general` sets the host up - the packages, the service and the
  datastore guests are stored in
* :code:`bhyve_switch` connects guests to host networking
* :code:`bhyve_guest` declares the virtual machines

Packages
========

OPNsense's own package repository does not carry vm-bhyve. The upstream
FreeBSD-ports repository does, but OPNsense deliberately disables it - and
re-disables it on upgrades - because leaving it on lets :code:`pkg upgrade` pull
FreeBSD builds over OPNsense's own packages.

:code:`bhyve_general` therefore enables that repository **for a single pkg
transaction only**, through a temporary overlay, and leaves the system's
repository configuration untouched. OPNsense keeps its higher priority
throughout, so its own builds still win wherever both repositories carry a
package.

The packages are not :code:`pkg lock`\ ed. If an OPNsense upgrade strips them,
re-running :code:`bhyve_general` puts them back.

Bridges
=======

A switch is always of vm-bhyve's :code:`manual` type: it attaches to a bridge
that already exists and never creates host interfaces of its own.

Bridges belong to **OPNsense's own interface configuration** - create them with
:code:`oxlorg.opnsense.interface_bridge`, or in
*Interfaces - Devices - Bridge* - and give the switch the name of the resulting
device. :code:`bhyve_switch` fails if that bridge does not exist, rather than
leaving a switch no guest can start on.

----

Definition
**********

oxlorg.opnsense.bhyve_general
=============================

..  csv-table:: Definition
    :header: "Parameter", "Type", "Required", "Default", "Aliases", "Comment"
    :widths: 15 10 10 10 10 45

    "enabled","boolean","false","true","\-","Whether this host should run bhyve guests at all. Disabling only stops vm-bhyve from starting; it neither removes packages nor touches existing guests"
    "dir","string","false","\-","datastore, vm_dir","Where guests are stored, as a vm-bhyve datastore specification - either a path or 'zfs:<dataset>'. A missing dataset is created. If omitted, the configured datastore is left alone"

oxlorg.opnsense.bhyve_switch
============================

..  csv-table:: Definition
    :header: "Parameter", "Type", "Required", "Default", "Aliases", "Comment"
    :widths: 15 10 10 10 10 45

    "name","string","true","\-","switch","Name guests use to reference this switch"
    "bridge","string","true (if state=present)","\-","\-","Existing bridge interface the switch attaches to. The bridge itself belongs to OPNsense's interface configuration - see the 'interface_bridge' module - and is never created or changed here"
    "state","string","false","present","\-","One of: 'present', 'absent'"

oxlorg.opnsense.bhyve_guest
===========================

..  csv-table:: Definition
    :header: "Parameter", "Type", "Required", "Default", "Aliases", "Comment"
    :widths: 15 10 10 10 10 45

    "name","string","true","\-","guest","Name of the guest"
    "cpu","integer","false","\-","\-","Number of virtual cpus. Left as it is if omitted"
    "memory","string","false","\-","\-","Memory to give the guest, as a size like '2G'. Left as it is if omitted"
    "loader","string","false","\-","\-","How the guest is booted. 'uefi' is what a prebuilt raw image usually wants. Left as it is if omitted. One of: 'uefi', 'uefi-csm', 'bhyveload', 'grub'"
    "disks","list of dicts","false","\-","\-","Disks of the guest, in order. The first one is the boot disk. Sub-options: 'size' (required, like '20G') and 'type' (one of: 'virtio-blk' (default), 'ahci-hd', 'nvme'). Disks can be added and grown; removing one from this list fails rather than throwing its data away"
    "nics","list of dicts","false","\-","\-","Network interfaces of the guest, in order. Sub-options: 'switch' (required), 'mac' (optional - if omitted the one vm-bhyve generated is kept) and 'type' (one of: 'virtio-net' (default), 'e1000')"
    "image","path","false","\-","\-","Path on the host to a prebuilt raw disk image. It seeds the first disk whenever that disk has no image file yet, and is ignored while the disk exists - so deleting the disk is what asks for the guest to be installed again"
    "running","boolean","false","\-","\-","Whether the guest should be running. Left as it is if omitted"
    "autostart","boolean","false","\-","\-","Whether the guest starts with the host. Left as it is if omitted"
    "restart_on_change","boolean","false","false","\-","Restart a running guest so it picks up a changed configuration. Without this the new configuration is written and applies at the next start, so a routine run never interrupts a guest"
    "stop_timeout","integer","false","90","\-","Seconds a guest is given to shut down cleanly before it is powered off"
    "state","string","false","present","\-","One of: 'present', 'absent'"

----

Usage
*****

Declared wins, undeclared is kept
=================================

A guest's configuration file is the state these modules manage. They read it,
change what you declared, and write it back - so **a setting you do not declare
keeps the value it has**.

That one rule covers the settings these modules have no parameters for (the
loader-specific ones, for instance) as well as those vm-bhyve generates at
runtime, like :code:`uuid` and the per-nic mac addresses. A guest created by hand
can be adopted without losing anything.

Installing from an image
========================

:code:`image` points at a prebuilt **raw** disk image on the firewall. It seeds
the first disk **whenever that disk's image file does not exist**, and is inert
while the disk is there.

So the workflow is: build an image elsewhere (*with
nixos-generators, mkosi, packer, ..*), copy it to the firewall, and let the guest
boot it unattended. Re-running the module never overwrites a guest that has since
written to its disk - **deleting the disk file is the deliberate act** that asks
for the guest to be installed again. Any further disks always start empty.

The disk is grown to the declared size after seeding, so the image itself can
stay small.

Disks only grow
===============

Disks are matched **by their position** in the list, and that list is
append-and-grow-only:

* a bigger :code:`size` sparse-extends the image file
* a smaller :code:`size` **fails** - it would truncate a filesystem the guest is using
* dropping an entry **fails** - it would throw the data away

Remove the whole guest (:code:`state: absent`) if you want to start over.

Nics, on the other hand, are reconciled freely - add, remove and change them as
you like.

Restarts
========

Changing the configuration of a **running** guest writes the new configuration,
reports the task as changed and warns you that the guest still runs with the old
one. It is **not** restarted unless you ask for it with
:code:`restart_on_change: true`.

A bhyve guest is a machine - stopping one as a side effect of an unrelated
setting is rarely what anybody wants, so applying the change stays an explicit
choice.

Notes
=====

* :code:`bhyve_switch` and :code:`bhyve_guest` fail with a clear message when
  vm-bhyve has not been set up yet - run :code:`bhyve_general` against the host first.
* :code:`state: absent` on a guest shuts it down and removes **everything** -
  dataset, configuration and disks. There is no second guard.
* :code:`autostart` is membership of rc.conf's :code:`vm_list`, which is what
  starts guests at boot.
* Guests are reached over the bridge like any other host on it. The firewall's
  own rules apply to that traffic where :code:`net.link.bridge.pfil_member` is on.
* Both modules support :code:`--check` and :code:`--diff`.

----

Examples
********

.. code-block:: yaml

    - hosts: firewalls
      become: true
      gather_facts: false
      module_defaults:
        group/oxlorg.opnsense.bhyve:
          # these modules run on the firewall itself - no api-parameters

      tasks:
        - name: Setting the host up
          oxlorg.opnsense.bhyve_general:
            dir: 'zfs:zroot/virtual-machines'

        - name: Connecting guests to the LAN bridge
          oxlorg.opnsense.bhyve_switch:
            name: 'lan'
            bridge: 'bridge0'

        - name: Running a NixOS guest from a prebuilt image
          oxlorg.opnsense.bhyve_guest:
            name: 'dns'
            cpu: 2
            memory: '2G'
            loader: 'uefi'
            image: '/root/images/dns.raw'
            disks:
              - size: '20G'
            nics:
              - switch: 'lan'
                mac: '58:9c:fc:00:00:01'
            autostart: true
            running: true

        - name: Giving it more memory, to be applied at the next start
          oxlorg.opnsense.bhyve_guest:
            name: 'dns'
            memory: '4G'

        - name: Giving it more memory and restarting it now
          oxlorg.opnsense.bhyve_guest:
            name: 'dns'
            memory: '4G'
            restart_on_change: true

        - name: Stopping a guest without removing it
          oxlorg.opnsense.bhyve_guest:
            name: 'dns'
            running: false

        - name: Removing a guest, disks and all
          oxlorg.opnsense.bhyve_guest:
            name: 'dns'
            state: 'absent'

Pinning a guest's mac address makes it addressable by the firewall's own DHCP:

.. code-block:: yaml

    - name: Giving the guest a fixed lease
      oxlorg.opnsense.dhcp_reservation:
        ip: '192.168.1.10'
        mac: '58:9c:fc:00:00:01'
        subnet: '192.168.1.0/24'
        hostname: 'dns'
