# 📡 NOC Monitoring Lab — Zabbix

A small monitoring lab built around one workflow: **detect a fault, investigate, restore service and verify recovery**.

Two Ubuntu virtual machines provide a practical environment for learning host, HTTP service and CPU monitoring with Zabbix.

> **In progress:** the Ubuntu guest baseline has been verified. Zabbix, the dashboard and fault/recovery exercises are not implemented yet. See [tested scope](docs/VALIDATION.md).

## How it works

The intended setup uses one VM as a monitoring server and the other as a target. Zabbix will collect measurements, evaluate alert conditions and show problem/recovery events in its web interface.

[![Lab design: a browser connects to the Zabbix server at 192.168.77.10, which monitors a Linux target at 192.168.77.20](docs/topology.png)](docs/topology.png)

*Design and guest baseline · Monitoring connections are planned · [Editable SVG](docs/topology.svg)*

| Component | Role |
|---|---|
| QEMU/KVM + libvirt | Run and manage the two VMs |
| Ubuntu Server 24.04 LTS | Guest operating systems |
| Zabbix 7.0 LTS | Planned monitoring server, agent and dashboard |
| Small HTTP service | Planned service to monitor and deliberately interrupt |

## Fault exercises

| Scenario | What the exercise will demonstrate |
|---|---|
| HTTP service stopped | Detect a service outage while the target remains reachable |
| Target VM shut down | Detect host unavailability and confirm recovery after boot |
| Bounded CPU load | Detect sustained resource pressure and its recovery |

These exercises are planned. The intended deliverables are a useful dashboard, measured detection/recovery times, reusable monitoring exports and short recovery runbooks. Initial notifications stay in the local dashboard.

## Explore

- **[Understand the lab](docs/GUIDE.md)** — components, monitoring concepts and learning order.
- **[Setup and file locations](docs/LAB.md)** — VM sizing, networking, Ubuntu image source, and what is installed on the host versus inside the project or guests.
- **[Validation](docs/VALIDATION.md)** — observed results and test limits.
- **Reusable baseline:** [network XML](configs/libvirt/noc-lab.xml), [cloud-init template](configs/cloud-init/user-data.example) and [optional guest creation script](scripts/create-guests.py).

VM images, backups, credentials and personal working notes stay outside Git. The repository contains documentation, reusable configuration and recorded evidence.
