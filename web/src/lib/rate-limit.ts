/**
 * A sliding-window request counter.
 *
 * Backed by Upstash Redis when `UPSTASH_REDIS_REST_URL` /
 * `UPSTASH_REDIS_REST_TOKEN` are set (Vercel's Upstash marketplace
 * integration sets both automatically), which is what makes this correct
 * across a serverless fleet — every instance checks the same shared counter.
 * Falls back to an in-process `Map` when they aren't, so `next dev` and a
 * plain `next start` still work with no Redis account at all; that fallback
 * is *only* correct for a single long-lived process (see `isRateLimitedInMemory`)
 * and was this module's entire implementation before Upstash was added.
 *
 * Either backend is reached through the same `isRateLimited`, so nothing at
 * a call site needs to know or care which one is actually in effect.
 */

import { Ratelimit } from '@upstash/ratelimit';
import { Redis } from '@upstash/redis';

const upstashUrl = process.env.UPSTASH_REDIS_REST_URL;
const upstashToken = process.env.UPSTASH_REDIS_REST_TOKEN;

// One Ratelimit instance per distinct (limit, window) pair a caller asks
// for -- the constructor bakes both into the instance, so a fresh (limit,
// windowMs) combination gets its own, cached the same way the underlying
// Redis client is (Upstash's own client is stateless per-request over REST,
// so reusing it across calls is safe and avoids re-creating it every time).
const limiters = new Map<string, Ratelimit>();

function getUpstashLimiter(limit: number, windowMs: number): Ratelimit | null {
  if (!upstashUrl || !upstashToken) return null;

  const cacheKey = `${limit}:${windowMs}`;
  const cached = limiters.get(cacheKey);
  if (cached) return cached;

  const redis = new Redis({ url: upstashUrl, token: upstashToken });
  const limiter = new Ratelimit({
    redis,
    // Upstash's Duration type wants a unit string ("s"/"m"/"h"/"d"), not a
    // raw millisecond count -- expressing every window in whole seconds
    // sidesteps having to map an arbitrary `windowMs` onto whichever unit
    // divides it evenly.
    limiter: Ratelimit.slidingWindow(limit, `${Math.max(1, Math.round(windowMs / 1000))} s`),
    // Distinguishes this app's keys from anything else sharing the same
    // Redis database (Upstash's free tier is commonly shared across small
    // projects on one account).
    prefix: 'denguesentinel',
  });
  limiters.set(cacheKey, limiter);
  return limiter;
}

// --- in-memory fallback, used only when Upstash isn't configured ----------

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

function isRateLimitedInMemory(key: string, limit: number, windowMs: number): boolean {
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

/**
 * Returns true if `key` has exceeded `limit` events within `windowMs`.
 *
 * Call this once per attempt, whether or not the attempt turns out to
 * succeed — checking after the fact would let a burst through before the
 * limiter ever saw it. Async regardless of which backend answers, since the
 * Upstash path is a real network call; the in-memory path resolves
 * immediately but keeps the same signature so a call site never has to know
 * which one it's talking to.
 */
export async function isRateLimited(key: string, limit: number, windowMs: number): Promise<boolean> {
  const limiter = getUpstashLimiter(limit, windowMs);
  if (limiter) {
    const { success } = await limiter.limit(key);
    return !success;
  }
  return isRateLimitedInMemory(key, limit, windowMs);
}
