/**
 * Unit tests for webui/js/time-utils.js
 */

import { describe, it, expect, vi, afterEach } from "vitest";
import {
  toLocalTime,
  toUTCISOString,
  getCurrentUTCISOString,
  formatDateTime,
  getUserTimezone,
  formatDuration,
} from "../time-utils.js";

// ---------------------------------------------------------------------------
// toLocalTime
// ---------------------------------------------------------------------------

describe("toLocalTime", () => {
  it("returns empty string for falsy input", () => {
    expect(toLocalTime("")).toBe("");
    expect(toLocalTime(null)).toBe("");
    expect(toLocalTime(undefined)).toBe("");
  });

  it("returns a non-empty string for a valid UTC ISO string", () => {
    const result = toLocalTime("2024-06-15T12:00:00Z");
    expect(typeof result).toBe("string");
    expect(result.length).toBeGreaterThan(0);
  });
});

// ---------------------------------------------------------------------------
// toUTCISOString
// ---------------------------------------------------------------------------

describe("toUTCISOString", () => {
  it("returns empty string for falsy input", () => {
    expect(toUTCISOString(null)).toBe("");
    expect(toUTCISOString(undefined)).toBe("");
  });

  it("returns an ISO string for a valid Date", () => {
    const date = new Date("2024-01-01T00:00:00Z");
    const result = toUTCISOString(date);
    expect(result).toBe("2024-01-01T00:00:00.000Z");
  });
});

// ---------------------------------------------------------------------------
// getCurrentUTCISOString
// ---------------------------------------------------------------------------

describe("getCurrentUTCISOString", () => {
  it("returns a valid ISO string for the current time", () => {
    const result = getCurrentUTCISOString();
    expect(typeof result).toBe("string");
    // Should end in Z (UTC)
    expect(result.endsWith("Z")).toBe(true);
    // Should parse to a valid date close to now
    const parsed = new Date(result);
    expect(isNaN(parsed.getTime())).toBe(false);
    const diff = Math.abs(Date.now() - parsed.getTime());
    expect(diff).toBeLessThan(5000); // within 5 seconds
  });
});

// ---------------------------------------------------------------------------
// formatDateTime
// ---------------------------------------------------------------------------

describe("formatDateTime", () => {
  it("returns empty string for falsy input", () => {
    expect(formatDateTime("")).toBe("");
    expect(formatDateTime(null)).toBe("");
  });

  it("returns a formatted string for 'full' format (default)", () => {
    const result = formatDateTime("2024-06-15T12:00:00Z");
    expect(typeof result).toBe("string");
    expect(result.length).toBeGreaterThan(0);
  });

  it("handles 'date' format", () => {
    const result = formatDateTime("2024-06-15T12:00:00Z", "date");
    expect(typeof result).toBe("string");
    expect(result.length).toBeGreaterThan(0);
  });

  it("handles 'time' format", () => {
    const result = formatDateTime("2024-06-15T12:00:00Z", "time");
    expect(typeof result).toBe("string");
    expect(result.length).toBeGreaterThan(0);
  });

  it("handles 'short' format", () => {
    const result = formatDateTime("2024-06-15T12:00:00Z", "short");
    expect(typeof result).toBe("string");
    expect(result.length).toBeGreaterThan(0);
  });

  it("falls back to 'full' for unknown format", () => {
    const full = formatDateTime("2024-06-15T12:00:00Z", "full");
    const unknown = formatDateTime("2024-06-15T12:00:00Z", "nonexistent");
    expect(full).toBe(unknown);
  });
});

// ---------------------------------------------------------------------------
// getUserTimezone
// ---------------------------------------------------------------------------

describe("getUserTimezone", () => {
  it("returns a non-empty string", () => {
    const tz = getUserTimezone();
    expect(typeof tz).toBe("string");
    expect(tz.length).toBeGreaterThan(0);
  });
});

// ---------------------------------------------------------------------------
// formatDuration
// ---------------------------------------------------------------------------

describe("formatDuration", () => {
  it("returns '0s' for null/undefined/negative values", () => {
    expect(formatDuration(null)).toBe("0s");
    expect(formatDuration(undefined)).toBe("0s");
    expect(formatDuration(-1)).toBe("0s");
  });

  it("returns '0s' for zero milliseconds", () => {
    expect(formatDuration(0)).toBe("0s");
  });

  it("formats sub-minute durations as seconds", () => {
    expect(formatDuration(5000)).toBe("5s");
    expect(formatDuration(59000)).toBe("59s");
  });

  it("formats exactly one minute", () => {
    expect(formatDuration(60000)).toBe("1m0s");
  });

  it("formats minutes and seconds", () => {
    expect(formatDuration(90000)).toBe("1m30s");
    expect(formatDuration(150000)).toBe("2m30s");
  });

  it("rounds to nearest second to avoid '1m60s'", () => {
    // 119,999ms should round to 120s = 2m0s
    expect(formatDuration(119999)).toBe("2m0s");
  });

  it("handles large durations", () => {
    // 3600000ms = 60 minutes
    expect(formatDuration(3600000)).toBe("60m0s");
  });
});
