# Zabbix monitoring export

`linux-target.yaml` is an unchanged host export from the running Zabbix7.0.31 lab, captured October5,2026. It was inspected for scope and secrets; no credentials or personal filesystem paths are present. Import into a fresh instance has **not** been tested. This baseline export predates the custom queue template linkage; it does not include that extension.

## Included

- Host `linux-target`, group `Linux servers`, agent interface192.168.77.20.
- Link to `Linux by Zabbix agent` (template contents are not embedded).
- Web scenario `HTTP health`, step `Health page`, interval30s, timeout5s, required body `NOC-LAB-HTTP-OK`, required status200.
- Average-severity HTTP trigger `last(/linux-target/web.test.fail[HTTP health])>0`, with component=http and scope=availability tags.

## Prerequisites and restoration procedure

Use a separate Zabbix7.0 environment with the `Linux by Zabbix agent` template installed. The source system used effective macros `{$AGENT.TIMEOUT}=3m`, `{$CPU.UTIL.CRIT}=90` and `{$LOAD_AVG_PER_CPU.MAX.WARN}=1.5`; these are inherited and not stored in the host export. Exact template export remains pending.

Prepare the target Agent2 to accept passive checks from the monitoring server, and Nginx to serve `/health.txt` with the marker above. The export does not install guest software or configure the agent. Adapt both the interface address and HTTP URL when using another lab subnet. If renaming the host, also update its trigger expression.

In Data collection → Hosts → Import, select the YAML. For a fresh destination, enable Create new for the included entities and template linkage; keep Delete missing disabled. Review import rules before executing. Existing-host updates are outside the tested scope. Do not reimport into the working lab simply to check the file.

After import, verify fresh CPU/memory/root-filesystem metrics, agent availability, HTTP failed step0/code200, and the enabled HTTP trigger. Recreate the global dashboard using [the dashboard guide](../../docs/DASHBOARD.md). The export contains neither that dashboard nor measurement/event history. It also does not preserve the manually disabled discovered interface-speed item: if the target reports unknown nominal speed (-1), apply the documented host-only exclusion again after discovery.

[Official host export/import documentation](https://www.zabbix.com/documentation/7.0/en/manual/xml_export_import/hosts)
