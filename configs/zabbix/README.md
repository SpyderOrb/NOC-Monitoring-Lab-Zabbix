# Zabbix configuration exports

The Linux and host YAML files were exported from the working Zabbix 7.0.31 lab on October 6, 2026. The current queue template is an **October 26 source revision**, based on that export, which fixes age calculation before the first worker heartbeat. It passes offline regressions but has not been deployed or tested in Zabbix. **Import into a fresh Zabbix instance remains untested and deferred.** These files are configuration artifacts, not VM or database backups.

## Included files

| File | Contents |
|---|---|
| [linux-template.yaml](linux-template.yaml) | Installed official `Linux by Zabbix agent`, vendor revision 7.0-4: 43 regular items, three discovery rules, macros, prototypes and template graphs/dashboards. |
| [noc-queue-template.yaml](noc-queue-template.yaml) | Revised queue template: one passive Text master, four unsigned dependent items and three triggers. Only worker-age preprocessing differs from the recorded export. Deploy the updated simulator first; see the [upgrade sequence](../../docs/QUEUE-DEMO.md#startup-fix-and-upgrade-order). |
| [recorded/noc-queue-template-2026-10-06.yaml](recorded/noc-queue-template-2026-10-06.yaml) | Unchanged operator export associated with the October 6 fault/recovery evidence. Retains the initial-pause limitation. |
| [linux-target.yaml](linux-target.yaml) | Host/group, passive interface `192.168.77.20`, links to both templates, HTTP health scenario and its Average-severity trigger. |
| [queue-worker-age.js](queue-worker-age.js) | Readable source matching the JavaScript embedded in the queue template. It computes worker age from one JSON snapshot. |

The host and recorded queue copies match the operator exports byte for byte. The Linux template copy only trims trailing whitespace and parses identically. The regression suite verifies the recorded queue file's SHA-256 and ensures that the revised template changes only its embedded JavaScript, which matches `queue-worker-age.js`. No credentials or personal filesystem paths were found.

Verified settings include agent timeout `3m`, CPU threshold `90`, per-CPU load threshold `1.5`; queue master polling `10s`, history `1d`, trends disabled; HTTP interval `30s`, timeout `5s`, required status `200` and body `NOC-LAB-HTTP-OK`. See [queue expressions and observed behavior](../../docs/QUEUE-DEMO.md).

## Optional import procedure — not yet tested

Use a separate Zabbix 7.0 instance with its own database. The monitoring server and target software must already be installed; YAML does not install Ubuntu, Zabbix, Agent 2, Nginx or the queue service. Follow the [monitoring setup guide](../../docs/MONITORING.md) for the guest-side prerequisites.

Prepare the target Agent 2 allowlist for passive checks from that server. Deploy the [current queue simulator/service](../../docs/QUEUE-DEMO.md), confirm JSON includes `started_at`, check readability and synchronize clocks. Nginx must serve `/health.txt` with the expected marker. Adjust the exported interface address and HTTP URL for a different subnet; a host rename also requires updating its trigger expression.

1. In **Data collection → Templates → Import**, import `linux-template.yaml`.
2. Import `noc-queue-template.yaml` through the same template page.
3. In **Data collection → Hosts → Import**, import `linux-target.yaml`.

Review Create new/Update rules for the destination and keep **Delete missing** disabled. Existing-host updates have not been tested. Do not reimport into the working lab merely to validate these files.

Check the expected template links, enabled items/triggers, fresh CPU/memory/root-filesystem samples, agent availability, HTTP failed step `0`/code `200`, and fresh queue JSON/worker age. These are proposed acceptance checks, not completed restoration results. [Official template](https://www.zabbix.com/documentation/7.0/en/manual/xml_export_import/templates) and [host export/import documentation](https://www.zabbix.com/documentation/7.0/en/manual/xml_export_import/hosts).

## What these files do not restore

- VM disks, guest packages, network settings or agent/service configuration.
- Database users, measurement history and past problem/recovery events.
- The global **NOC Lab Overview** dashboard; recreate it using the [dashboard guide](../../docs/DASHBOARD.md). Official template dashboards are included in the Linux template.
- The manually disabled discovered interface-speed item. If the virtual target reports nominal speed `-1`, reapply the [host-only exclusion](../../docs/MONITORING.md#virtual-interface-speed-exception) after discovery.

Offline checks do not replace Zabbix server-schema validation or an actual import. [Recorded verification and limits](../../docs/VALIDATION.md).
