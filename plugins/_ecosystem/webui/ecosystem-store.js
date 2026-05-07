import { createStore } from "/js/AlpineStore.js";
import * as api from "/js/api.js";
import { openModal } from "/js/modals.js";
import {
  toastFrontendSuccess,
  toastFrontendError,
} from "/components/notifications/notification-store.js";

const ECOSYSTEM_API = "plugins/_ecosystem/ecosystem";

// Label mapping for filter chips
const TYPE_LABELS = {
  product: "Products",
  integration: "Integrations",
  template: "Templates",
  install: "Install & Setup",
  benchmark: "Benchmarks",
  example: "Examples",
};

// Material Symbols icon per action type
const ACTION_ICONS = {
  open_url: "open_in_new",
  copy_text: "content_copy",
  open_plugin_hub: "store",
  open_settings: "settings",
};

const model = {
  // ── State ─────────────────────────────────────────────
  catalog: [],
  loading: false,
  error: "",

  // active filter chip key: "all" | entry.type
  filter: "all",

  // tracks which copy action is in the "just copied" state
  // format: "<entry.id>:<action.label>"
  copiedKey: "",
  _copiedTimer: null,

  // ── Lifecycle ─────────────────────────────────────────

  async onOpen() {
    if (this.catalog.length === 0) {
      await this.fetchCatalog();
    }
  },

  cleanup() {
    this.filter = "all";
    this.error = "";
  },

  // ── Data ──────────────────────────────────────────────

  async fetchCatalog() {
    this.loading = true;
    this.error = "";
    try {
      const data = await api.callJsonApi(ECOSYSTEM_API, { action: "get_catalog" });
      if (!data.success) {
        throw new Error(data.error || "Failed to load ecosystem catalog");
      }
      this.catalog = Array.isArray(data.catalog) ? data.catalog : [];
    } catch (e) {
      const message = e instanceof Error ? e.message : String(e);
      this.error = message;
      void toastFrontendError(message, "Ecosystem");
    } finally {
      this.loading = false;
    }
  },

  // ── Computed ──────────────────────────────────────────

  get filterOptions() {
    const options = [{ key: "all", label: "All", count: this.catalog.length }];
    const seen = new Map();
    for (const entry of this.catalog) {
      seen.set(entry.type, (seen.get(entry.type) || 0) + 1);
    }
    for (const [type, count] of seen.entries()) {
      options.push({
        key: type,
        label: TYPE_LABELS[type] || (type.charAt(0).toUpperCase() + type.slice(1)),
        count,
      });
    }
    return options;
  },

  get filteredCatalog() {
    if (this.filter === "all") return this.catalog;
    return this.catalog.filter((entry) => entry.type === this.filter);
  },

  // ── UI helpers ────────────────────────────────────────

  getActionIcon(actionType) {
    return ACTION_ICONS[actionType] || "arrow_forward";
  },

  isCopied(entry, action) {
    return this.copiedKey === `${entry.id}:${action.label}`;
  },

  // ── Action routing ────────────────────────────────────

  async handleAction(action, entry) {
    const type = action.type || "";

    switch (type) {
      case "open_url": {
        window.open(action.url, "_blank", "noopener,noreferrer");
        break;
      }

      case "copy_text": {
        try {
          await navigator.clipboard.writeText(action.text);
          const key = `${entry.id}:${action.label}`;
          this.copiedKey = key;
          clearTimeout(this._copiedTimer);
          this._copiedTimer = setTimeout(() => {
            if (this.copiedKey === key) this.copiedKey = "";
          }, 2000);
          void toastFrontendSuccess("Copied to clipboard", "Ecosystem");
        } catch (_e) {
          void toastFrontendError("Failed to copy to clipboard", "Ecosystem");
        }
        break;
      }

      case "open_plugin_hub": {
        try {
          const { store: pluginListStore } = await import(
            "/components/plugins/list/pluginListStore.js"
          );
          await pluginListStore.open?.("pluginHub");
        } catch (e) {
          const message = e instanceof Error ? e.message : String(e);
          void toastFrontendError(message, "Ecosystem");
        }
        break;
      }

      case "open_settings": {
        openModal("settings/settings.html");
        if (action.tab) {
          setTimeout(() => {
            globalThis.Alpine?.store?.("settings")?.enterTab?.(action.tab);
          }, 80);
        }
        break;
      }

      default:
        console.warn("[ecosystemStore] unknown action type:", type);
    }
  },
};

const store = createStore("ecosystemStore", model);
export { store };
