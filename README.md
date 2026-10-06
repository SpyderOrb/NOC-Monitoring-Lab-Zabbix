# 📡 NOC Monitoring Lab — Zabbix

A hands-on lab for monitoring Linux hosts and investigating service failures.

Two Ubuntu VMs run Zabbix and a monitored target. I tested six fault scenarios, checked that alerts cleared after recovery, and recorded the results. This repository contains the configuration exports, screenshots, scripts and runbooks from those tests.

## The lab

[![A browser connects to the Zabbix server at 192.168.77.10, which monitors a Linux target at 192.168.77.20](docs/topology.png)](docs/topology.png)

*[Editable diagram](docs/topology.svg) · [Setup details](docs/LAB.md)*

| Component | Role |
|---|---|
| QEMU/KVM + libvirt | Runs the two Ubuntu Server 24.04 VMs |
| Zabbix 7.0.31 | Collects metrics, evaluates alerts and displays the dashboard |
| Zabbix Agent 2 | Provides CPU, memory, disk and queue data |
| Target Nginx | Serves an HTTP health page checked for status and content |
| Python queue simulator | Publishes JSON to test worker stalls, backlog and stale telemetry |

The six-widget dashboard shows target availability, CPU, memory, disk usage, current problems and HTTP health. [Dashboard setup](docs/DASHBOARD.md).

## Faults I tested

| Scenario | What the test showed |
|---|---|
| [Nginx stopped](runbooks/MON-01-http-service.md) | HTTP monitoring reported a problem and cleared it after restart. |
| [Target VM shut down](runbooks/MON-02-vm-outage.md) | HTTP and agent checks detected the outage and recovered after boot. |
| [HTTP 200 with incorrect content](runbooks/MON-04-http-content.md) | The page was reachable, but its health marker was wrong; the content check detected it. |
| [Bounded CPU load](runbooks/MON-03-cpu-load.md) | Sustained high CPU triggered a warning that cleared after load ended. |
| [Queue worker paused](runbooks/MON-05-queue-worker.md) | Worker liveness recovered first; the backlog alert cleared later, as the queue drained. |
| [Queue publisher stopped](runbooks/MON-06-queue-telemetry.md) | Monitoring detected an old timestamp even though the JSON file was still readable. |

Each scenario produced automatic problem and recovery events. [Validation](docs/VALIDATION.md) records the observed timings and limits; individual test results are not guaranteed response times.

## What I learned

An HTTP 200 response does not always mean a service is healthy. A readable metrics file can also contain old data. The queue tests helped separate these checks from worker liveness and the amount of work waiting to be processed.

One restart test produced an unexpected worker warning. With help from the AI agent, I changed the worker-age calculation to use timestamps from one JSON sample, then repeated the restart and worker-pause tests. The recorded restart retest showed no extra worker warning, while the real pause still triggered an alert. [Queue design and evidence](docs/QUEUE-DEMO.md).

## Read more

- [Understand the lab](docs/GUIDE.md) — components and how measurements become alerts.
- [Setup](docs/LAB.md) — VM sizing, networking and software locations.
- [Queue demo](docs/QUEUE-DEMO.md) — the simulator, custom metrics and alert conditions.
- [Validation](docs/VALIDATION.md) — results, screenshots and known limits.
- [Configuration exports](configs/zabbix/README.md) — the Linux template, queue template and target host. Offline checks passed; import into a fresh Zabbix instance has not been tested.
- [Project walkthrough](docs/PROJECT-STORY.md) — a short English explanation for an interview.

## How I worked

This was an AI-assisted learning project. I carried out the manual VM setup, guest configuration and fault tests. An AI coding agent helped me plan the work, troubleshoot issues, prepare scripts and documentation, and check the configuration exports. The results come from the recorded lab runs; untested areas are listed in Validation.

The queue is an educational simulator, not a production job system. Notifications stay in the local Zabbix dashboard. VM images, backups, credentials and personal working notes stay outside Git.
