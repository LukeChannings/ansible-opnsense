from re import match as regex_match

NIC_TYPE_DEFAULT = 'virtio-net'
DISK_TYPE_DEFAULT = 'virtio-blk'
SIZE_UNITS = {'': 1, 'k': 1024, 'm': 1024 ** 2, 'g': 1024 ** 3, 't': 1024 ** 4}


class BhyveError(Exception):
    """Raised when the declared state cannot be reached. Reported as a failed task."""


def size_to_bytes(size: str) -> int:
    """Reads a disk size the way 'truncate' does, so sizes can be compared."""
    found = regex_match(r'^(\d+)([kmgtKMGT]?)$', str(size).strip())

    if found is None:
        raise BhyveError(
            f"'{size}' is not a valid size - expected a number of bytes, "
            "optionally followed by 'K', 'M', 'G' or 'T'"
        )

    return int(found.group(1)) * SIZE_UNITS[found.group(2).lower()]


def indexed_settings(conf: dict, prefix: str) -> dict:
    """Groups settings like 'network0_switch' by their index: {0: {'switch': ..}}."""
    grouped = {}

    for key, value in conf.items():
        found = regex_match(rf'^{prefix}(\d+)_(.+)$', key)
        if found is not None:
            grouped.setdefault(int(found.group(1)), {})[found.group(2)] = value

    return grouped


def _apply_indexed(conf: dict, prefix: str, entries: list) -> dict:
    """Replaces the indexed settings of one kind - nics or disks - with 'entries'.

    Settings of an index that is still declared keep their place in the file;
    those of an index that is gone are dropped with it.
    """
    desired = {}
    for index, entry in enumerate(entries):
        for suffix, value in entry.items():
            desired[f'{prefix}{index}_{suffix}'] = str(value)

    applied = {}
    for key, value in conf.items():
        if regex_match(rf'^{prefix}\d+_', key) is None:
            applied[key] = value

        elif key in desired:
            applied[key] = desired[key]

    for key, value in desired.items():
        if key not in applied:
            applied[key] = value

    return applied


def _nic_settings(nics: list, existing: dict) -> list:
    """Maps the declared nics onto the settings of 'networkN_*'.

    An undeclared mac-address is taken from the nic that currently sits at the
    same position, so the one vm-bhyve generated survives a reconfiguration.
    """
    current = indexed_settings(existing, 'network')
    settings = []

    for index, nic in enumerate(nics):
        kept = {
            suffix: value for suffix, value in current.get(index, {}).items()
            if suffix not in ['switch', 'type', 'mac']
        }
        mac = nic.get('mac') or current.get(index, {}).get('mac')

        settings.append({
            **kept,
            'type': nic.get('type') or NIC_TYPE_DEFAULT,
            'switch': nic['switch'],
            **({'mac': mac} if mac is not None else {}),
        })

    return settings


def _disk_settings(disks: list, existing: dict) -> list:
    """Maps the declared disks onto the settings of 'diskN_*'.

    The declared size is deliberately not written: vm-bhyve removes 'diskN_size'
    once the image exists, leaving the file on the host as the only truth.
    """
    current = indexed_settings(existing, 'disk')
    settings = []

    for index in current:
        if index >= len(disks):
            raise BhyveError(
                f'guest disk{index} is not declared - disks can only be added, never '
                'removed. Declare it again, or remove the whole guest to start over'
            )

    for index, disk in enumerate(disks):
        kept = {
            suffix: value for suffix, value in current.get(index, {}).items()
            if suffix not in ['type', 'name']
        }

        settings.append({
            **kept,
            'type': disk.get('type') or DISK_TYPE_DEFAULT,
            'name': current.get(index, {}).get('name') or f'disk{index}.img',
        })

    return settings


def parse_conf(raw: str) -> dict:
    """Parses a vm-bhyve configuration file the same way vm-bhyve itself does.

    See 'config::load' in /usr/local/lib/vm-bhyve/vm-config: only lines starting
    with a lowercase letter are settings, everything from the first '#' onwards is
    a comment, trailing spaces are dropped and every double-quote is removed.
    """
    settings = {}

    for line in raw.splitlines():
        if not line[:1].islower():
            continue

        line = line.split('#', 1)[0].rstrip(' ').replace('"', '')
        if '=' not in line:
            continue

        key, value = line.split('=', 1)
        settings[key] = value

    return settings


