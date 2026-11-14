// Fallbacks for the live demo (#17): offline replay from web/static/snapshot/ and the typed form when the
// model gateway fails. Loaded before app.js; app.js calls Fallback.api() for every route.
//
// Offline replay: switched on by the "Offline replay" toggle, by ?offline=1, or automatically when the server is
// unreachable or a route errors. It answers only what web/snapshot.py recorded; any other remark shows
// "offline: parsing needs the network". The key below mirrors check_key() in web/snapshot.py.
"use strict";

const Fallback = (function makeFallback() {
  const SNAPSHOT = "/static/snapshot/";
  const REQUEST_FIELDS = ["type", "part", "to_supplier", "from_supplier", "site", "at_supplier", "new_material",
                          "new_coating", "scope"];
  const FORM_FIELDS = ["type", "part", "to_supplier", "from_supplier", "site", "new_material", "new_coating"];
  const forced = new URLSearchParams(location.search).get("offline") === "1";
  const mode = { on: forced, why: forced ? "?offline=1" : "", manifest: null };

  function norm(text) { return String(text || "").split(/\s+/).filter(Boolean).join(" ").toLowerCase(); }

  function checkKey(body) {
    let asOf = body.as_of || "";
    const drop = [...(body.drop_rows || [])].sort().join(",");
    if (body.remark) return `remark|${norm(body.remark)}|${asOf}|${drop}`;
    if (body.scenario) return `scenario|${body.scenario}|${asOf}|${drop}`;
    const request = body.request || body.form || {};
    asOf = asOf || request.as_of || "";
    const values = REQUEST_FIELDS.map(function value(field) {
      return String(request[field] || (field === "scope" ? "series" : ""));
    });
    return `request|${values.join("|")}|${asOf}|${drop}`;
  }

  function keyFor(path, body) { return body ? checkKey(body) : `GET ${path}`; }

  async function manifest() {
    if (!mode.manifest) {
      const response = await fetch(`${SNAPSHOT}index.json`, { cache: "no-store" });
      if (!response.ok) throw new Error("no offline snapshot on this machine (run python -m web.snapshot)");
      mode.manifest = await response.json();
    }
    return mode.manifest;
  }

  async function replay(path, body) {
    const recorded = await manifest();
    const name = recorded.index[keyFor(path, body)];
    if (!name) {
      if (body && body.remark) throw new Error("offline: parsing needs the network (only the recorded demo remarks replay)");
      if (body && body.form) throw new Error("offline: this typed request was not recorded");
      throw new Error("offline: this was not recorded");
    }
    const response = await fetch(SNAPSHOT + name, { cache: "no-store" });
    const data = await response.json();
    data.labels = recorded.labels;
    if (body && body.speaker && data.card) data.card.request.speaker = body.speaker;
    return data;
  }

  function setOffline(on, why) {
    mode.on = on;
    mode.why = why || "";
    renderSwitch();
  }

  function parseFailure(data) {
    const error = new Error(data.error);
    error.parseFailed = true;
    error.payload = data;
    return error;
  }

  async function api(path, body) {
    if (mode.on) return replay(path, body);
    const options = body ? { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) } : {};
    let response = null;
    let data = null;
    try {
      response = await fetch(path, options);
      data = await response.json();
    } catch (networkError) {
      return goOffline(path, body, "server unreachable");
    }
    if (data && data.parse_failed) throw parseFailure(data);   // gateway down: typed form, never a fake
    if (!response.ok || data.error) {
      if (body && body.form) throw new Error(data.error || `HTTP ${response.status}`);  // a typing mistake
      return goOffline(path, body, `route error: ${data.error || response.status}`);
    }
    return data;
  }

  async function goOffline(path, body, why) {
    try {
      const data = await replay(path, body);
      setOffline(true, why);
      return data;
    } catch (replayError) {
      throw new Error(`${why}; ${replayError.message}`);
    }
  }

  // ---- the switch and the label -----------------------------------------------------------------------------

  function renderSwitch() {
    let badge = document.getElementById("offline-badge");
    if (!badge) {
      badge = document.createElement("div");
      badge.id = "offline-badge";
      badge.className = "offline-badge";
      document.body.append(badge);
    }
    badge.hidden = !mode.on;
    const when = mode.manifest ? ` · recorded ${mode.manifest.created_at}` : "";
    badge.textContent = `offline replay${when}`;
    badge.title = mode.why ? `Switched on: ${mode.why}` : "Answers come from web/static/snapshot/";
    const toggle = document.getElementById("offline-toggle");
    if (toggle) {
      toggle.textContent = mode.on ? "Offline replay: on" : "Offline replay: off";
      toggle.classList.toggle("on", mode.on);
    }
  }

  function mountSwitch() {
    const nav = document.querySelector(".topnav");
    if (nav && !document.getElementById("offline-toggle")) {
      const toggle = document.createElement("button");
      toggle.id = "offline-toggle";
      toggle.className = "link offline-toggle";
      toggle.title = "Answer from the recorded snapshot instead of the server";
      toggle.addEventListener("click", async function flip() {
        if (!mode.on) {
          try { await manifest(); } catch (error) { alert(error.message); return; }
        }
        setOffline(!mode.on, mode.on ? "" : "switched by hand");
      });
      nav.prepend(toggle);
    }
    if (mode.on) manifest().then(renderSwitch, renderSwitch);
    renderSwitch();
  }

  // ---- typed form when the parse fails ----------------------------------------------------------------------

  function hideForm() {
    const box = document.getElementById("parse-fallback");
    if (box) box.hidden = true;
  }

  function showForm(payload, submit) {
    let box = document.getElementById("parse-fallback");
    if (!box) {
      box = document.createElement("section");
      box.id = "parse-fallback";
      box.className = "parse-fallback";
      document.getElementById("status").after(box);
    }
    box.innerHTML = "";
    box.hidden = false;
    const form = payload.form || {};
    const labels = payload.labels || {};
    const head = document.createElement("div");
    head.className = "pf-head";
    head.innerHTML = "<b>The remark was not parsed.</b> ";
    head.append(`${payload.error} Nothing was guessed: check the typed form below. It is prefilled with the closest `
                + `demo request (“${payload.closest_remark}”, similarity ${payload.similarity}); edit any field.`);
    box.append(head);
    const grid = document.createElement("div");
    grid.className = "pf-grid";
    const inputs = {};
    const typeSelect = document.createElement("select");
    for (const type of payload.change_types || []) {
      const option = document.createElement("option");
      option.value = type;
      option.textContent = type;
      typeSelect.append(option);
    }
    typeSelect.value = form.type || "";
    inputs.type = typeSelect;
    for (const field of FORM_FIELDS.slice(1)) {
      const input = document.createElement("input");
      input.value = form[field] || "";
      input.placeholder = "id or name";
      inputs[field] = input;
    }
    const asOf = document.createElement("input");
    asOf.type = "date";
    asOf.value = form.as_of || "";
    inputs.as_of = asOf;
    for (const [field, input] of Object.entries(inputs)) {
      const cell = document.createElement("label");
      cell.className = "pf-field";
      const name = document.createElement("span");
      name.textContent = field.replace("_", " ");
      cell.append(name, input);
      if (labels[input.value]) {
        const hint = document.createElement("span");
        hint.className = "muted small";
        hint.textContent = labels[input.value];
        cell.append(hint);
      }
      grid.append(cell);
    }
    box.append(grid);
    const button = document.createElement("button");
    button.className = "primary";
    button.textContent = "Check typed form";
    button.addEventListener("click", function send() {
      const typed = { utterance: form.utterance };
      for (const [field, input] of Object.entries(inputs)) {
        if (input.value.trim()) typed[field] = input.value.trim();
      }
      submit(typed);
    });
    box.append(button);
    box.scrollIntoView({ behavior: "smooth", block: "center" });
  }

  document.addEventListener("DOMContentLoaded", mountSwitch);

  return { api: api, showForm: showForm, hideForm: hideForm, isOffline: function isOffline() { return mode.on; } };
})();
