"""Offline simulator/preprocessing regressions; no lab services are contacted.

Requires Python 3.9+ on Linux and Node.js. Node executes the Zabbix function body;
these tests do not replace validation with Zabbix's Duktape engine or an import.
"""

from contextlib import redirect_stdout
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import textwrap
import time
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'scripts/noc-queue.py'
AGE_SCRIPT = ROOT / 'configs/zabbix/queue-worker-age.js'
RECORDED = ROOT / 'configs/zabbix/recorded/noc-queue-template-2026-10-06.yaml'
EPOCH = 1_700_000_000
NODE_RUNNER = """
const fs = require('node:fs');
const age = new Function('value', fs.readFileSync(process.argv[1], 'utf8'));
const samples = JSON.parse(fs.readFileSync(0, 'utf8'));
console.log(JSON.stringify(samples.map(sample => {
    try { return {value: age(JSON.stringify(sample))}; }
    catch (error) { return {error: String(error)}; }
})));
"""


def evaluate(samples):
    result = subprocess.run(['node', '-e', NODE_RUNNER, str(AGE_SCRIPT)],
                            input=json.dumps(samples), text=True, capture_output=True,
                            check=True, timeout=10)
    return json.loads(result.stdout)


class Clock:
    """Advance the actual main loop without waiting out monitoring thresholds."""

    def __init__(self, state, epoch, pause):
        self.state, self.epoch, self.pause = state, epoch, pause
        self.elapsed = 0.0
        self.samples = []
        self.set_pause()

    def monotonic(self):
        return self.elapsed

    def time(self):
        return self.epoch + self.elapsed

    def set_pause(self):
        flag = self.state / 'pause-worker'
        if self.pause(self.elapsed):
            flag.touch()
        else:
            flag.unlink(missing_ok=True)

    def sleep(self, seconds):
        sample = json.loads((self.state / 'metrics.json').read_text())
        if not self.samples or sample != self.samples[-1]:
            self.samples.append(sample)
        self.elapsed = round(self.elapsed + seconds, 6)
        self.set_pause()


