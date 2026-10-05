# MON-01 — HTTP service failure and recovery

Purpose: verify that stopping target Nginx produces an HTTP problem and that restarting it produces automatic recovery. Run only against the disposable `linux-target` guest, never the monitoring server.

## Monitoring configuration

- Endpoint: `http://192.168.77.20/health.txt`, body contains `NOC-LAB-HTTP-OK`.
- Web scenario: `HTTP health`; step: `Health page`; interval: 30s; attempts: 1; timeout: 5s; required status: 200.
- Trigger: `linux-target: HTTP health check failed`, severity Average.
- Expression: `last(/linux-target/web.test.fail[HTTP health])>0`.
- Recovery: expression becomes false; single problem generation. Tags: `component=http`, `scope=availability`.

## Procedure

1. Confirm synchronized clocks on both guests, healthy fresh HTTP values (`web.test.fail=0`, status 200), and an enabled/OK trigger. Open Monitoring → Problems for the target.
2. In the target SSH session, verify `hostname` returns `linux-target`. Prime sudo with `sudo -v`.
3. Stop the target service and record UTC command completion:

   ```bash
   sudo systemctl stop nginx && date -u '+STOP completed: %Y-%m-%d %H:%M:%S UTC'
   ```

4. Observe failed step 1 and the named HTTP problem. Record its event timestamp. Restore immediately after capture or within two minutes even if no problem appears; do not wait for further instructions.

   ```bash
   sudo systemctl start nginx && date -u '+START completed: %Y-%m-%d %H:%M:%S UTC'
   systemctl is-active nginx
   ```

5. Verify fresh failed step 0/status 200 and automatic RESOLVED status. Use Problems → History to capture problem and recovery times. Do not manually close the event.

If start fails, inspect `systemctl status nginx --no-pager -l` and `sudo nginx -t` inside the target before further tests. Preserve the error output.

## Interpretation and recorded result

A failed connection may leave an older HTTP 200 value visible; check Last check and failed-step status. Likewise, the last-error item can retain an earlier error after recovery.

The 2026-10-05 trial measured approximately 24s from stop completion to problem and 7s from start completion to recovery. The recorded event lasted 60s. These are single-trial observations, limited by action timestamp precision and clock accuracy, not guaranteed detection bounds. The trigger does not independently detect missing monitoring data.

[Evidence and UTC timeline](../docs/evidence/2026-10-05-http-fault.txt) · [Event screenshot](../docs/evidence/2026-10-05-http-resolved.png)

## Additional content-check exercise

The same scenario can detect a wrong body even when HTTP status remains200. On `linux-target` only, verify `hostname`, then replace `/var/www/html/health.txt` with `NOC-LAB-HTTP-FAIL` using `printf '%s\n' 'NOC-LAB-HTTP-FAIL' | sudo tee /var/www/html/health.txt`. From the monitoring server, request `http://192.168.77.20/health.txt` and verify200 plus the incorrect marker. Capture failed step1 and the required-pattern error.

Restore `NOC-LAB-HTTP-OK` with the same target-side command after observing the problem, or within two minutes. Confirm the target hostname before restoration: writing the same path on the monitoring server does not repair the target. Verify automatic recovery, without restarting Nginx or manually closing the event.

The October5 content trial passed, with a7m recorded event due to delayed correct-host restoration. Action references were entered after writes, so no precise latency is claimed. [Evidence](../docs/evidence/2026-10-05-http-content.txt).
