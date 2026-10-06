var m = JSON.parse(value);
if (m.worker_last_seen === 0) return 0;
return Math.max(0, m.updated_at - m.worker_last_seen);
