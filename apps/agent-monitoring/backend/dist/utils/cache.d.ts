/**
 * Simple in-memory cache for frequently accessed data
 */
declare class SimpleCache {
    private cache;
    /**
     * Get cached value or null if expired/missing
     */
    get<T>(key: string): T | null;
    /**
     * Set cached value with TTL in milliseconds
     */
    set<T>(key: string, value: T, ttlMs?: number): void;
    /**
     * Clear cache entry
     */
    delete(key: string): void;
    /**
     * Clear all cache
     */
    clear(): void;
    /**
     * Clean expired entries
     */
    clean(): void;
}
export declare const cache: SimpleCache;
export {};
//# sourceMappingURL=cache.d.ts.map