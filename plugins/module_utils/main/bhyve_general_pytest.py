from ansible_collections.oxlorg.opnsense.plugins.module_utils.main.bhyve_general import \
    PACKAGES, REPO_DIRS, REPO_OVERLAY


def test_the_host_gets_vm_bhyve_and_both_loaders():
    # 'bhyve-firmware' is what pulls in 'edk2-bhyve', so uefi guests can boot
    assert PACKAGES == ['vm-bhyve', 'grub2-bhyve', 'bhyve-firmware']


def test_packages_are_installed_from_the_hosts_own_repositories_too():
    # the overlay only adds a repository, so dependencies still resolve against
    # OPNsense's and the packages it has priority on stay its own
    assert REPO_DIRS == ['/etc/pkg', '/usr/local/etc/pkg/repos']


def test_the_overlay_only_re_enables_the_ports_repository():
    # see ADR-0002: OPNsense ships FreeBSD-ports disabled and re-disables it on
    # upgrade, so it is enabled for a single pkg transaction instead of on disk
    assert REPO_OVERLAY.strip() == 'FreeBSD-ports: { enabled: yes }'
