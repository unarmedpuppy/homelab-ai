"use strict";
/**
 * Simple in-memory cache for frequently accessed data
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.cache = void 0;
class SimpleCache {
    cache = new Map();
    /**
     * Get cached value or null if expired/missing
     */
    get(key) {
        const entry = this.cache.get(key);
        if (!entry) {
            return null;
        }
        const now = Date.now();
        if (now - entry.timestamp > entry.ttl) {
            this.cache.delete(key);
            return null;
        }
        return entry.data;
    }
    /**
     * Set cached value with TTL in milliseconds
     */
    set(key, value, ttlMs = 5000) {
        this.cache.set(key, {
            data: value,
            timestamp: Date.now(),
            ttl: ttlMs
        });
    }
    /**
     * Clear cache entry
     */
    delete(key) {
        this.cache.delete(key);
    }
    /**
     * Clear all cache
     */
    clear() {
        this.cache.clear();
    }
    /**
     * Clean expired entries
     */
    clean() {
        const now = Date.now();
        for (const [key, entry] of this.cache.entries()) {
            if (now - entry.timestamp > entry.ttl) {
                this.cache.delete(key);
            }
        }
    }
}
exports.cache = new SimpleCache();
// Clean cache every minute
if (typeof setInterval !== 'undefined') {
    setInterval(() => {
        exports.cache.clean();
    }, 60000);
}
//# sourceMappingURL=cache.js.map