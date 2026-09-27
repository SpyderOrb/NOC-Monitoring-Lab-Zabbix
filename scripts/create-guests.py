#!/usr/bin/env python3
"""Create the two lab guests from the pinned, signature-verified Ubuntu image.

Run as root with IMAGE and SSH_PUBLIC_KEY arguments after authenticating SHA256SUMS.
Existing guests, disks and rendered configuration are never overwritten.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import uuid
import xml.etree.ElementTree as ET

import libvirt


IMAGE_SHA256 = '6a81c37564db9b1ee84e141922625e1d7c5b389b99bb3c572e0243607d5bb4d2'
GUESTS = (
    ('zabbix-server', 4096, 2, 24, '52:54:00:77:00:10', '192.168.77.10'),
    ('linux-target', 1024, 1, 12, '52:54:00:77:00:20', '192.168.77.20'),
)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('image', type=Path)
    parser.add_argument('ssh_public_key', type=Path)
    args = parser.parse_args()
    if os.geteuid() != 0:
        raise SystemExit('Run through sudo or pkexec; system libvirt requires administrative access.')
    image = args.image.resolve(strict=True)
    with image.open('rb') as source:
        if hashlib.file_digest(source, 'sha256').hexdigest() != IMAGE_SHA256:
            raise SystemExit('Image checksum does not match Ubuntu release build 20260926.')
    key = args.ssh_public_key.read_text().strip()
    if not key.startswith('ssh-ed25519 ') or '\n' in key:
        raise SystemExit('Provide one Ed25519 public key, not a private key.')

    project = Path(__file__).resolve().parent.parent
    template = (project / 'configs/cloud-init/user-data.example').read_text()
    state = project / '.project/cloud-init'
    pool_path = Path('/var/lib/libvirt/images/noc-lab')
    meminfo = dict(line.split(':', 1) for line in Path('/proc/meminfo').read_text().splitlines())
    if int(meminfo['MemAvailable'].split()[0]) < 7 * 1024 * 1024:
        raise SystemExit('Need at least 7 GiB available RAM for the 5 GiB guest budget plus headroom.')
    if shutil.disk_usage(pool_path).free < 45 * 1024**3:
        raise SystemExit('Need at least 45 GiB free disk for guest capacities and host headroom.')

    with libvirt.open('qemu:///system') as conn:
        network = conn.networkLookupByName('noc-lab')
        pool = conn.storagePoolLookupByName('noc-lab')
        if not network.isActive() or not pool.isActive():
            raise SystemExit('The noc-lab network and pool must be active.')
        if ET.fromstring(pool.XMLDesc()).findtext('target/path') != str(pool_path):
            raise SystemExit('Unexpected noc-lab pool path.')
        reservations = {h.get('mac'): h.get('ip') for h in ET.fromstring(network.XMLDesc()).findall('ip/dhcp/host')}
        names = {domain.name() for domain in conn.listAllDomains()}
        for name, _, _, _, mac, address in GUESTS:
            if reservations.get(mac) != address:
                raise SystemExit(f'DHCP reservation mismatch: {name}')
            if name in names or (pool_path / f'{name}.qcow2').exists() or (state / name).exists():
                raise SystemExit(f'{name} already has state; inspect it instead of recreating it.')

        os.umask(0o077)
        state.mkdir(parents=True, exist_ok=True)
        for name, memory, cpus, disk_gib, mac, _ in GUESTS:
            seed = state / name
            seed.mkdir()
            (seed / 'user-data').write_text(template.replace('__HOSTNAME__', name).replace('__SSH_PUBLIC_KEY__', json.dumps(key)))
            (seed / 'meta-data').write_text(json.dumps({'instance-id': f'{name}-{uuid.uuid4()}', 'local-hostname': name}) + '\n')
            network_data = {'version': 2, 'ethernets': {'lab0': {
                'match': {'macaddress': mac}, 'set-name': 'lab0',
                'dhcp4': True, 'dhcp-identifier': 'mac', 'dhcp6': False, 'accept-ra': False,
            }}}
            (seed / 'network-config').write_text(json.dumps(network_data) + '\n')
            disk = pool_path / f'{name}.qcow2'
            print(f'Preparing {name}: {cpus} vCPU, {memory} MiB RAM, {disk_gib} GiB disk.', flush=True)
            subprocess.run(['qemu-img', 'convert', '-f', 'qcow2', '-O', 'qcow2', str(image), str(disk)], check=True)
            subprocess.run(['qemu-img', 'resize', str(disk), f'{disk_gib}G'], check=True)
            pool.refresh()
            subprocess.run([
                'virt-install', '--connect', 'qemu:///system', '--name', name,
                '--memory', str(memory), '--vcpus', str(cpus), '--cpu', 'host-model',
                '--machine', 'q35', '--virt-type', 'kvm', '--osinfo', 'ubuntu24.04',
                '--import', '--boot', 'uefi,firmware.feature0.name=secure-boot,firmware.feature0.enabled=no',
                '--disk', f'path={disk},format=qcow2,bus=virtio',
                '--network', f'network=noc-lab,model=virtio,mac={mac}',
                '--graphics', 'none', '--console', 'pty,target_type=serial',
                '--channel', 'unix,target_type=virtio,name=org.qemu.guest_agent.0',
                '--cloud-init', f'user-data={seed / "user-data"},meta-data={seed / "meta-data"},network-config={seed / "network-config"}',
                '--noautoconsole',
            ], check=True)
            conn.lookupByName(name).setAutostart(0)
        print('Both domains created. Wait for cloud-init and verify guest networking before proceeding.', flush=True)


if __name__ == '__main__':
    main()
