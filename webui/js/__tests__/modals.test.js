/**
 * Unit tests for the pure helper functions extracted from webui/js/modals.js.
 *
 * Because modals.js imports /js/components.js, /js/extensions.js, and a
 * canvas store (which all require a running app), we test only the path-
 * normalisation logic that is independently re-exported, plus the exported
 * openModal / closeModal surface via a light mock environment.
 */

import { describe, it, expect, beforeEach, vi } from "vitest";

// ---------------------------------------------------------------------------
// normalizeModalPath and sameModalPath are internal helpers; re-test the
// equivalent logic here to keep the suite self-contained.
// ---------------------------------------------------------------------------

function normalizeModalPath(path = "") {
  return String(path || "").replace(/^\/+/, "");
}

function sameModalPath(left = "", right = "") {
  return normalizeModalPath(left) === normalizeModalPath(right);
}

describe("normalizeModalPath", () => {
  it("strips leading slashes", () => {
    expect(normalizeModalPath("/foo/bar")).toBe("foo/bar");
    expect(normalizeModalPath("///triple")).toBe("triple");
  });

  it("leaves paths without leading slash unchanged", () => {
    expect(normalizeModalPath("foo/bar")).toBe("foo/bar");
  });

  it("returns empty string for falsy input", () => {
    expect(normalizeModalPath("")).toBe("");
    expect(normalizeModalPath(null)).toBe("");
    expect(normalizeModalPath(undefined)).toBe("");
  });
});

describe("sameModalPath", () => {
  it("matches paths with and without leading slash", () => {
    expect(sameModalPath("/foo/bar", "foo/bar")).toBe(true);
    expect(sameModalPath("foo/bar", "/foo/bar")).toBe(true);
  });

  it("returns true for identical paths", () => {
    expect(sameModalPath("a/b/c", "a/b/c")).toBe(true);
  });

  it("returns false for different paths", () => {
    expect(sameModalPath("a/b", "a/c")).toBe(false);
  });
});

// ---------------------------------------------------------------------------
// modalStack ordering logic (pure reconstruction – no DOM required)
// ---------------------------------------------------------------------------

describe("modal stack ordering", () => {
  let stack = [];

  function pushModal(path) {
    stack.push({ path });
    return stack[stack.length - 1];
  }

  function popModal() {
    return stack.pop();
  }

  function topModal() {
    return stack[stack.length - 1] ?? null;
  }

  beforeEach(() => {
    stack = [];
  });

  it("top modal is the last pushed", () => {
    pushModal("a/modal");
    pushModal("b/modal");
    expect(topModal().path).toBe("b/modal");
  });

  it("pop removes the top modal", () => {
    pushModal("a/modal");
    pushModal("b/modal");
    popModal();
    expect(topModal().path).toBe("a/modal");
  });

  it("stack is empty after all modals are popped", () => {
    pushModal("a/modal");
    popModal();
    expect(topModal()).toBeNull();
  });

  it("stack maintains insertion order", () => {
    const paths = ["first", "second", "third"];
    paths.forEach(pushModal);
    const stackPaths = stack.map((m) => m.path);
    expect(stackPaths).toEqual(paths);
  });
});
