# 📡 NOC Monitoring Lab — Zabbix

A small monitoring lab built around one workflow: **detect a fault, investigate, restore service and verify recovery**.

Two Ubuntu virtual machines provide a practical environment for learning host, HTTP service and application monitoring with Zabbix.

> **Verified scope:** Zabbix 7.0.31 collects host metrics from two Ubuntu VMs, checks HTTP status/content and monitors a simulated application queue. Six fault scenarios demonstrated automatic problem and recovery events, with observed timings and a six-widget dashboard. Configuration exports passed offline checks; import into a fresh Zabbix instance is untested and deferred. See [validation and limits](docs/VALIDATION.md).

## How it works

One VM runs the monitoring server and the other is the target. Zabbix collects host measurements through Agent 2 and checks an HTTP health page. A bounded Python queue simulator demonstrates how to distinguish stalled processing, accumulated backlog and stale telemetry.

[![Lab design: a browser connects to the Zabbix server at 192.168.77.10, which monitors a Linux target at 192.168.77.20](docs/topology.png)](docs/topology.png)

*Lab design · CPU and memory collection verified on both guests · [Editable SVG](docs/topology.svg)*

| Component | Role |
|---|---|
| QEMU/KVM + libvirt | Run and manage the two VMs |
| Ubuntu Server 24.04 LTS | Guest operating systems |
| Zabbix 7.0 LTS | Server and target monitoring with a verified overview dashboard |
| Target Nginx service | HTTP status/content monitoring and tested stop/recovery |
| Python queue simulator | JSON telemetry, dependent items and worker/backlog/freshness alerts |

## Fault exercises

| Scenario | Scope and result |
|---|---|
| HTTP service stopped | Passed: detected failure and automatic recovery; [runbook](runbooks/MON-01-http-service.md) |
| Target VM shut down | Passed: agent and HTTP problems automatically resolved after boot; [runbook](runbooks/MON-02-vm-outage.md) |
| HTTP 200 with incorrect content | Passed: required-body check detected failure and automatic recovery; [evidence](docs/evidence/2026-10-05-http-content.txt) |
| Bounded CPU load | Passed: 100% CPU observed, warning and automatic recovery; [runbook](runbooks/MON-03-cpu-load.md) |
| Queue worker paused | Passed: worker and backlog warnings automatically resolved; corrected worker trigger also passed a short regression; [runbook](runbooks/MON-05-queue-worker.md) |
| Queue telemetry publisher stopped | Passed: stale-file alert resolved; corrected restart regression showed no extra worker warning; [runbook](runbooks/MON-06-queue-telemetry.md) |

The [configuration exports](configs/zabbix/README.md) include the installed Linux template, custom queue template and target host with its HTTP scenario. They capture monitoring configuration; VM disks, installed software and measurement/event history are outside their scope. Fresh-instance import is deferred. Notifications stay in the local dashboard.

## Explore

- **[Understand the lab](docs/GUIDE.md)** — components, monitoring concepts and learning order.
- **[Setup and file locations](docs/LAB.md)** — VM sizing, networking, Ubuntu image source, and what is installed on the host versus inside the project or guests.
- **[Dashboard setup](docs/DASHBOARD.md)** — the verified six-widget overview.
- **[Application queue demo](docs/QUEUE-DEMO.md)** — bounded producer/worker simulator, dependent metrics, verified alerts and restart-noise correction.
- **[Validation](docs/VALIDATION.md)** — observed results and test limits.
- **Historical cloud-image examples:** [network XML](configs/libvirt/noc-lab.xml), [cloud-init template](configs/cloud-init/user-data.example) and [optional guest creation script](scripts/create-guests.py).

VM images, backups, credentials and personal working notes stay outside Git. The repository contains documentation, reusable configuration and recorded evidence.
