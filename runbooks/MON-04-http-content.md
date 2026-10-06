# MON-04 — HTTP 200 with incorrect content

Purpose: check application content even when the web server responds successfully. Run only on the disposable `linux-target` guest. This uses the same HTTP scenario and trigger as [MON-01](MON-01-http-service.md), but Nginx stays running.

## Monitoring configuration

The `HTTP health` scenario checks `http://192.168.77.20/health.txt` every 30s, with one attempt and a 5s timeout. Its `Health page` step requires both HTTP status `200` and the text `NOC-LAB-HTTP-OK`.

The Average trigger `last(/linux-target/web.test.fail[HTTP health])>0` reports a failed step and clears automatically when that step succeeds again.

## Procedure

1. Confirm healthy fresh HTTP values: failed step `0`, response code `200`, trigger OK. Verify `hostname` returns `linux-target` in the session where you change the file.
2. On **linux-target**, replace only the health marker:

   ```bash
   printf '%s
' 'NOC-LAB-HTTP-FAIL' | sudo tee /var/www/html/health.txt
   ```

3. From **zabbix-server**, request the target page and inspect the status and body:

   ```bash
   wget --timeout=5 --tries=1 -S -O - http://192.168.77.20/health.txt
   ```

   Expect HTTP 200 with the wrong marker. In Zabbix, expect failed step `1`, a required-pattern error and the HTTP problem. Check sample timestamps, since old status values may still be visible.
4. On **linux-target**, restore after capturing the problem, or within two minutes even if no problem appears:

   ```bash
   hostname
   printf '%s
' 'NOC-LAB-HTTP-OK' | sudo tee /var/www/html/health.txt
   ```

5. Repeat the server-side request. Expect the correct marker, fresh failed step `0`/status `200`, and automatic RESOLVED status. No Nginx restart or manual event closure is needed.

## What the recorded trial showed

On October 5, the server-side request returned HTTP 200 with the wrong marker while Zabbix reported a failed required-text check. The problem opened at 19:29:01 UTC and automatically resolved at 19:36:01 UTC, lasting seven minutes.

An initial restoration wrote the file on the monitoring server instead of the target. It did not repair the target endpoint and delayed recovery. The correct target-side write was confirmed later. This is why the procedure explicitly identifies the execution host.

The trial confirms content-failure detection and automatic recovery. Exact detection/recovery delays cannot be calculated from the separately entered action references. A fresh post-recovery HTTP/failed-step sample was not captured; corrected target content and automatic event recovery were confirmed.

[Evidence and timing limits](../docs/evidence/2026-10-05-http-content.txt) · [Resolved event](../docs/evidence/2026-10-05-http-content-resolved.png)
