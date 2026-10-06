# Understand the lab

The idea is simple: one machine watches another, you introduce a controlled fault, and monitoring helps you notice and explain what happened.

This page explains the current lab. [Validation](VALIDATION.md) records the test results and remaining limits; [LAB.md](LAB.md) contains setup details.

## What each part does

| Part | Purpose |
|---|---|
| Physical computer | Runs the virtual machines. Fault experiments happen inside the target VM. |
| `zabbix-server` | Collects measurements, store them in a database and serve the web interface. |
| `linux-target` | Runs the monitored agent and HTTP service. This is where faults are introduced. |
| `noc-lab` storage pool | Registers the project `vms/` folder containing separate guest disks; it is not a VM. |
| `noc-lab` network | Connects the VMs and provides outbound access through NAT. |
| Browser | Displays Zabbix measurements, graphs and problems. |

The QEMU guest agent helps the virtualization tools communicate with Ubuntu. It is separate from Zabbix Agent 2, which provides monitoring data.

## From a measurement to a problem

1. An agent provides measurements such as CPU usage. HTTP checks separately test the web service.
2. An **item** describes one measurement Zabbix collects.
3. A **trigger** evaluates a condition, such as CPU usage staying above a chosen threshold.
4. A **problem event** records when that condition becomes true. Recovery records when it clears.
5. You investigate, repair the cause and verify that measurements return to normal.

A **template** groups reusable monitoring settings. A **dashboard** displays selected results. A successful ping proves network reachability, not that an application is healthy.

## Learning order

| Stage | Practical outcome |
|---|---|
| Build the environment | Two Linux VMs with working SSH, addressing, DNS and package access |
| Collect the first metric | A recent target measurement visible in Zabbix |
| Establish normal operation | Host, HTTP and CPU checks with sensible intervals and thresholds |
| Reproduce faults | Problem and recovery events for six tested scenarios |
| Share the result | Sanitized configuration exports, observed timings and short runbooks |

For every fault, record when it started, when Zabbix detected it, when service was restored and when recovery appeared. Polling intervals and trigger evaluation periods help explain the delay.

## Make it your own

- **CPU and RAM:** choose VM allocations in virt-manager; review the [baseline budget](LAB.md). Shut down existing guests before changing their persistent allocations.
- **Network:** choose a subnet that does not overlap your LAN or VPN. Keep DHCP reservations and guest MAC addresses consistent.
- **Initial guest settings:** review the [cloud-init template](../configs/cloud-init/user-data.example) if using the cloud-image method. It applies during initial setup, not every time the file is edited.
- **Monitoring:** choose items, polling intervals, thresholds and dashboard widgets in Zabbix.

Work in small steps: understand the purpose, choose a setting, apply it and inspect the result. The current learning path uses virt-manager and the Ubuntu installer. The optional creation script records an earlier cloud-image build; its settings differ from the manual setup and it must not be run over existing guests.
