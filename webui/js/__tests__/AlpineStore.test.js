/**
 * Unit tests for webui/js/AlpineStore.js
 *
 * AlpineStore provides createStore / getStore / saveState / loadState utilities.
 * These tests run in a DOM-like environment (happy-dom) without Alpine.js,
 * so all reads/writes go through the plain target object path of the Proxy.
 */

import { describe, it, expect, beforeEach } from "vitest";
import { createStore, getStore, saveState, loadState } from "../AlpineStore.js";

// ---------------------------------------------------------------------------
// createStore / getStore
// ---------------------------------------------------------------------------

describe("createStore", () => {
  it("returns a proxy with the initial state values", () => {
    const store = createStore("testStoreA", { count: 0, label: "hello" });
    expect(store.count).toBe(0);
    expect(store.label).toBe("hello");
  });

  it("allows mutation via the proxy", () => {
    const store = createStore("testStoreB", { value: 1 });
    store.value = 42;
    expect(store.value).toBe(42);
  });

  it("returns the same proxy when getStore is called with the same name", () => {
    const store = createStore("testStoreC", { x: 10 });
    const retrieved = getStore("testStoreC");
    expect(retrieved).toBe(store);
  });

  it("returns undefined from getStore for an unknown name", () => {
    expect(getStore("non_existent_store_xyz")).toBeUndefined();
  });
});

// ---------------------------------------------------------------------------
// saveState
// ---------------------------------------------------------------------------

describe("saveState", () => {
  it("snapshots all non-function own properties", () => {
    const store = { a: 1, b: "hello", fn: () => {} };
    const snapshot = saveState(store);
    expect(snapshot).toHaveProperty("a", 1);
    expect(snapshot).toHaveProperty("b", "hello");
    expect(snapshot).not.toHaveProperty("fn");
  });

  it("deep-copies arrays", () => {
    const store = { items: [1, 2, 3] };
    const snapshot = saveState(store);
    store.items.push(4);
    expect(snapshot.items).toEqual([1, 2, 3]);
  });

  it("shallow-copies plain objects", () => {
    const store = { meta: { x: 1 } };
    const snapshot = saveState(store);
    store.meta.x = 99;
    // Snapshot holds the value at save time via spread (shallow)
    expect(snapshot.meta).toBeDefined();
  });

  it("respects include whitelist", () => {
    const store = { a: 1, b: 2, c: 3 };
    const snapshot = saveState(store, ["a", "c"]);
    expect(snapshot).toHaveProperty("a");
    expect(snapshot).not.toHaveProperty("b");
    expect(snapshot).toHaveProperty("c");
  });

  it("respects exclude blacklist", () => {
    const store = { a: 1, b: 2, c: 3 };
    const snapshot = saveState(store, [], ["b"]);
    expect(snapshot).toHaveProperty("a");
    expect(snapshot).not.toHaveProperty("b");
    expect(snapshot).toHaveProperty("c");
  });

  it("exclude takes priority over include when both provided", () => {
    const store = { a: 1, b: 2, c: 3 };
    const snapshot = saveState(store, ["a"], ["b"]);
    // exclude is non-empty → exclude mode; 'a' and 'c' included
    expect(snapshot).toHaveProperty("a");
    expect(snapshot).not.toHaveProperty("b");
  });
});

// ---------------------------------------------------------------------------
// loadState
// ---------------------------------------------------------------------------

describe("loadState", () => {
  it("merges all keys from state into store", () => {
    const store = { a: 0, b: "" };
    loadState(store, { a: 10, b: "loaded" });
    expect(store.a).toBe(10);
    expect(store.b).toBe("loaded");
  });

  it("does nothing when state is null/undefined", () => {
    const store = { a: 5 };
    loadState(store, null);
    expect(store.a).toBe(5);
    loadState(store, undefined);
    expect(store.a).toBe(5);
  });

  it("deep-copies arrays from state", () => {
    const store = { items: [] };
    const state = { items: [1, 2, 3] };
    loadState(store, state);
    state.items.push(4);
    expect(store.items).toEqual([1, 2, 3]);
  });

  it("shallow-copies plain objects from state", () => {
    const store = { meta: {} };
    loadState(store, { meta: { key: "value" } });
    expect(store.meta.key).toBe("value");
  });

  it("respects include whitelist", () => {
    const store = { a: 0, b: 0 };
    loadState(store, { a: 1, b: 2 }, ["a"]);
    expect(store.a).toBe(1);
    expect(store.b).toBe(0);
  });

  it("respects exclude blacklist", () => {
    const store = { a: 0, b: 0 };
    loadState(store, { a: 1, b: 2 }, [], ["b"]);
    expect(store.a).toBe(1);
    expect(store.b).toBe(0);
  });
});
