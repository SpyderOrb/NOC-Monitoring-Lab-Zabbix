# NOC Lab Overview

A manually configured Zabbix 7.0 dashboard for the two-host lab. Data refresh and layout persistence after browser reload were operator-confirmed on October 5, 2026.

Create the dashboard under Dashboards. Add the following widgets with a 30-second refresh interval, then Save changes. For Item value widgets, select the host inside the Item selector; leave Override host empty. Use the latest value with default display options.

| Widget name | Type | Source or filter |
|---|---|---|
| Target agent availability | Item value | linux-target: Zabbix agent availability |
| Target CPU | Item value | linux-target: CPU utilization |
| Target available memory | Item value | linux-target: Available memory in % |
| Target root disk used | Item value | linux-target: FS [/]: Space: Used, in % |
| Current problems | Problems | Hosts Zabbix server and linux-target; Show Problems; other filters default |
| HTTP health | Web monitoring | Host linux-target; other filters default |

Place the four status/resource tiles across the top, with Problems and HTTP below. Widen the availability tile until its mapped state is fully visible. Keep timestamps visible to assess sample age. Widget refresh does not change item polling intervals.

Available memory is remaining headroom; disk used is occupied space. The default change arrow indicates direction, not trigger severity. An empty Problems widget means no matching unresolved events. HTTP Ok1 represents the single successful web scenario. The layout has been verified, but API export/import or restoration has not yet been tested.
