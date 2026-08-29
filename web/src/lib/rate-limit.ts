/**
 * A fixed-window request counter, in process memory.
 *
 * This is scoped to what `make web` / `make web-build` actually run: a single
 * long-lived Node process (`next start`), not a serverless fleet. On a single
 * process, an in-memory map is a correct, sufficient limiter. It stops being
 * correct the moment this app runs as multiple instances behind a load
 * balancer or as serverless functions — each instance would count
 * independently, so the real limit becomes (this limit × instance count). If
 * this deployment ever moves to that shape, replace the `Map` below with a
 * shared store (Redis, or a Postgres table) keyed the same way; nothing else
 * about the call sites needs to change.
 */

interface Bucket {
  count: number;
  windowStart: number;
}

const buckets = new Map<string, Bucket>();

// A cap on the map itself: without one, an attacker who cycles through
// unique emails or spoofed IPs indefinitely would grow this unboundedly. The
// oldest bucket is evicted to make room, which is an acceptable trade against
// spending a persistent store on what is meant to be a lightweight, in-process
// backstop rather than the primary defence.
const MAX_TRACKED_KEYS = 10_000;

/**
 * Returns true if `key` has exceeded `limit` events within `windowMs`.
 *
 * Call this once per attempt, whether or not the attempt turns out to
 * succeed — checking after the fact would let a burst through before the
 * limiter ever saw it.
 */
export function isRateLimited(key: string, limit: number, windowMs: number): boolean {
  const now = Date.now();
  const existing = buckets.get(key);

  if (!existing || now - existing.windowStart > windowMs) {
    if (buckets.size >= MAX_TRACKED_KEYS && !existing) {
      const oldestKey = buckets.keys().next().value;
      if (oldestKey !== undefined) buckets.delete(oldestKey);
    }
    buckets.set(key, { count: 1, windowStart: now });
    return false;
  }

  existing.count += 1;
  return existing.count > limit;
}
