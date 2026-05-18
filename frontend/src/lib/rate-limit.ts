// Simple In-Memory Rate Limiter (Token Bucket)
// ACHTUNG: Funktioniert am besten in Single-Node Deployments (wie hier mit SQLite vorgesehen).
// Für Multi-Node / Vercel Edge wird in Produktion Redis empfohlen (z.B. Upstash).

const rateLimitCache = new Map<string, { count: number, resetTime: number }>();

interface RateLimitConfig {
  interval: number; // in milliseconds
  uniqueTokenPerInterval: number; // max requests
}

export function applyRateLimit(identifier: string, config: RateLimitConfig) {
  const now = Date.now();
  const limitInfo = rateLimitCache.get(identifier);

  if (!limitInfo) {
    rateLimitCache.set(identifier, {
      count: 1,
      resetTime: now + config.interval
    });
    return { success: true };
  }

  if (now > limitInfo.resetTime) {
    // Reset
    rateLimitCache.set(identifier, {
      count: 1,
      resetTime: now + config.interval
    });
    return { success: true };
  }

  if (limitInfo.count >= config.uniqueTokenPerInterval) {
    return { success: false }; // Rate limit exceeded
  }

  limitInfo.count += 1;
  return { success: true };
}
