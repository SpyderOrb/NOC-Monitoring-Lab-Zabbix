# Lab setup

Two Ubuntu VMs are ready; monitoring is the next step. This page describes the lab configuration and how its guest baseline was built. See [validation](VALIDATION.md) for observed results, rather than assuming every planned feature already works.

## What runs where

- **Physical host:** QEMU/KVM runs the VMs; libvirt manages their network and disks. virt-manager is the graphical management tool.
- **zabbix-server:** will collect monitoring data, store it in a database and serve the browser dashboard.
- **linux-target:** will run Zabbix Agent 2 and a small HTTP service. Fault exercises happen here.

The VMs currently run Ubuntu Server **24.04.5 LTS**. Zabbix **7.0 LTS** is planned, not installed.

## Lab settings

| VM | vCPU | RAM | Disk capacity | Reserved IP | MAC address |
|---|---:|---:|---:|---|---|
| zabbix-server | 2 | 4 GiB | 24 GiB | 192.168.77.10 | 52:54:00:77:00:10 |
| linux-target | 1 | 1 GiB | 12 GiB | 192.168.77.20 | 52:54:00:77:00:20 |

These are starting allocations for this small lab, not production sizing recommendations. Reassess memory after installing services. Each VM uses UEFI, virtio devices and its own qcow2 disk; sparse disk files grow as data is written.

The `noc-lab` network uses subnet `192.168.77.0/24`, gateway `192.168.77.1`, bridge `virbr-noc` and DNS domain `noc.test`. DHCP assigns the reserved addresses above; its dynamic range is `.100`–`.199`. NAT lets guests reach package repositories without connecting them directly to the physical LAN. It also permits guest-initiated LAN access; it is not full isolation from your LAN.

## Prepare your own virtualization host

Use a Linux host with hardware virtualization enabled. Install QEMU/KVM, libvirt, virt-manager, virt-install, UEFI firmware, dnsmasq and Python libvirt bindings using your distribution's instructions. Service names and firewall setup vary by distribution.

Before creating anything, check available memory/storage, existing libvirt networks and routes. Choose a lab subnet that does not overlap your LAN or VPN. The optional creation script requires at least **7 GiB available RAM and 45 GiB free disk** before it starts; these are its guardrails, not measurements of the author's computer.

Run these inspection commands **on the physical host**:

```sh
ip route
virsh -c qemu:///system --readonly net-list --all
virsh -c qemu:///system --readonly pool-list --all
```

On a new setup, review [the network XML](../configs/libvirt/noc-lab.xml), then create the network and storage pool from the repository root. Skip creation when they already exist; inspect them instead.

```sh
sudo virsh -c qemu:///system net-define configs/libvirt/noc-lab.xml
sudo virsh -c qemu:///system net-start noc-lab
sudo virsh -c qemu:///system net-autostart noc-lab
sudo install -d -m 0755 /var/lib/libvirt/images/noc-lab
sudo virsh -c qemu:///system pool-define-as noc-lab dir --target /var/lib/libvirt/images/noc-lab
sudo virsh -c qemu:///system pool-start noc-lab
sudo virsh -c qemu:///system pool-autostart noc-lab
```

If your host firewall blocks the lab, allow guest DHCP, DNS to the lab gateway and outbound forwarding through your actual uplink. Keep the firewall enabled; do not copy an interface name from another computer. Verify guest DNS and package access after boot.

Network and pool autostart are enabled in this build. **VM autostart is disabled:** opening the storage pool does not start the guests.

## Create and access the guests

### Reproduce guest creation

1. Obtain `ubuntu-24.04-server-cloudimg-amd64.img`, `SHA256SUMS` and `SHA256SUMS.gpg` from the [official release build 20260926](https://cloud-images.ubuntu.com/releases/noble/release-20260926/). Use the released build, not the moving daily image URL.
2. Follow [Canonical's signature verification procedure](https://ubuntu.com/docs/public-images/public-images-how-to/verify-image-checksum/). The verified signing fingerprint is `D2EB44626FDDC30B513D5BB71A5D6C4C7DB87C81`. Then check the image against the authenticated manifest. The expected SHA256 is:

   ```text
   6a81c37564db9b1ee84e141922625e1d7c5b389b99bb3c572e0243607d5bb4d2
   ```

3. Prepare a dedicated SSH key and run [the provisioner](../scripts/create-guests.py) from the repository root. These are first-creation commands; keep any existing key and guests instead of replacing them:

   ```sh
   install -d -m 700 credentials
   ssh-keygen -t ed25519 -N '' -C noc-lab-admin -f credentials/noc-lab_ed25519
   sudo python3 scripts/create-guests.py \
     images/ubuntu-24.04-20260926/ubuntu-24.04-server-cloudimg-amd64.img \
     credentials/noc-lab_ed25519.pub
   ```

The provisioner checks the pinned image hash, available resources and DHCP reservations, and refuses existing guest names, disks or rendered configuration. It requires the prepared `noc-lab` network/pool and the host's libvirt Python bindings. It creates independent disks, injects [cloud-init user data](../configs/cloud-init/user-data.example) and boots both guests. Partial failures leave state for inspection; the script does not delete or recreate existing guests automatically.

Cloud-init creates the `noc` administrator, disables SSH password login, generates distinct host keys, sets UTC, installs QEMU guest agent and updates APT metadata. Passwordless sudo is limited to the lab's administrator account inside each guest. Rendered data and keys stay excluded from Git. Guest initialization completed without errors in this build.

Connect with the project key, for example `ssh -i credentials/noc-lab_ed25519 -o UserKnownHostsFile=credentials/known_hosts noc@192.168.77.10` (target: `.20`). Confirm the first host key, retain it and do not disable host-key checking. After a physical-host restart, start each guest using `sudo virsh -c qemu:///system start zabbix-server` and `sudo virsh -c qemu:///system start linux-target`.

## What the repository can reproduce

The network XML, cloud-init template and creation script reproduce the documented guest baseline with the pinned image. They do **not** install Zabbix, create a dashboard or run fault exercises. Exact guest versions and checks are recorded in [validation](VALIDATION.md).

The creation script is optional automation for a fresh lab. Review it before running it: it creates and boots both VMs. For existing guests, use SSH and virt-manager or `virsh`; do not rerun provisioning to apply changes.
