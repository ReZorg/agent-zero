import { createStore } from "/js/AlpineStore.js";
import * as API from "/js/api.js";

/**
 * Store for the agent team-members editor section.
 *
 * Loads the team_agents list for the currently selected agent profile,
 * allows adding / removing members, and saves changes via the subagents API.
 */
const model = {
  // The agent profile name whose team is being edited
  profileName: "",

  // List of team member objects: { profile, name, description }
  members: [],

  // Available agent profiles for the member-profile dropdown
  availableProfiles: [],

  loading: false,
  saving: false,
  error: null,
  successMessage: null,

  // ── Lifecycle ────────────────────────────────────────────────────────────────

  init() {},

  async onOpen(profileName) {
    if (!profileName) return;
    this.profileName = profileName;
    this.error = null;
    this.successMessage = null;
    await Promise.all([this.loadTeamAgents(), this.loadAvailableProfiles()]);
  },

  onClose() {
    this.profileName = "";
    this.members = [];
    this.error = null;
    this.successMessage = null;
  },

  // ── Data loading ─────────────────────────────────────────────────────────────

  async loadTeamAgents() {
    if (!this.profileName) return;
    this.loading = true;
    try {
      const res = await API.callJsonApi("subagents", {
        action: "load",
        name: this.profileName,
      });
      if (res?.ok) {
        this.members = (res.data?.team_agents || []).map((m) => ({ ...m }));
      } else {
        this.error = res?.error || "Failed to load agent data";
      }
    } catch (e) {
      this.error = e.message || "Failed to load agent data";
    } finally {
      this.loading = false;
    }
  },

  async loadAvailableProfiles() {
    try {
      const res = await API.callJsonApi("subagents", { action: "list" });
      if (res?.ok) {
        this.availableProfiles = (res.data || []).map((a) => ({
          key: a.name,
          label: a.title || a.name,
        }));
      }
    } catch (_) {
      this.availableProfiles = [];
    }
  },

  // ── Editing ───────────────────────────────────────────────────────────────────

  addMember() {
    this.members.push({ profile: "", name: "", description: "" });
  },

  removeMember(index) {
    this.members.splice(index, 1);
  },

  // ── Saving ────────────────────────────────────────────────────────────────────

  async saveTeamAgents() {
    if (!this.profileName) return;
    this.saving = true;
    this.error = null;
    this.successMessage = null;
    try {
      // Load the full agent first to avoid clobbering other fields
      const loadRes = await API.callJsonApi("subagents", {
        action: "load",
        name: this.profileName,
      });
      if (!loadRes?.ok) throw new Error(loadRes?.error || "Failed to reload agent data");

      const agentData = { ...loadRes.data };
      agentData.team_agents = this.members.filter((m) => m.profile.trim() !== "");

      const saveRes = await API.callJsonApi("subagents", {
        action: "save",
        name: this.profileName,
        data: agentData,
      });
      if (saveRes?.ok) {
        this.members = (saveRes.data?.team_agents || []).map((m) => ({ ...m }));
        this.successMessage = "Team members saved.";
        setTimeout(() => {
          this.successMessage = null;
        }, 3000);
      } else {
        throw new Error(saveRes?.error || "Failed to save agent data");
      }
    } catch (e) {
      this.error = e.message || "Save failed";
    } finally {
      this.saving = false;
    }
  },
};

export const store = createStore("agentTeamEditor", model);
