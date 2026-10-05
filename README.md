# 📡 NOC Monitoring Lab — Zabbix

A small monitoring lab built around one workflow: **detect a fault, investigate, restore service and verify recovery**.

Two Ubuntu virtual machines provide a practical environment for learning host, HTTP service and CPU monitoring with Zabbix.

> **In progress:** Zabbix 7.0.31 collects live CPU, memory and root-filesystem metrics from two Ubuntu VMs. All three fault exercises demonstrated automatic problem and recovery events in one trial each. The six-widget dashboard is verified; the target host export is captured and reviewed, with restoration testing still pending. See [tested scope and known limitations](docs/VALIDATION.md).

## How it works

One VM runs the monitoring server and the other is the target. Zabbix collects host measurements through Agent 2. HTTP service, VM shutdown and CPU load exercises have demonstrated automatic problem and recovery events in the web interface.

[![Lab design: a browser connects to the Zabbix server at 192.168.77.10, which monitors a Linux target at 192.168.77.20](docs/topology.png)](docs/topology.png)

*Lab design · CPU and memory collection verified on both guests · [Editable SVG](docs/topology.svg)*

| Component | Role |
|---|---|
| QEMU/KVM + libvirt | Run and manage the two VMs |
| Ubuntu Server 24.04 LTS | Guest operating systems |
| Zabbix 7.0 LTS | Server and target monitoring with a verified overview dashboard |
| Target Nginx service | HTTP status/content monitoring and tested stop/recovery |

## Fault exercises

| Scenario | Scope and result |
|---|---|
| HTTP service stopped | Passed: detected failure and automatic recovery; [runbook](runbooks/MON-01-http-service.md) |
| Target VM shut down | Passed: agent and HTTP problems automatically resolved after boot; [runbook](runbooks/MON-02-vm-outage.md) |
| HTTP 200 with incorrect content | Passed: required-body check detected failure and automatic recovery; [evidence](docs/evidence/2026-10-05-http-content.txt) |
| Bounded CPU load | Passed: 100% CPU observed, warning and automatic recovery; [runbook](runbooks/MON-03-cpu-load.md) |

The [target host export](configs/zabbix/README.md) includes the HTTP scenario and trigger; restoration into a fresh instance remains untested. Initial notifications stay in the local dashboard.

## Explore

- **[Understand the lab](docs/GUIDE.md)** — components, monitoring concepts and learning order.
- **[Setup and file locations](docs/LAB.md)** — VM sizing, networking, Ubuntu image source, and what is installed on the host versus inside the project or guests.
- **[Dashboard setup](docs/DASHBOARD.md)** — the verified six-widget overview.
- **[Application queue demo](docs/QUEUE-DEMO.md)** — bounded producer/worker simulator and verified JSON collection; custom alerting remains in progress.
- **[Validation](docs/VALIDATION.md)** — observed results and test limits.
- **Historical cloud-image examples:** [network XML](configs/libvirt/noc-lab.xml), [cloud-init template](configs/cloud-init/user-data.example) and [optional guest creation script](scripts/create-guests.py).

VM images, backups, credentials and personal working notes stay outside Git. The repository contains documentation, reusable configuration and recorded evidence.
