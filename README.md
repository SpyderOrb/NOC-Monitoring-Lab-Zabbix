# NOC Monitoring Lab — Zabbix

A hands-on lab for detecting service outages and resource problems, investigating alerts and confirming recovery.

The initial design uses a Zabbix server and a separate Linux target with a small web service. Three exercises cover a stopped web service, an unavailable host and sustained CPU load inside the target guest.

## Scope

- Host, HTTP service and resource monitoring.
- A concise dashboard with problem and recovery events.
- Trigger thresholds and delays that distinguish brief fluctuations from persistent failures.
- Repeatable fault exercises with observed detection timings and recovery instructions.

## Build

See [Lab design and build steps](docs/LAB.md) and [verified results](docs/VALIDATION.md). The virtualization host and lab network are prepared. The two Linux guests, Zabbix deployment and fault exercises are still pending.