def simulate(state, duration=45, *, epoch=EPOCH, pause=lambda elapsed: False):
    spec = importlib.util.spec_from_file_location('noc_queue', SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    clock = Clock(state, epoch, pause)
    argv = [str(SCRIPT), '--state-dir', str(state), '--duration', str(duration)]
    with patch.object(sys, 'argv', argv), patch.object(module, 'time', clock), \
            patch.object(module.signal, 'signal'), redirect_stdout(io.StringIO()):
        module.main()
    return clock.samples


class QueueTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='noc-queue-test-')
        self.addCleanup(self.temp.cleanup)
        self.state = Path(self.temp.name)

    def ages(self, samples):
        results = evaluate(samples)
        for result in results:
            self.assertNotIn('error', result)
        return [result['value'] for result in results]

    def test_normal_start_has_no_false_stall(self):
        samples = simulate(self.state)
        self.assertEqual(samples[0]['worker_last_seen'], 0)
        self.assertTrue(all(s['started_at'] == EPOCH for s in samples))
        self.assertTrue(all(age <= 1 for age in self.ages(samples)))
        self.assertGreater(samples[-1]['processed_total'], 0)

    def test_initial_pause_ages_then_recovers_and_drains(self):
        samples = simulate(self.state, 85, pause=lambda elapsed: elapsed < 40)
        ages = self.ages(samples)
        paused = [(s, age) for s, age in zip(samples, ages) if s['worker_paused']]
        self.assertTrue(all(s['worker_last_seen'] == 0 for s, _ in paused))
        self.assertGreater(max(age for _, age in paused), 30)
        self.assertGreater(max(s['queue_depth'] for s, _ in paused), 10)
        self.assertEqual(ages[-1], 0)
        self.assertEqual(samples[-1]['queue_depth'], 0)
        self.assertGreater(samples[-1]['worker_last_seen'], EPOCH)

    def test_pause_after_healthy_work_uses_last_heartbeat(self):
        samples = simulate(self.state, 90, pause=lambda elapsed: 8 <= elapsed < 48)
        ages = self.ages(samples)
        paused = [(s, age) for s, age in zip(samples, ages) if s['worker_paused']]
        self.assertEqual(len({s['worker_last_seen'] for s, _ in paused}), 1)
        self.assertGreater(paused[0][0]['worker_last_seen'], EPOCH)
        self.assertGreater(max(age for _, age in paused), 30)
        self.assertEqual(ages[-1], 0)
        self.assertEqual(samples[-1]['queue_depth'], 0)

    def test_restart_uses_new_process_reference(self):
        previous = simulate(self.state, pause=lambda elapsed: True)
        self.assertGreater(self.ages(previous)[-1], 30)
        for paused in (False, True):
            with self.subTest(paused=paused):
                samples = simulate(self.state, epoch=EPOCH + 1000,
                                   pause=lambda elapsed: paused)
                ages = self.ages(samples)
                self.assertEqual(samples[0]['started_at'], EPOCH + 1000)
                self.assertEqual(samples[0]['produced_total'], 0)
                self.assertEqual(samples[0]['worker_last_seen'], 0)
                self.assertEqual(ages[0], 0)
                if paused:
                    self.assertGreater(ages[-1], 30)
                else:
                    self.assertTrue(all(age <= 1 for age in ages))

    def test_timestamp_validation_and_old_samples(self):
        cases = [
            ({'updated_at': 140, 'worker_last_seen': 100}, 40),
            ({'updated_at': 90, 'worker_last_seen': 100}, 0),
            ({'updated_at': 100, 'worker_last_seen': 0, 'started_at': 100}, 0),
            ({'updated_at': 131, 'worker_last_seen': 0, 'started_at': 100}, 31),
        ]
        self.assertEqual(self.ages([sample for sample, _ in cases]),
                         [expected for _, expected in cases])
        invalid = [{'updated_at': 140, 'worker_last_seen': 0}]
        for key in ('updated_at', 'worker_last_seen', 'started_at'):
            for value in (None, '100', True, -1, 1.5):
                sample = {'updated_at': 140, 'worker_last_seen': 0, 'started_at': 100}
                sample[key] = value
                invalid.append(sample)
        for result in evaluate(invalid):
            self.assertIn('error', result)
            self.assertIn('queue timestamp', result['error'])

    def test_template_preserves_recorded_settings_and_matches_source(self):
        original = RECORDED.read_bytes()
        self.assertEqual(hashlib.sha256(original).hexdigest(),
                         '03ec42a545b5502794c1355a780f0e7b40b0a2c47f67b4a34d1db31e9c3c7a36')
        original = original.decode()
        blocks = re.findall(r'                - \|\n((?: {18}[^\n]*\n|\n)+)', original)
        self.assertEqual(len(blocks), 1)
        revised = original.replace(blocks[0], textwrap.indent(AGE_SCRIPT.read_text(), ' ' * 18), 1)
        self.assertEqual((ROOT / 'configs/zabbix/noc-queue-template.yaml').read_text(), revised)

    def test_real_process_lock_and_graceful_stop(self):
        command = [sys.executable, str(SCRIPT), '--state-dir', str(self.state), '--duration', '10']
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        try:
            deadline = time.monotonic() + 5
            metrics = self.state / 'metrics.json'
            while not metrics.exists() and time.monotonic() < deadline:
                if process.poll() is not None:
                    self.fail('Simulator exited before publishing telemetry')
                time.sleep(0.05)
            self.assertTrue(metrics.exists(), 'No telemetry within five seconds')
            sample = json.loads(metrics.read_text())
            self.assertGreater(sample['started_at'], 0)
            second = subprocess.run(command, capture_output=True, text=True, timeout=5)
            self.assertEqual(second.returncode, 1)
            self.assertIn('Another queue instance', second.stderr)
            process.terminate()
            stdout, stderr = process.communicate(timeout=5)
            self.assertEqual(process.returncode, 0, stderr)
            self.assertIn('Queue stopped', stdout)
            self.assertTrue(metrics.exists(), 'Last sample must survive a publisher stop')
            self.assertFalse((self.state / 'metrics.json.tmp').exists())
            restarted = subprocess.run(command[:-1] + ['1'], capture_output=True, text=True, timeout=5)
            self.assertEqual(restarted.returncode, 0, restarted.stderr)
        finally:
            if process.poll() is None:
                process.kill()
            process.communicate()


if __name__ == '__main__':
    unittest.main()
