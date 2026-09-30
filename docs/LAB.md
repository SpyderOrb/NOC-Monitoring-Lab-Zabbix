# Setup and file locations

This guide describes the reproducible Ubuntu guest baseline. **Monitoring setup is in progress:** Zabbix and the fault exercises are not included in the creation script. See [validation](VALIDATION.md) for tested scope.

## Lab layout

| VM | vCPU | RAM | Virtual disk capacity | Reserved IPv4 |
|---|---:|---:|---:|---|
| zabbix-server | 2 | 4 GiB | 24 GiB | 192.168.77.10 |
| linux-target | 1 | 1 GiB | 12 GiB | 192.168.77.20 |

Both guests use Ubuntu Server 24.04 LTS, UEFI and virtio devices. These are small-lab starting allocations; reassess them after installing services. Sparse qcow2 disks grow with use, so virtual capacity is different from space occupied on the physical disk. Backups need additional space.

The [network definition](../configs/libvirt/noc-lab.xml) creates `noc-lab`: subnet `192.168.77.0/24`, gateway `192.168.77.1`, bridge `virbr-noc`, DNS domain `noc.test`, dynamic DHCP range `.100`–`.199` and reserved guest addresses `.10`/`.20`. NAT permits guest-initiated access to the internet and LAN; it is not full isolation from the LAN. Choose a different subnet if it overlaps your network or VPN.

## Installation scope and file locations

`<project>` means the repository directory. Running a command there does not make its installation local.

| Location | What lives there | Concrete example |
|---|---|---|
| **Physical host — system packages** | QEMU/KVM, libvirt, virt-manager, virt-install, dnsmasq, UEFI firmware and dependencies, installed through the host package manager | `virt-manager` launches from `/usr/bin/virt-manager`; QEMU from `/usr/bin/qemu-system-x86_64`. Paths vary by distribution. |
| **Physical host — system configuration** | libvirt services, registered definitions, network/firewall rules and per-VM firmware state | Configuration under `/etc/libvirt`; state under `/var/lib/libvirt`; UEFI variables under `/var/lib/libvirt/qemu/nvram`. |
| **Project — reusable files** | Network XML, guest template and helper script | `configs/libvirt/noc-lab.xml` is a source file; registering it creates a separate libvirt-managed network. |
| **Project — private local files** | Downloaded media, SSH keys and backups; excluded from Git | `images/`, `credentials/`, `backups/`. These are data files, not host-installed applications. |
| **Guest disks** | Ubuntu and its installed packages; future Zabbix/database/HTTP packages live inside the guests | The documented script stores qcow2 files in `/var/lib/libvirt/images/noc-lab/`. |

**Project-local guest storage is planned:** a pool targeting `<project>/vms/`. The current script still uses the system path above. Moving the disks requires updating libvirt and verifying QEMU access to the new directory; it does not move system services or network rules into the project. See [libvirt file access](https://libvirt.org/drvqemu.html#security-infrastructure).

```text
Physical host: virtualization packages, service and network rules
  Project: configuration sources, installation media, keys and backups
  Guest disk: Ubuntu filesystem, guest packages and application data
```

### Access to project-local disks

With `qemu:///system`, the VM process uses a service account rather than your desktop login. A private home directory can therefore block access even when the disk path is correct.

Before creating a pool in the project:

- Identify the QEMU service account and save the original directory permissions.
- Grant that account directory traversal through the required parent directories and access to the dedicated `vms/` directory. An ACL can grant access to one account without opening the directory to everyone.
- Keep `credentials/` and backups private; do not apply recursive permission changes to the entire project or home directory.
- Verify access as the service account, then recheck disk ownership and permissions after libvirt creates the first volume.

The pool definition is still system-managed; only its data directory is project-local. Pool autostart makes storage available when libvirt starts—it does not automatically start guests. Guest autostart is a separate setting.

## Where Ubuntu comes from

The baseline uses an official **Ubuntu Server cloud image from Canonical**, build `20260926`, named `ubuntu-24.04-server-cloudimg-amd64.img`:

[Official release image and checksum files](https://cloud-images.ubuntu.com/releases/noble/release-20260926/)

A cloud image is an already installed base OS designed to boot in a VM. It differs from an installer ISO, which walks you through installing Ubuntu onto an empty disk. The image was copied into two independent disks; cloud-init supplied the initial user, SSH access and guest settings. The signed checksum manifest and image digest were verified before use.

Ubuntu images are not committed to this repository. Exact image hash, observed guest version and test results are in [the baseline evidence](evidence/2026-09-27-guest-baseline.txt).

## Reproduce the cloud-image baseline

This is an optional automated path for a **fresh lab**, using the system storage path above. It is not a manual ISO walkthrough and does not modify existing guests. Read the script and template before running them.

Prerequisites: a Linux host with KVM support; QEMU/libvirt, virt-install, UEFI firmware, dnsmasq and Python libvirt bindings. Prepare the host using your distribution's instructions. The helper requires at least **7 GiB available RAM and 45 GiB free disk**; these are its fixed checks, not a complete capacity estimate.

<details>
<summary>Network, storage and first-boot commands</summary>

Run on the physical host, from the project root. Inspect existing networks/routes first. Do not recreate an existing `noc-lab` network or pool.

```sh
sudo virsh -c qemu:///system net-define configs/libvirt/noc-lab.xml
sudo virsh -c qemu:///system net-start noc-lab
sudo virsh -c qemu:///system net-autostart noc-lab
sudo install -d -m 0755 /var/lib/libvirt/images/noc-lab
sudo virsh -c qemu:///system pool-define-as noc-lab dir --target /var/lib/libvirt/images/noc-lab
sudo virsh -c qemu:///system pool-start noc-lab
sudo virsh -c qemu:///system pool-autostart noc-lab
```

If the host firewall blocks guest traffic, configure scoped DHCP, DNS and outbound forwarding allowances for your actual lab interface and uplink. Keep the firewall enabled. Network/pool autostart does not start the guests; guest autostart is disabled in this baseline.

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

</details>

## What you can change

The script's `GUESTS` entries specify memory, CPUs, disk capacity, MAC and reserved IP. Keep MAC/IP settings consistent with the network XML and review the fixed resource checks when changing allocations. The pool path and image checksum are also fixed in the script. The cloud-init template controls initial guest settings; editing it does not update an already created VM.

For an existing guest, use virt-manager and SSH. Check baseline connectivity before adding monitoring, and keep credentials and generated files outside Git.
