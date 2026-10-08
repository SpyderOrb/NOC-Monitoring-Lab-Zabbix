# From installed guests to monitoring

Start after the [manual guest build](LAB.md#manual-build-sequence): both VMs have working SSH, reserved addresses, package updates and synchronized clocks. This guide records the lab's configuration choices and connects installation to the exported monitoring configuration. The complete procedure has not been repeated on a fresh instance; [validation](VALIDATION.md) identifies what was observed.

## Connections and software

| Initiator | Destination | Purpose |
|---|---|---|
| Host browser | `192.168.77.10:8080/TCP` | Zabbix frontend |
| Zabbix server | `192.168.77.20:10050/TCP` | Passive Agent 2 checks, including queue JSON |
| Zabbix server | `192.168.77.20:80/TCP` | HTTP health scenario |
| Server and frontend processes | Server loopback `127.0.0.1:5432/TCP` | Local PostgreSQL database |

The target does not send active checks to port 10051 in this configuration. SSH is a separate administration path. These are application flows, not a complete host-firewall ruleset; guest DHCP, DNS and package access are covered by the network setup. This private lab uses HTTP and unencrypted passive-agent connections; TLS has not been configured or tested.

## Monitoring server

Inside **zabbix-server**, use the [official installation selector](https://www.zabbix.com/download?zabbix=7.0&os_distribution=ubuntu&os_version=24.04&components=server_frontend_agent&db=pgsql&ws=nginx): Zabbix **7.0 LTS**, Ubuntu **24.04**, server/frontend/agent, **PostgreSQL** and **Nginx**. The recorded lab used Zabbix 7.0.31, PostgreSQL 16 and PHP 8.3 FPM; current 7.0 packages may have a newer patch version. Record the version you actually install.

1. Add the official Zabbix repository and install the selected server/frontend packages, PostgreSQL, Nginx and PHP PostgreSQL support inside the guest.
2. Create the `zabbix` PostgreSQL role with a private password and an empty UTF-8 database owned by that role. Import the packaged Zabbix schema **once into that empty database** with errors treated as failures. Do not reimport it into an existing lab database.
3. Edit the existing `/etc/zabbix/zabbix_server.conf` parameters: `DBHost=127.0.0.1`, `DBPort=5432`, `DBName=zabbix`, `DBUser=zabbix` and your private `DBPassword`. Preserve the packaged file and keep credentials outside Git.
4. In the existing `/etc/zabbix/nginx.conf` server block, use `listen 8080;` and `server_name 192.168.77.10;`. Retain the packaged PHP and document-root settings. Run `sudo nginx -t` before applying the change.
5. Enable/start PostgreSQL, Zabbix server, Nginx and PHP FPM as directed by the package guide. Verify active services and a successful Zabbix database connection. Open `http://192.168.77.10:8080/` from the host browser, complete the frontend wizard using the same local database, and replace the default administrator password.

The browser reaching the login page proves frontend access. Server self-monitoring additionally requires its local agent and the `Zabbix server` host to produce fresh values; an empty Problems page alone does not establish this.

## Target Agent 2

Inside **linux-target**, install `zabbix-agent2` from the same official 7.0 Ubuntu repository. Edit the existing active entries in `/etc/zabbix/zabbix_agent2.conf`:

```ini
Server=192.168.77.10
Hostname=linux-target
```

Keep one active occurrence of each setting. Comment out the packaged `ServerActive` entry and any active-check entry in included configuration files for this passive-only setup. `Server` is the allowed polling source; the hostname identifies the guest. Preserve other package settings. See the [Agent 2 parameter reference](https://www.zabbix.com/documentation/7.0/en/manual/appendix/config/zabbix_agent2).

Check and apply inside the target, stopping on a validation error:

```bash
sudo zabbix_agent2 -T -c /etc/zabbix/zabbix_agent2.conf
sudo systemctl enable zabbix-agent2
sudo systemctl restart zabbix-agent2
systemctl is-active zabbix-agent2
```

Configuration validation and an active service are preliminary checks. Acceptance requires a recent value collected by the server under **Monitoring → Latest data → linux-target**, with a successful agent interface and fresh CPU, memory and root-filesystem items.

## Target HTTP endpoint

Inside **linux-target**, install Nginx and create the health marker in its default document root:

```bash
sudo apt install nginx
printf '%s\n' 'NOC-LAB-HTTP-OK' | sudo tee /var/www/html/health.txt
sudo nginx -t
sudo systemctl enable --now nginx
```

Inside **zabbix-server**, check the actual target path:

```bash
wget --timeout=5 --tries=1 -S -O - http://192.168.77.20/health.txt
```

Expect HTTP 200 and `NOC-LAB-HTTP-OK`. Keep the server's frontend on port 8080 separate from the target's port-80 health page.

## Queue and frontend configuration

Deploy the simulator inside linux-target using the [queue installation steps](QUEUE-DEMO.md#persistent-guest-deployment). Verify JSON readability as the `zabbix` user before expecting the file-content item to work.

On a separate fresh monitoring instance, follow the [export guide](../configs/zabbix/README.md#optional-import-procedure--not-yet-tested): Linux template, queue template, then target host. Review addresses and import rules first. This import path remains untested; the original lab was configured manually in the frontend. Do not reimport over the working lab merely to check an export.

For manual frontend configuration, create host `linux-target` in `Linux servers`, agent interface `192.168.77.20:10050`, and link **Linux by Zabbix agent** (the passive template). Add the queue template using its [documented items and expressions](QUEUE-DEMO.md#verified-zabbix-collection). Configure the HTTP scenario and trigger from [MON-01](../runbooks/MON-01-http-service.md#monitoring-configuration); the [host export](../configs/zabbix/linux-target.yaml) contains the exact recorded settings. Recreate the global dashboard with the [widget guide](DASHBOARD.md).

After collection begins, check a small baseline: fresh CPU/memory/root-disk values, HTTP failed step `0` with status `200`, advancing queue timestamps with depth near zero, and no unexplained problems. Only then use the fault runbooks. This proposed acceptance batch is not a new restoration result.

## Virtual interface speed exception

The observed virtio interface reported `-1` in `/sys/class/net/enp1s0/speed`; the Linux template multiplied it into a negative speed, which its unsigned item rejected. On the affected target only, open **Data collection → Hosts → linux-target → Items**, find **Interface enp1s0: Speed**, and disable that individual discovered item. First confirm the actual interface name and raw value on a rebuilt guest; do not apply the exception to every host or change the shared template.

The original operator reported this exclusion. It does not repair the virtual driver's speed reporting or supply a measured link speed. Speed-based checks remain outside scope; unrelated traffic/error items stay enabled. The exclusion is not restored by the host YAML and may need reapplying after discovery. [Recorded observation](VALIDATION.md#initial-target-collection--2026-10-04).
