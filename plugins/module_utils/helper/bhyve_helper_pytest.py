from pytest import raises

from ansible_collections.oxlorg.opnsense.plugins.module_utils.helper.bhyve import \
    parse_conf, render_conf, build_guest_conf, size_to_bytes, plan_disks, \
    switch_names, switch_bridge, conf_diff, apply_autostart, parse_datastore, \
    is_valid_name, plan_switch, plan_running, clear_switch_bridge, is_zvol, \
    BhyveError

# the conf of the guest that exists on the development router
GUEST_CONF_NIXOS = '''loader="grub"
cpu=1
memory=512M
network0_type="virtio-net"
network0_switch="public"
disk0_type="ahci-hd"
disk0_name="disk0.img"
grub_run_partition="1"
grub_run_dir="/boot/grub"
uuid="f13b5b28-4a29-11f0-a8c4-b496913b9060"
network0_mac="58:9c:fc:0e:92:b2"
'''


def test_parse_conf_reads_every_setting_of_a_real_guest():
    assert parse_conf(GUEST_CONF_NIXOS) == {
        'loader': 'grub',
        'cpu': '1',
        'memory': '512M',
        'network0_type': 'virtio-net',
        'network0_switch': 'public',
        'disk0_type': 'ahci-hd',
        'disk0_name': 'disk0.img',
        'grub_run_partition': '1',
        'grub_run_dir': '/boot/grub',
        'uuid': 'f13b5b28-4a29-11f0-a8c4-b496913b9060',
        'network0_mac': '58:9c:fc:0e:92:b2',
    }


def test_parse_conf_sees_only_what_vm_bhyve_sees():
    # mirrors 'config::load' - a line is only a setting if it starts with a
    # lowercase letter, so comments and indented lines are not settings
    assert parse_conf(
        '# a comment\n'
        '  cpu=4\n'
        'Memory=1G\n'
        'loader=uefi\n'
    ) == {'loader': 'uefi'}


def test_parse_conf_strips_trailing_comments_and_spaces():
    assert parse_conf('cpu=4   # four cores   \n') == {'cpu': '4'}


def test_parse_conf_treats_a_hash_inside_quotes_as_a_comment_too():
    # a vm-bhyve quirk we have to reproduce, else our idea of the
    # configured value differs from the one the guest actually boots with
    assert parse_conf('password="se#cret"\n') == {'password': 'se'}


def test_render_conf_quotes_every_value():
    assert render_conf({'loader': 'uefi', 'cpu': '4'}) == 'loader="uefi"\ncpu="4"\n'


def test_render_conf_keeps_existing_settings_in_place():
    # rewriting a conf should not reshuffle it - the file stays readable for
    # whoever looks at it on the host
    conf = parse_conf(GUEST_CONF_NIXOS)
    conf['cpu'] = '2'
    conf['autostart'] = 'yes'

    assert render_conf(conf).splitlines()[:3] == ['loader="grub"', 'cpu="2"', 'memory="512M"']
    assert render_conf(conf).splitlines()[-1] == 'autostart="yes"'


def test_a_guest_conf_survives_a_round_trip():
    assert parse_conf(render_conf(parse_conf(GUEST_CONF_NIXOS))) == parse_conf(GUEST_CONF_NIXOS)


def test_building_a_guest_conf_writes_the_declared_settings():
    conf = build_guest_conf(
        existing=parse_conf(GUEST_CONF_NIXOS),
        params={'cpu': 2, 'memory': '2G', 'loader': 'uefi'},
    )

    assert conf['cpu'] == '2'
    assert conf['memory'] == '2G'
    assert conf['loader'] == 'uefi'


def test_building_a_guest_conf_keeps_settings_the_module_does_not_manage():
    # the loader-specific settings of the existing guest are nothing this module
    # knows about - dropping them on a rewrite would stop the guest booting
    conf = build_guest_conf(existing=parse_conf(GUEST_CONF_NIXOS), params={'cpu': 2})

    assert conf['grub_run_partition'] == '1'
    assert conf['grub_run_dir'] == '/boot/grub'


