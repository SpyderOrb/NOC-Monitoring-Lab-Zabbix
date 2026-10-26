var m = JSON.parse(value);

function timestamp(name) {
    var n = m[name];
    if (typeof n !== 'number' || !isFinite(n) || n < 0 || Math.floor(n) !== n) {
        throw 'Missing or invalid queue timestamp: ' + name;
    }
    return n;
}

var reference = timestamp('worker_last_seen');
// Before the first heartbeat, measure how long this process has been waiting.
if (reference === 0) reference = timestamp('started_at');
return Math.max(0, timestamp('updated_at') - reference);
