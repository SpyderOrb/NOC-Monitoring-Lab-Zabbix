# Start here: understand and build the lab

This is a small learning lab, not a finished monitoring product. Two Ubuntu VMs have been built and checked. The next milestone is **one real measurement from the target visible in Zabbix**.

Read this page for the story and learning order, [LAB.md](LAB.md) for setup details, and [VALIDATION.md](VALIDATION.md) for evidence of what actually worked.

## The idea in plain English

Imagine a small service that should stay available. Monitoring helps you notice when it stops working and confirm when it recovers.

| Part | Job |
|---|---|
| Your physical computer | Runs the two virtual machines. It is not the fault-test target. |
| `zabbix-server` VM | Will run Zabbix, its database and its web interface. It is the monitoring station. |
| `linux-target` VM | Will run a tiny website and a monitoring agent. This is the machine we deliberately break and repair. |
| Browser | Will show the Zabbix interface: measurements, graphs and problems. |
| `noc-lab` virtual network | Connects the VMs and gives them access to package repositories through NAT. |

The intended flow is:

1. The target's **agent** provides measurements such as CPU usage. Separately, Zabbix checks whether the HTTP service answers.
2. Zabbix stores measurements as **items**. An item is one thing being measured.
3. A **trigger** evaluates a condition, such as CPU usage staying too high for a chosen period.
4. A matching condition creates a **problem event** in the interface. After the condition clears, a recovery event records that change.
5. You investigate, restore the service, and compare the fault time with the problem and recovery times.

A **template** is a reusable collection of monitoring settings. A **dashboard** presents selected results. Neither replaces checking the actual measurements and event times.

The existing **QEMU guest agent** helps libvirt manage the VMs. It is different from **Zabbix Agent 2**, which is not installed yet.

## Roadmap: one visible result at a time

| Step | State | What you do | How you know it worked |
|---|---|---|---|
| 1. Build the lab | Verified on 2026-09-27 | Prepare virtualization, create both Ubuntu guests, connect over SSH. | Guests boot; SSH, peer connectivity, DNS and package access work. |
| 2. Get the first metric | Next | Install the Zabbix server/database/frontend, install Agent 2 on the target, and add the target in Zabbix. | A target measurement appears with a recent timestamp. |
| 3. Make normal operation visible | Planned | Add the HTTP service, host/HTTP/CPU checks and a small dashboard. Choose intervals and thresholds. | Normal readings make sense and there are no unexplained problems. |
| 4. Break and repair | Planned | Stop HTTP, shut down the target, then run a bounded CPU load; restore normal operation after each exercise. | Each fault produces the expected problem and recovery, with recorded times. |
| 5. Package the results | Planned | Export reusable monitoring settings and write short recovery runbooks. | Another reader can understand the checks and repeat the documented exercises. |

Do not start fault experiments until normal monitoring works. For each exercise record: fault start, first problem, service restoration, recovery event, and the polling/evaluation settings. Notifications initially stay in the local dashboard.

Installation commands for the monitoring stack will be documented as that stage is implemented and checked. This repository currently reproduces the **guest baseline**, not the full roadmap.

## Your controls

You can change the lab deliberately rather than accepting every default. Change one thing, understand the effect, and check the result before moving on.

| Choice | Where you control it | When it takes effect |
|---|---|---|
| VM CPU and RAM | Before creation: `GUESTS` in [create-guests.py](../scripts/create-guests.py). Existing VM: shut it down normally, edit its allocation in virt-manager, then start it. | Creation or the next boot after editing the VM definition. |
| Lab addresses | [Network XML](../configs/libvirt/noc-lab.xml); keep the script's guest MAC/IP values consistent. | When applied to libvirt and guest leases are renewed; editing the file alone does not change the live network. |
| Initial guest user and packages | [cloud-init template](../configs/cloud-init/user-data.example). | First boot of a newly created guest. Existing guests are managed through SSH. |
| Starting and stopping VMs | virt-manager, or `virsh` on the physical host. | Immediately; stopping the target later becomes a monitoring exercise. |
| What to monitor, how often, and when to alert | Zabbix items, templates and triggers, once installed. | After saving the monitoring configuration and waiting for collection/evaluation. |
| What you see | Zabbix dashboard widgets, once installed. | After saving the dashboard. |

The optional creation script has fixed defaults: network/pool names, storage path, image checksum and minimum free-resource checks. It is a small reproducible helper, not a general configuration tool. Read it before use. Changing VM sizes also means reviewing its resource checks. For an existing lab, work with the VMs directly instead of rerunning the script.

For learning, use a short cycle: **understand the purpose → choose the setting → run the step yourself → inspect the output → record the result**. Keep credentials and personal notes outside public commits.

## First hands-on session: find your way around

These checks inspect an existing lab without changing its configuration. Use the addresses and SSH key from your own setup if they differ.

**On the physical host**, from the repository root:

```sh
virsh -c qemu:///system --readonly list --all
```

You should see `zabbix-server` and `linux-target`. If a VM is stopped, start it in virt-manager. Do not create it again. Connect to the target:

```sh
ssh -i credentials/noc-lab_ed25519 -o UserKnownHostsFile=credentials/known_hosts noc@192.168.77.20
```

On first connection, verify the displayed host-key fingerprint against the guest's console before accepting it. Keep host-key checking enabled.

**Inside linux-target**:

```sh
hostname
ip -br address
ping -c 3 192.168.77.10
cloud-init status --long
```

For this lab, expect hostname `linux-target`, address `192.168.77.20`, replies from the server and completed cloud-init. A ping proves network reachability; it does not prove Zabbix is installed or healthy. Use `exit` to return to the physical host.

Once you can identify which machine you are using and explain these results, move to step 2: install the monitoring stack in small, checked steps.
