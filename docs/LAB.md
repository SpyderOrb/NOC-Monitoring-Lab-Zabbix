# Setup and file locations

The main learning path is a manual Ubuntu installation through **virt-manager**. Set up the host, create storage and networking, install each guest, then verify SSH and package health before adding monitoring. See [validation](VALIDATION.md) for observed results and remaining checks.

## Lab layout

| VM | vCPU | RAM | Virtual disk capacity | Reserved IPv4 |
|---|---:|---:|---:|---|
| zabbix-server | 2 | 4 GiB | 25 GiB | 192.168.77.10 |
| linux-target | 1 | 2 GiB | 16 GiB | 192.168.77.20 |

Both manually installed guests run Ubuntu Server 24.04.5 LTS with virtio devices and BIOS boot. Each has a small GRUB boot partition and an ext4 root partition, without LVM or guest disk encryption. These are starting allocations, not measured monitoring capacity requirements. Sparse qcow2 files grow with use; virtual capacity is not their physical disk usage.

## What is installed where?

`<project>` means the repository directory. Running an installer from that directory does not make its installation local.

| Scope | Contents and installation method | Location |
|---|---|---|
| **Host: system packages** | QEMU/KVM, libvirt, virt-manager and supporting tools, installed through the host package manager | Executables under `/usr/bin`; package files elsewhere in the host filesystem |
| **Host: system configuration** | libvirt VM, pool and network definitions; scoped firewall rules | Definitions under `/etc/libvirt`, runtime state under `/var/lib/libvirt`; firewall configuration belongs to the host |
| **Project: installation media** | Ubuntu Server ISO and downloaded checksum/signature files | `images/ubuntu-24.04.5/`; ISO observed as 3.80 GiB |
| **Project: guest disks** | Independent qcow2 volumes created in virt-manager | `vms/zabbix-server.qcow2` and `vms/linux-target.qcow2`; capacities 25 and 16 GiB |
| **Project: private access files** | Client SSH key, known-host records and client configuration | `credentials/`, excluded from Git |
| **Project: backups** | Preserved disks/configuration and future backups | `backups/`, excluded from Git; allow additional storage |
| **Host: user directory** | `ssh-copy-id` uses temporary working files here | `~/.ssh/`; lab keys and known-host records remain in the project |
| **Inside each guest** | Ubuntu packages and OpenSSH, installed through the Ubuntu installer and APT | Guest `/usr`, `/etc`, `/var`; physically backed by that guest's qcow2 file |
| **Inside each guest: SSH access** | Public client key installed with `ssh-copy-id` | Guest user's `~/.ssh/authorized_keys`; private key stays on the host |

Zabbix 7.0.31, PostgreSQL 16, Nginx and PHP 8.3 FPM are installed **inside the server guest**, with server self-monitoring verified in the frontend. Agent 2 version 7.0.31 is installed inside the target guest, with CPU and memory values visible through passive polling. The target HTTP service remains pending. No workstation inventory or total host package-size estimate is published; those figures depend on the host and shared dependencies.

## Storage and networking are separate

The **`noc-lab` storage pool** registers `<project>/vms/` with libvirt. It is a folder of disks, not another VM. The **`noc-lab` network** connects guest network cards. Sharing a name does not connect these objects automatically: select both explicitly when creating a VM.

The manual network uses `192.168.77.0/24`, gateway `192.168.77.1`, NAT, DHCP range `.100`–`.199` and DNS domain `noc-lab`. Its observed host bridge is `virbr1`; generated bridge names can differ on another computer. DHCP reservations associate each guest's actual MAC address with `.10` or `.20`. Ubuntu continues to use DHCP.

Choose a non-overlapping subnet. NAT allows guest-initiated access to the internet and LAN; it is not complete isolation from the LAN. If the host firewall blocks traffic, permit DHCP/DNS and outbound forwarding only for the actual lab bridge/subnet and host uplink. Keep the firewall enabled.

With `qemu:///system`, QEMU runs under a service account. Check its identity and save existing permissions before granting narrow directory traversal and access to `vms/` and installation media. Do not grant recursive access to the entire home directory, credentials or backups. Verify access as the service account. See [libvirt file access](https://libvirt.org/drvqemu.html#security-infrastructure).

Pool/network autostart makes those resources available when libvirt starts. Guest autostart is a separate choice.

## Manual build sequence

1. **Prepare the host.** Check virtualization support, available resources and existing networks. Install the host virtualization tools and enable the required libvirt services for your distribution.
2. **Create project storage and the NAT network.** Register a directory pool targeting `<project>/vms/`; check QEMU access. Create the network described above and review scoped firewall allowances.
3. **Obtain and verify Ubuntu.** The observed installer is `ubuntu-24.04.5-live-server-amd64.iso` from [Ubuntu releases](https://releases.ubuntu.com/24.04/). Download its checksum list and signature alongside it. Follow [Ubuntu's verification procedure](https://ubuntu.com/tutorials/how-to-verify-ubuntu): authenticate the manifest and verify the ISO hash. A cloud image is a preinstalled disk and does not provide this interactive installation path.
4. **Create each VM in virt-manager.** Choose local ISO installation, the allocations above, a separate sparse qcow2 volume in `noc-lab` storage, and the `noc-lab` NAT network. Never share the same writable guest disk between these VMs.
5. **Install Ubuntu.** Choose standard Ubuntu Server, a suitable keyboard, automatic DHCP, no proxy unless your network requires one, and a working package mirror. Review the selected virtual disk before formatting. Set the appropriate hostname and a local administrator account. Enable OpenSSH with initial password access; skip Ubuntu Pro attachment and optional featured snaps for this lab.
6. **Boot from the installed disk.** Eject virtual installation media if requested; retain the ISO file. Check hostname, interface address, default route and SSH service/socket state. An active SSH socket can start an otherwise inactive SSH service on demand.
7. **Reserve addresses and configure SSH.** Check actual guest MACs and existing leases before adding DHCP reservations to both live and persistent network configuration. Reacquire the guest lease and verify the address. Compare the server's public host-key fingerprint from its console before trusting the first SSH connection. Create a project-local client key, copy only its public half to each guest, and test key-only login before considering any password-login changes.
8. **Update and inspect each guest.** Run `sudo apt update`, review `apt list --upgradable`, then `sudo apt upgrade`. Reboot when appropriate and verify `systemctl --failed --no-pager`, `sudo dpkg --audit` and guest addressing. Finally test connectivity between the guests before configuring monitoring.

The local SSH client file is invoked from the project root using `ssh -F credentials/ssh_config.manual zabbix-server` or `linux-target`. Its relative key/known-host paths rely on that working directory. Private access files are intentionally not shipped in this repository.

## Configuration choices and historical automation

You control VM sizing, disk capacity, subnet, guest accounts and authentication. Shut down a guest before changing persistent resource settings where required; keep reservations consistent with guest MACs. Monitoring intervals, thresholds and dashboards will be chosen during the monitoring stage.

The existing [creation script](../scripts/create-guests.py), [cloud-init template](../configs/cloud-init/user-data.example) and [network XML](../configs/libvirt/noc-lab.xml) belong to the earlier **cloud-image baseline**. They use different allocations, UEFI, a system disk pool and fixed MAC/network settings. They are historical examples, not an installer or update command for the manual setup. Do not run them over these guests. The [historical evidence](evidence/2026-09-27-guest-baseline.txt) records that separate build.