def test_building_a_guest_conf_keeps_what_vm_bhyve_generated_at_runtime():
    conf = build_guest_conf(existing=parse_conf(GUEST_CONF_NIXOS), params={'cpu': 2})

    assert conf['uuid'] == 'f13b5b28-4a29-11f0-a8c4-b496913b9060'
    assert conf['network0_mac'] == '58:9c:fc:0e:92:b2'


def test_building_a_guest_conf_leaves_undeclared_settings_alone():
    conf = build_guest_conf(existing=parse_conf(GUEST_CONF_NIXOS), params={'cpu': 2})

    assert conf['memory'] == '512M'
    assert conf['loader'] == 'grub'


def test_nics_are_numbered_by_their_position_in_the_list():
    conf = build_guest_conf(
        existing={},
        params={'nics': [{'switch': 'lan'}, {'switch': 'dmz', 'type': 'e1000'}]},
    )

    assert conf['network0_switch'] == 'lan'
    assert conf['network0_type'] == 'virtio-net'
    assert conf['network1_switch'] == 'dmz'
    assert conf['network1_type'] == 'e1000'


def test_a_nic_keeps_the_mac_vm_bhyve_gave_it():
    conf = build_guest_conf(
        existing=parse_conf(GUEST_CONF_NIXOS),
        params={'nics': [{'switch': 'public'}]},
    )

    assert conf['network0_mac'] == '58:9c:fc:0e:92:b2'


def test_a_declared_mac_pins_the_nic():
    conf = build_guest_conf(
        existing=parse_conf(GUEST_CONF_NIXOS),
        params={'nics': [{'switch': 'public', 'mac': '58:9c:fc:00:00:01'}]},
    )

    assert conf['network0_mac'] == '58:9c:fc:00:00:01'


def test_dropping_a_nic_removes_it_from_the_conf():
    conf = build_guest_conf(
        existing=parse_conf(GUEST_CONF_NIXOS),
        params={'nics': []},
    )

    assert 'network0_switch' not in conf
    assert 'network0_type' not in conf
    assert 'network0_mac' not in conf


def test_leaving_the_nics_undeclared_keeps_them():
    conf = build_guest_conf(existing=parse_conf(GUEST_CONF_NIXOS), params={'cpu': 2})

    assert conf['network0_switch'] == 'public'


def test_disks_are_numbered_by_their_position_in_the_list():
    conf = build_guest_conf(
        existing={},
        params={'disks': [{'size': '20G'}, {'size': '5G', 'type': 'nvme'}]},
    )

    assert conf['disk0_name'] == 'disk0.img'
    assert conf['disk0_type'] == 'virtio-blk'
    assert conf['disk1_name'] == 'disk1.img'
    assert conf['disk1_type'] == 'nvme'


def test_a_disk_keeps_the_image_file_it_already_uses():
    # the existing guest boots 'disk0.img' - a rewrite must not point it elsewhere
    conf = build_guest_conf(
        existing=parse_conf(GUEST_CONF_NIXOS),
        params={'disks': [{'size': '20G', 'type': 'ahci-hd'}]},
    )

    assert conf['disk0_name'] == 'disk0.img'
    assert conf['disk0_type'] == 'ahci-hd'


def test_sizes_are_read_the_way_truncate_writes_them():
    assert size_to_bytes('512M') == 512 * 1024 ** 2
    assert size_to_bytes('20G') == 20 * 1024 ** 3
    assert size_to_bytes('1T') == 1024 ** 4
    assert size_to_bytes('4k') == 4096
    assert size_to_bytes('1024') == 1024


def test_an_unreadable_size_is_rejected():
    with raises(BhyveError, match='not a valid size'):
        size_to_bytes('20GB')


