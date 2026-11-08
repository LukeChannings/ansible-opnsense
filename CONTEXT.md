# OPNsense Ansible Collection

Ansible modules for declaratively managing an OPNsense firewall. Almost all modules speak to the OPNsense REST API; the `bhyve_*` family runs on the host itself (see ADR-0001).

## Language

### bhyve virtual machines

**Guest**:
A bhyve virtual machine managed by vm-bhyve: its resources (cpu, memory, disks, nics), loader, autostart, and running state.
_Avoid_: VM, instance, machine

**Switch**:
A vm-bhyve virtual switch that connects guest nics to host networking. Always `manual` type: it attaches to an existing OPNsense-managed bridge and never creates host interfaces itself.
_Avoid_: bridge (a bridge is the OPNsense-managed interface a switch attaches to, not the switch itself)

**Host setup**:
The one-per-host vm-bhyve foundation: the package set, `vm_enable`, and the datastore directory (`vm_dir`). Managed by `bhyve_general`.

**Image**:
A prebuilt raw disk image that seeds a guest's boot disk whenever that disk does not exist. While the disk exists the image is inert; deleting the disk forces re-installation on the next run.
_Avoid_: ISO, installer, template

**Datastore**:
A vm-bhyve storage location for guests (e.g. `zfs:zroot/virtual-machines`). The default datastore is defined by `vm_dir`.