def render_conf(settings: dict) -> str:
    """Renders settings back into a vm-bhyve configuration file.

    Values are quoted as vm-bhyve does when writing them itself (it shells out to
    'sysrc'); the quotes are dropped again on read, so they carry no meaning.
    Existing settings keep their position in the file and new ones are appended.
    """
    return ''.join(f'{key}="{value}"\n' for key, value in settings.items())


def is_valid_name(name: str) -> bool:
    """Checks a guest- or switch-name the way vm-bhyve does. See 'util::check_name'."""
    return regex_match(r'^[a-zA-Z0-9][.a-zA-Z0-9_-]{0,229}[a-zA-Z0-9]$', str(name)) is not None


def parse_datastore(spec: str) -> tuple:
    """Splits a datastore specification into its scheme and location.

    'zfs:zroot/virtual-machines' is a dataset vm-bhyve expects to be mounted;
    anything else is simply a directory.
    """
    if spec.startswith('zfs:'):
        return 'zfs', spec[len('zfs:'):]

    return 'dir', spec


def apply_autostart(current: list, name: str, enabled: bool) -> list:
    """Adds or removes a guest from the list rc.conf starts at boot."""
    if not enabled:
        return [guest for guest in current if guest != name]

    if name in current:
        return list(current)

    return [*current, name]


def conf_diff(before: dict, after: dict) -> dict:
    """Reports the settings that differ between two configurations.

    Comparing settings rather than file contents means re-quoting or reordering a
    conf is not a change, and the guest is left alone.
    """
    changed = [
        key for key in {**before, **after}
        if before.get(key) != after.get(key)
    ]

    return {
        'before': {key: before[key] for key in changed if key in before},
        'after': {key: after[key] for key in changed if key in after},
    }


def switch_names(system_conf: dict) -> list:
    """Lists the switches of a host.

    Membership of 'switch_list' is what makes a switch exist - 'vm switch destroy'
    leaves the 'bridge_<name>' setting of a removed switch behind, so that setting
    says nothing about whether the switch is still there.
    """
    return system_conf.get('switch_list', '').split()


def switch_bridge(system_conf: dict, name: str) -> str:
    """Returns the bridge a switch attaches to, or None if it attaches to none."""
    return system_conf.get(f'bridge_{name}')


def plan_switch(system_conf: dict, name: str, bridge: str, state: str) -> str:
    """Decides what has to happen to a switch: create, recreate, destroy or keep.

    vm-bhyve offers no way to move a switch to another bridge, so a switch that
    points at the wrong one is destroyed and created again.
    """
    exists = name in switch_names(system_conf)

    if state == 'absent':
        return 'destroy' if exists else 'keep'

    if not exists:
        return 'create'

    if switch_bridge(system_conf, name) != bridge:
        return 'recreate'

    return 'keep'


def plan_disks(conf: dict, disks: list, sizes: dict) -> list:
    """Works out what has to happen to the image files of the declared disks.

    Takes the conf built by 'build_guest_conf', which has already refused to drop
    a disk. 'sizes' holds the current size of each disk's image file in bytes, or
    None where the file does not exist. Disks only ever grow: shrinking one would
    truncate a filesystem the guest is using, so that is refused as well.
    """
    planned = []
    for index, disk in enumerate(disks):
        size = size_to_bytes(disk['size'])
        current = sizes.get(index)

        if current is None:
            action = 'create'

        elif current < size:
            action = 'grow'

        elif current > size:
            raise BhyveError(
                f"guest disk{index} is {current} bytes and cannot be shrunk to {size} bytes"
            )

        else:
            action = 'keep'

        planned.append({
            'index': index,
            'name': conf[f'disk{index}_name'],
            'action': action,
            'size': size,
        })

    return planned


def build_guest_conf(existing: dict, params: dict) -> dict:
    """Builds the configuration a guest should have, from the one it has.

    A single rule throughout: a declared setting is written, an undeclared one is
    kept as-is. That keeps the settings this module has no parameters for - the
    loader-specific ones - as well as those vm-bhyve generates at runtime, like
    'uuid' and the per-nic mac-addresses.
    """
    conf = dict(existing)

    for key in ['loader', 'cpu', 'memory']:
        if params.get(key) is not None:
            conf[key] = str(params[key])

    if params.get('nics') is not None:
        conf = _apply_indexed(conf, 'network', _nic_settings(params['nics'], conf))

    if params.get('disks') is not None:
        conf = _apply_indexed(conf, 'disk', _disk_settings(params['disks'], conf))

    return conf
