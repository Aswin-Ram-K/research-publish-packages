/**
 * hash.ts — the single cryptographic entry point.
 *
 * Directive (docs/HASHING.md): "make it light and fast; standardise all complex
 * cryptographic work." Application code imports from here and never touches a
 * crypto library directly.
 *
 * Default is BLAKE3 when an implementation is available. Node's crypto has no
 * BLAKE3, so we fall back to BLAKE2b-512 — same interface, same call sites, and
 * swapping in a real BLAKE3 module is a one-line change with no ripple.
 */

import { createHash } from "node:crypto";

export type ContentHash = string;

export interface Hasher {
  readonly algorithm: string;
  /** Async by contract: the commit path must never block on a digest. */
  hash(bytes: Uint8Array): Promise<ContentHash>;
  hashConcat(parts: Uint8Array[]): Promise<ContentHash>;
  /** Explicit fast path for the sync case. Callers opt in knowingly. */
  hashSync(bytes: Uint8Array): ContentHash;
  /**
   * Content-addressed hashing, keyed on the caller's CONTENT IDENTITY
   * (scheme/locator/pin) rather than on the bytes. This is the cache that
   * matters: a resource hashed once is free thereafter, so a repeated task
   * pays for its resources exactly once.
   */
  hashContent(key: string, bytes: Uint8Array): Promise<ContentHash>;
  readonly cache: DigestCache;
}

export interface Verifier {
  verify(bytes: Uint8Array, expected: ContentHash): Promise<boolean>;
}

const enc = new TextEncoder();
export const utf8 = (s: string): Uint8Array => enc.encode(s);

/**
 * Digest cache. Content addressing means duplicate content is duplicate by
 * definition, so on a repeated task the hit rate is high. Keyed on the caller's
 * content identity, never on the bytes (hashing bytes to find a cache key would
 * defeat the purpose).
 */
export class DigestCache {
  #map = new Map<string, ContentHash>();
  #hits = 0;
  #misses = 0;

  get(key: string): ContentHash | undefined {
    const v = this.#map.get(key);
    if (v === undefined) this.#misses++;
    else this.#hits++;
    return v;
  }
  set(key: string, value: ContentHash): ContentHash {
    this.#map.set(key, value);
    return value;
  }
  get stats() {
    const total = this.#hits + this.#misses;
    return {
      size: this.#map.size,
      hits: this.#hits,
      misses: this.#misses,
      hitRate: total === 0 ? 0 : this.#hits / total,
    };
  }
}

class Blake2b512Hasher implements Hasher {
  readonly algorithm = "blake2b512";
  readonly #cache = new DigestCache();

  #digest(bytes: Uint8Array): ContentHash {
    return createHash("blake2b512").update(bytes).digest("hex");
  }

  hashSync(bytes: Uint8Array): ContentHash {
    return this.#digest(bytes);
  }

  async hash(bytes: Uint8Array): Promise<ContentHash> {
    return this.#digest(bytes);
  }

  /**
   * Hash by composition. Because resources are already content-addressed, a
   * state's digest is computed over existing digests plus small inline fields —
   * a state referencing a 200 MB artefact hashes as cheaply as an empty one.
   */
  async hashConcat(parts: Uint8Array[]): Promise<ContentHash> {
    const h = createHash("blake2b512");
    for (const p of parts) h.update(p);
    return h.digest("hex");
  }

  async hashContent(key: string, bytes: Uint8Array): Promise<ContentHash> {
    const cached = this.#cache.get(key);
    if (cached !== undefined) return cached;
    const digest = this.#digest(bytes);
    return this.#cache.set(key, digest);
  }

  get cache(): DigestCache {
    return this.#cache;
  }
}

export const hasher: Hasher = new Blake2b512Hasher();

/**
 * Stable cache key for a resource. Uses the caller's content identity, not the
 * bytes — hashing bytes to find a cache key would defeat the purpose.
 */
export const contentKey = (
  scheme: string,
  locator: string,
  pin: string,
): string => `${scheme}\u0000${locator}\u0000${pin}`;

/** Split a hash into path segments for on-disk fan-out (git-style). */
export const shard = (h: ContentHash): string => `${h.slice(0, 2)}/${h.slice(2)}`;

/* ------------------------------------------------------------------ */
/* Canonical form — docs/STATE.md §3                                   */
/* ------------------------------------------------------------------ */

/**
 * Deterministic serialisation for hashing.
 *
 * Rules: lexicographic key order (recursive) · no insignificant whitespace ·
 * absent !== null · no floats (a float in a hashed field is a cross-platform
 * hash divergence waiting to happen).
 *
 * `id`, `ts` and `epoch` are excluded by the caller (`VOLATILE` in
 * `src/state.ts`; `epoch` left the digest under D-058, because a stored workflow
 * position is a second source of truth that destroys dedup). `canonical()` itself
 * filters nothing — it serialises whatever it is handed, which is why the
 * exclusion lives with the envelope and not here.
 */
export function canonical(value: unknown): string {
  if (value === null) return "null";
  const t = typeof value;
  if (t === "number") {
    if (!Number.isInteger(value as number)) {
      throw new TypeError(
        `canonical(): float in identity-bearing field: ${String(value)}. ` +
          `Use an integer or a string (docs/STATE.md §3).`,
      );
    }
    return String(value);
  }
  if (t === "string") return JSON.stringify(value);
  if (t === "boolean") return value ? "true" : "false";
  if (Array.isArray(value)) {
    return `[${value.map(canonical).join(",")}]`;
  }
  if (t === "object") {
    const o = value as Record<string, unknown>;
    const keys = Object.keys(o)
      .filter((k) => o[k] !== undefined)
      .sort();
    return `{${keys.map((k) => `${JSON.stringify(k)}:${canonical(o[k])}`).join(",")}}`;
  }
  throw new TypeError(`canonical(): unsupported type ${t}`);
}