def test_the_declared_size_stays_out_of_the_conf():
    # vm-bhyve drops 'diskN_size' after creating the image; the size of the file
    # on the host is the truth, so storing it again would only let the two drift
    conf = build_guest_conf(existing={}, params={'disks': [{'size': '20G'}]})

    assert 'disk0_size' not in conf


# the system-conf of the development router
SYSTEM_CONF = '''switch_list="public"
type_public="manual"
bridge_public="bridge0"
'''


def test_the_switches_of_a_host_are_read_from_its_system_conf():
    assert switch_names(parse_conf(SYSTEM_CONF)) == ['public']


def test_a_switch_knows_the_bridge_it_attaches_to():
    assert switch_bridge(parse_conf(SYSTEM_CONF), 'public') == 'bridge0'


def test_a_host_without_any_switch_has_an_empty_list():
    assert switch_names({}) == []


def test_a_removed_switch_is_gone_even_though_its_bridge_setting_remains():
    # 'vm switch destroy' forgets to remove 'bridge_<name>', so only membership
    # of 'switch_list' tells us whether a switch exists
    left_behind = parse_conf('switch_list=""\nbridge_public="bridge0"\n')

    assert switch_names(left_behind) == []


def test_a_stopped_guest_that_should_run_is_started():
    assert plan_running(
        running_now=False, running_wanted=True, conf_changed=False, restart_on_change=False,
    ) == ['start']


def test_a_running_guest_that_should_stop_is_stopped():
    assert plan_running(
        running_now=True, running_wanted=False, conf_changed=False, restart_on_change=False,
    ) == ['stop']


def test_a_guest_already_in_the_wanted_state_is_left_alone():
    assert plan_running(
        running_now=True, running_wanted=True, conf_changed=False, restart_on_change=False,
    ) == []


def test_an_undeclared_running_state_is_not_touched():
    assert plan_running(
        running_now=False, running_wanted=None, conf_changed=False, restart_on_change=False,
    ) == []


def test_reconfiguring_a_running_guest_does_not_restart_it_by_default():
    # the conf is written either way; applying it must stay an explicit choice,
    # so a routine run never interrupts a guest
    assert plan_running(
        running_now=True, running_wanted=None, conf_changed=True, restart_on_change=False,
    ) == []


def test_reconfiguring_a_running_guest_restarts_it_when_asked():
    assert plan_running(
        running_now=True, running_wanted=True, conf_changed=True, restart_on_change=True,
    ) == ['stop', 'start']


def test_a_guest_that_should_stop_is_not_restarted_for_a_conf_change():
    assert plan_running(
        running_now=True, running_wanted=False, conf_changed=True, restart_on_change=True,
    ) == ['stop']


def test_a_stopped_guest_needs_no_restart_to_pick_up_a_new_conf():
    assert plan_running(
        running_now=False, running_wanted=None, conf_changed=True, restart_on_change=True,
    ) == []


def test_removing_a_switch_takes_its_bridge_setting_with_it():
    # 'vm switch destroy' leaves 'bridge_<name>' behind; we clear it so repeated
    # runs do not pile up settings for switches that no longer exist
    left_behind = parse_conf(
        'switch_list=""\n'
        'bridge_public="bridge0"\n'
        'bridge_other="bridge1"\n'
    )

    assert clear_switch_bridge(left_behind, 'public') == {
        'switch_list': '',
        'bridge_other': 'bridge1',
    }


def test_clearing_a_switch_that_left_nothing_behind_changes_nothing():
    assert clear_switch_bridge(parse_conf(SYSTEM_CONF), 'other') == parse_conf(SYSTEM_CONF)


def test_a_switch_that_does_not_exist_yet_is_created():
    assert plan_switch({}, name='lan', bridge='bridge0', state='present') == 'create'


def test_a_switch_on_the_declared_bridge_is_left_alone():
    assert plan_switch(
        parse_conf(SYSTEM_CONF), name='public', bridge='bridge0', state='present',
    ) == 'keep'


