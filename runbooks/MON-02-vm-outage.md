# MON-02 — Target VM outage and recovery

Purpose: verify passive-agent and HTTP problem/recovery events during a graceful shutdown of the disposable target. Keep the monitoring server running.

## Configuration

Agent trigger: `max(/linux-target/zabbix[host,agent,available],{$AGENT.TIMEOUT})=0`, severity Average. Verified effective timeout: `3m`. HTTP monitoring uses the [MON-01 configuration](MON-01-http-service.md).

## Procedure

1. Verify the target agent trigger is enabled/OK and HTTP is healthy. Check clock synchronization for timestamp comparisons. Open Monitoring → Problems for `linux-target`. In virt-manager, locate its start control before shutdown.
2. In the target terminal, verify `hostname` returns `linux-target`, then run:

   ```bash
   sudo -v
   date -u '+SHUTDOWN requested: %Y-%m-%d %H:%M:%S UTC' && sudo systemctl poweroff
   ```

3. Expect SSH disconnection and the target to show shut off in virt-manager. Record HTTP and agent problem timestamps. Start the target after the agent event, or after six minutes at most if it does not appear; preserve the failed result for diagnosis.
4. In the physical-host terminal, record a reference immediately before clicking the target start button in virt-manager:

   ```bash
   date -u '+START reference: %Y-%m-%d %H:%M:%S UTC'
   ```

5. After boot, reconnect to the target and run `systemctl is-active nginx zabbix-agent2`. Expect two active lines. In Monitoring → Problems → History, verify both availability events resolve automatically and record recovery times. Do not manually close test events.

## Observed result and limits

The October 5 trial detected HTTP failure in 22s and agent unavailability in 3m44s from the shutdown request. HTTP and agent recovery appeared 51s and 1m46s after the pre-start reference. Both services were active after boot. A separate recent-restart warning was still visible.

These are single-trial approximate observations, including shutdown/boot and polling delays. Start-click timing and cross-machine clock offsets limit precision. Agent unavailability is not independent proof that a VM is powered off; agent or network failure can produce the same event.

[Evidence and UTC timeline](../docs/evidence/2026-10-05-vm-outage.txt)
