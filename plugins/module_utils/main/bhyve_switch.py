from ansible.module_utils.basic import AnsibleModule

from ansible_collections.oxlorg.opnsense.plugins.module_utils.base.bhyve import \
    BhyveModule
from ansible_collections.oxlorg.opnsense.plugins.module_utils.helper.bhyve import \
    BhyveError, clear_switch_bridge, is_valid_name, plan_switch, render_conf, \
    switch_bridge, switch_names


class Switch(BhyveModule):
    def __init__(self, module: AnsibleModule, result: dict):
        BhyveModule.__init__(self=self, module=module, result=result)
        self.action = 'keep'

    def check(self) -> None:
        if not is_valid_name(self.p['name']):
            raise BhyveError(f"'{self.p['name']}' is not a valid switch name")

        system_conf = self.h.system_conf()
        self.action = plan_switch(
            system_conf,
            name=self.p['name'],
            bridge=self.p['bridge'],
            state=self.p['state'],
        )

        if self.p['state'] == 'present':
            self._check_bridge()

        exists = self.p['name'] in switch_names(system_conf)
        self.r['diff']['before'] = {
            'state': 'present' if exists else 'absent',
            'bridge': switch_bridge(system_conf, self.p['name']) if exists else None,
        }
        self.r['diff']['after'] = {
            'state': self.p['state'],
            'bridge': self.p['bridge'] if self.p['state'] == 'present' else None,
        }
        self.r['changed'] = self.action != 'keep'

    def _check_bridge(self) -> None:
        """A switch may only attach to a bridge that already exists.

        Checked even when the switch needs no change, so a switch left pointing at
        a bridge that has gone is reported rather than silently kept.
        """
        bridges = self.h.bridges()

        if self.p['bridge'] not in bridges:
            raise BhyveError(
                f"'{self.p['bridge']}' is not a bridge on this host - bridges are "
                "part of OPNsense's interface configuration, create it there (see "
                f"the 'interface_bridge' module) first. "
                f"Available: {', '.join(bridges) if bridges else 'none'}"
            )

    def process(self) -> None:
        if self.action == 'keep' or self.m.check_mode:
            return

        if self.action in ['destroy', 'recreate']:
            self.h.vm(['switch', 'destroy', self.p['name']])
            self._clear_leftovers()

        if self.action in ['create', 'recreate']:
            self.h.vm([
                'switch', 'create',
                '-t', 'manual',
                '-b', self.p['bridge'],
                self.p['name'],
            ])

        if self.action == 'recreate':
            self.m.warn(
                f"switch '{self.p['name']}' now attaches to a different bridge - "
                'running guests keep using the old one until they are restarted'
            )

    def _clear_leftovers(self) -> None:
        """Removes what 'vm switch destroy' forgets, so removal really removes."""
        conf_path = f'{self.h.vm_dir()}/.config/system.conf'
        cleared = clear_switch_bridge(self.h.read_conf(conf_path), self.p['name'])

        self.h.write(conf_path, render_conf(cleared))