def test_a_switch_pointing_at_another_bridge_is_rebuilt():
    # vm-bhyve cannot re-point a switch, so it has to go and come back
    assert plan_switch(
        parse_conf(SYSTEM_CONF), name='public', bridge='bridge1', state='present',
    ) == 'recreate'


def test_an_unwanted_switch_is_destroyed():
    assert plan_switch(
        parse_conf(SYSTEM_CONF), name='public', bridge=None, state='absent',
    ) == 'destroy'


def test_a_switch_that_is_already_gone_is_left_alone():
    assert plan_switch({}, name='public', bridge=None, state='absent') == 'keep'


def test_a_switch_is_recreated_where_only_its_stale_bridge_setting_survived():
    # the setting 'vm switch destroy' left behind must not look like a switch
    left_behind = parse_conf('switch_list=""\nbridge_public="bridge0"\n')

    assert plan_switch(
        left_behind, name='public', bridge='bridge0', state='present',
    ) == 'create'


def test_a_disk_without_an_image_file_is_created():
    conf = build_guest_conf(existing={}, params={'disks': [{'size': '20G'}]})

    assert plan_disks(conf, [{'size': '20G'}], sizes={0: None}) == [
        {
            'index': 0, 'name': 'disk0.img', 'action': 'create',
            'size': 20 * 1024 ** 3, 'dev': 'file', 'volblocksize': None,
        },
    ]


def test_a_disk_declared_bigger_than_its_image_file_is_grown():
    conf = build_guest_conf(existing={}, params={'disks': [{'size': '20G'}]})

    assert plan_disks(conf, [{'size': '20G'}], sizes={0: 5 * 1024 ** 3}) == [
        {
            'index': 0, 'name': 'disk0.img', 'action': 'grow',
            'size': 20 * 1024 ** 3, 'dev': 'file', 'volblocksize': None,
        },
    ]


def test_a_disk_that_is_already_the_declared_size_is_left_alone():
    conf = build_guest_conf(existing={}, params={'disks': [{'size': '20G'}]})

    assert plan_disks(conf, [{'size': '20G'}], sizes={0: 20 * 1024 ** 3}) == [
        {
            'index': 0, 'name': 'disk0.img', 'action': 'keep',
            'size': 20 * 1024 ** 3, 'dev': 'file', 'volblocksize': None,
        },
    ]


def test_a_zvol_backed_disk_is_planned_as_the_volume_it_is():
    disks = [{'size': '40G', 'dev': 'zvol', 'volblocksize': '128k'}]
    conf = build_guest_conf(existing={}, params={'disks': disks})

    assert plan_disks(conf, disks, sizes={0: None}) == [
        {
            'index': 0, 'name': 'disk0', 'action': 'create',
            'size': 40 * 1024 ** 3, 'dev': 'zvol', 'volblocksize': '128k',
        },
    ]


def test_a_zvol_is_named_as_a_dataset_rather_than_a_file():
    # it is a volume below the guest's dataset, where an '.img' suffix would
    # only suggest a file that is not there
    conf = build_guest_conf(
        existing={}, params={'disks': [{'size': '40G', 'dev': 'sparse-zvol'}]},
    )

    assert conf['disk0_name'] == 'disk0'
    assert conf['disk0_dev'] == 'sparse-zvol'


def test_a_file_backed_disk_says_nothing_about_its_backing():
    # 'file' is vm-bhyve's own default, so writing it would mark every guest
    # that predates zvol support as changed
    conf = build_guest_conf(existing={}, params={'disks': [{'size': '20G'}]})

    assert 'disk0_dev' not in conf


def test_an_undeclared_backing_keeps_the_one_the_disk_has():
    existing = parse_conf('disk0_name="disk0"\ndisk0_dev="zvol"\n')
    conf = build_guest_conf(existing=existing, params={'disks': [{'size': '40G'}]})

    assert conf['disk0_dev'] == 'zvol'
    assert conf['disk0_name'] == 'disk0'


