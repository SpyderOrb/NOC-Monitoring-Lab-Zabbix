# MON-03 — Bounded CPU load and recovery

Purpose: verify sustained CPU pressure and automatic recovery on the disposable one-vCPU target.

## Configuration

Trigger: `min(/linux-target/system.cpu.util,5m)>{$CPU.UTIL.CRIT}`, effective threshold 90, Warning. The trigger depends on `Linux: Load average is too high`. Keep one load worker; adding workers changes the experiment and can activate the parent trigger.

## Procedure

1. Inside the target, check `hostname` and `nproc`; expect `linux-target` and 1. Confirm fresh low CPU and enabled/OK trigger in Zabbix. Keep clock synchronization suitable for timestamp comparisons.
2. Run in the target bash session, without sudo:

   ```bash
   date -u '+CPU START reference: %Y-%m-%d %H:%M:%S UTC'
   timeout --kill-after=5s 8m yes > /dev/null
   cpu_test_rc=$?
   date -u '+CPU STOP observed: %Y-%m-%d %H:%M:%S UTC'
   printf 'timeout exit code: %s\n' "$cpu_test_rc"
   ```

   One worker uses the guest CPU; output is discarded. Timeout stops it after 8m, with a 5s forced-stop fallback. Code 124 is expected on normal timeout expiry. Ctrl+C stops early; record the STOP timestamp separately if needed.
3. Observe CPU utilization under Monitoring → Latest data and the Warning in Monitoring → Problems. Every sample in the five-minute window must exceed 90 for the expression to become true, and the dependency must permit event generation.
4. Let the bounded command finish. Verify a fresh lower CPU sample and automatic RESOLVED event in Problems → History. Record action references, problem/recovery timestamps and exit code. If no event appears, preserve the result and inspect sampling/dependency state before any repeat.

## Recorded result

On October 5, CPU reached 100%, the timeout returned 124 and the CPU event automatically resolved after 2m. The problem appeared 6m39s after the pre-load reference; recovery appeared 22s after the post-load timestamp. These are approximate observations: separate interactive commands introduced unmeasured start/end gaps. Post-recovery Latest data confirmed 0.2338% CPU, checked 5s earlier; the graph also shows return to baseline.

[Evidence and timeline](../docs/evidence/2026-10-05-cpu-load.txt)

[Recovery graph](../docs/evidence/2026-10-05-cpu-recovery-graph.png)