def test_rebacking_an_existing_disk_is_refused():
    # the data is in the backing store, so swapping it is not a reconfiguration
    # but a silent wipe
    existing = parse_conf('disk0_name="disk0"\ndisk0_dev="zvol"\n')

    with raises(BhyveError, match='cannot be turned into'):
        build_guest_conf(existing=existing, params={'disks': [{'size': '40G', 'dev': 'file'}]})


def test_only_volumes_count_as_zvols():
    assert is_zvol('zvol')
    assert is_zvol('sparse-zvol')
    assert not is_zvol('file')
    assert not is_zvol(None)


def test_shrinking_a_disk_is_refused():
    # truncating a disk the guest has a filesystem on destroys data, so we stop
    conf = build_guest_conf(existing={}, params={'disks': [{'size': '20G'}]})

    with raises(BhyveError, match='cannot be shrunk'):
        plan_disks(conf, [{'size': '5G'}], sizes={0: 20 * 1024 ** 3})


def test_a_guest_is_autostarted_by_joining_the_rc_conf_list():
    assert apply_autostart(['nixos'], 'media', enabled=True) == ['nixos', 'media']


def test_autostarting_a_guest_twice_does_not_list_it_twice():
    assert apply_autostart(['nixos'], 'nixos', enabled=True) == ['nixos']


def test_a_guest_stops_autostarting_by_leaving_the_list():
    assert apply_autostart(['nixos', 'media'], 'nixos', enabled=False) == ['media']


def test_leaving_a_list_a_guest_is_not_on_changes_nothing():
    assert apply_autostart(['media'], 'nixos', enabled=False) == ['media']


def test_a_zfs_datastore_names_a_dataset():
    assert parse_datastore('zfs:zroot/virtual-machines') == ('zfs', 'zroot/virtual-machines')


def test_a_plain_datastore_is_just_a_directory():
    assert parse_datastore('/data/virtual-machines') == ('dir', '/data/virtual-machines')


def test_names_vm_bhyve_would_reject_are_rejected():
    # mirrors 'util::check_name'
    assert is_valid_name('nixos')
    assert is_valid_name('web-01.lan')
    assert not is_valid_name('-nixos')
    assert not is_valid_name('nixos-')
    assert not is_valid_name('ni xos')
    assert not is_valid_name('')


def test_a_diff_shows_only_what_changes():
    before = parse_conf(GUEST_CONF_NIXOS)
    after = build_guest_conf(existing=before, params={'cpu': 2})

    assert conf_diff(before, after) == {
        'before': {'cpu': '1'},
        'after': {'cpu': '2'},
    }


def test_a_diff_reports_added_and_removed_settings():
    diff = conf_diff({'cpu': '1', 'memory': '512M'}, {'cpu': '1', 'autostart': 'yes'})

    assert diff == {
        'before': {'memory': '512M'},
        'after': {'autostart': 'yes'},
    }


def test_an_unchanged_conf_has_an_empty_diff():
    conf = parse_conf(GUEST_CONF_NIXOS)

    assert conf_diff(conf, build_guest_conf(existing=conf, params={'cpu': 1})) == {
        'before': {}, 'after': {},
    }


def test_rewriting_a_conf_in_a_different_style_is_not_a_change():
    # we compare settings, not bytes, so re-quoting alone never rewrites the file
    conf = parse_conf(GUEST_CONF_NIXOS)

    assert conf_diff(conf, parse_conf(render_conf(conf))) == {'before': {}, 'after': {}}


def test_dropping_a_disk_is_refused():
    # guarded where the conf is built, so no caller can drop a disk by accident
    existing = parse_conf(
        'disk0_name="disk0.img"\n'
        'disk1_name="disk1.img"\n'
    )

    with raises(BhyveError, match='disk1'):
        build_guest_conf(existing=existing, params={'disks': [{'size': '20G'}]})
