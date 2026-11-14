// Change Check demo page. Talks only to the JSON routes of web/server.py; no core code runs in the browser.
"use strict";

const TODAY = "2026-11-14";
const RULE_CHANGE_REMARK = "Can we switch BR-220 from anodising to trivalent conversion coating?";
const NO_RULE_REMARK = "Let's move the BR-220 final inspection to the new CMM next week.";
const NO_RULE_REQUEST = { type: "EquipmentChange", part: "BR-220" };
const EPISTEMIC_TITLE = {
  CONSTRAINT: "Constraint: a rule or requirement that must hold",
  DECISION: "Decision: something a person or board decided",
  EVIDENCE: "Evidence: a recorded fact or measurement",
  PLAN: "Plan: a proposal or promise, not yet a fact",
  QUESTION: "Question: open, needs an answer from its owner",
};

const VERDICT_TEXT = {
  blockers_found: ["Blockers found", "Do not proceed as proposed. Each blocker below cites the documents it rests on."],
  needs_info: ["Needs information", "No blocker, but open questions have a named owner."],
  no_blockers_found: ["No blockers found", "Checked, nothing fired — not an approval. The change goes through standard change control; a person decides."],
  not_covered: ["Not covered: a person decides", "No rule covers this change. It goes to a person with the facts below."],
};
const SEVERITY_TEXT = { blocker: "Blocker", warning: "Warning", question: "Question", info: "Info" };

const state = { labels: {}, people: {}, scenarios: [], lastRequest: null, lastResponse: null, table: null,
                names: { parts: {}, people: {}, change_types: {} } };

// Decision-table deciders (core/decision_table.yaml) -> the person who holds the role (data/registries.json).
const DECIDER_PERSON = { "supplier quality engineer": "PER-GALLO", "plant quality manager": "PER-CONTI" };
const VERDICT_ICON = { blockers_found: "stop", needs_info: "question", no_blockers_found: "check", not_covered: "person" };
const SEVERITY_ICON = { blocker: "stop", warning: "alert", question: "question", info: "info" };
const ICONS = {
  stop: '<circle cx="12" cy="12" r="10"/><path d="M15 9l-6 6M9 9l6 6"/>',
  alert: '<path d="M12 3l10 18H2z"/><path d="M12 10v5M12 18h.01"/>',
  question: '<circle cx="12" cy="12" r="10"/><path d="M9.1 9a3 3 0 015.8 1c0 2-3 2.5-3 4.5M12 18h.01"/>',
  info: '<circle cx="12" cy="12" r="10"/><path d="M12 11v6M12 7h.01"/>',
  check: '<circle cx="12" cy="12" r="10"/><path d="M8 12.5l2.8 2.8L16.5 9.5"/>',
  person: '<circle cx="12" cy="8" r="4"/><path d="M4 21c1.5-4 4.5-6 8-6s6.5 2 8 6"/>',
  action: '<path d="M5 12h14M13 6l6 6-6 6"/>',
  doc: '<path d="M6 2h9l5 5v15H6z"/><path d="M14 2v6h6"/>',
  chevron: '<path d="M9 6l6 6-6 6"/>',
};


// ---- helpers -------------------------------------------------------------------------------------------

function el(tag, attrs, children) {
  const node = document.createElement(tag);
  for (const [key, value] of Object.entries(attrs || {})) {
    if (value === null || value === undefined || value === false) continue;
    if (key === "class") node.className = value;
    else if (key === "text") node.textContent = value;
    else if (key.startsWith("on")) node.addEventListener(key.slice(2), value);
    else node.setAttribute(key, value);
  }
  for (const child of [].concat(children || [])) {
    if (child === null || child === undefined || child === false) continue;
    node.append(child instanceof Node ? child : document.createTextNode(String(child)));
  }
  return node;
}

function $(id) { return document.getElementById(id); }

function icon(name, extraClass) {
  const span = document.createElement("span");
  span.className = `ico ico-${name}${extraClass ? " " + extraClass : ""}`;
  span.setAttribute("aria-hidden", "true");
  span.innerHTML = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">${ICONS[name] || ""}</svg>`;
  return span;
}

// ---- human names (front end only: the core findings are never rewritten) -------------------------------

function shortName(id) {
  const full = label(id);
  if (!full || full === id) return id || "";
  return full.replace(/\s*\([^)]*\)\s*$/, "").replace(/\s+(S\.r\.l\.|S\.p\.A\.|AB|GmbH|Ltd\.?)$/, "").trim();
}

function changeTypeText(type) {
  const text = (state.names.change_types || {})[type];
  return text ? text.replace(/\s*\([^)]*\)\s*$/, "") : (type || "Change");
}

function idChip(id) {
  return id ? el("span", { class: "id-chip", title: id }, id) : null;
}

// Name first, the id as a small secondary chip.
function nameWithId(id) {
  if (!id) return null;
  const name = shortName(id);
  return el("span", { class: "named" }, [el("span", { class: "name" }, name), name !== id ? idChip(id) : null]);
}

function partCustomer(part) {
  const info = (state.names.parts || {})[part];
  return info ? info.customer : null;
}

function humanize(text) {
  // Display only: ids that have a registry name read as that name; part ids and document ids stay.
  return String(text || "").replace(/\b([A-Z][A-Za-z]+Change)\b/g, function typeName(match) {
    const plain = (state.names.change_types || {})[match];
    return plain ? changeTypeText(match).toLowerCase() : match;
  }).replace(/\b(SUP|PLT|CUST|PER|PRG)-[A-Z0-9]+\b/g, function idName(match) { return shortName(match); })
    .replace(/ (S\.r\.l\.|S\.p\.A\.)/g, "");
}

function changeSentence(request) {
  const part = request.part || "";
  const partInfo = (state.names.parts || {})[part];
  const partText = part ? `${part}${partInfo ? ` ${partInfo.name.split(",")[0].toLowerCase()}s` : ""}` : "the part";
  const customer = partCustomer(part);
  const forWhom = customer ? `, for ${shortName(customer)}` : "";
  const site = request.site ? `, ${shortName(request.site)}` : "";
  const from = request.from_supplier ? ` from ${shortName(request.from_supplier)}` : "";
  switch (request.type) {
    case "SourceChange":
      return `Move ${partText}${from} to ${request.to_supplier ? shortName(request.to_supplier) : "a new supplier"}${site}${forWhom}`;
    case "CoatingChange":
      return `Switch ${partText} to ${request.new_coating ? shortName(request.new_coating).toLowerCase() : "a new coating"}${forWhom}`;
    case "MaterialChange":
      return `Make ${partText} in ${request.new_material ? shortName(request.new_material) : "a new material"}${forWhom}`;
    case "LocationChange":
      return `Move ${partText} production${request.site ? ` to ${shortName(request.site)}` : ""}${forWhom}`;
    default:
      return `${changeTypeText(request.type)}${part ? ` on ${partText}` : ""}${request.to_supplier ? ` at ${shortName(request.to_supplier)}` : ""}${forWhom}`;
  }
}

function deciderTile(decider, request) {
  const personId = DECIDER_PERSON[decider];
  const person = personId ? state.people[personId] : null;
  let main = decider;
  let sub = "";
  if (person) { main = person.name; sub = decider.replace(/^./, function cap(c) { return c.toUpperCase(); }); }
  else if (decider === "customer") {
    const customer = partCustomer(request.part);
    main = customer ? shortName(customer) : "The customer";
    sub = "Customer approval";
  } else if (decider) { main = decider.replace(/^./, function cap(c) { return c.toUpperCase(); }); sub = "a person decides"; }
  return el("div", { class: "tile tile-who" }, [
    el("div", { class: "tile-label" }, [icon("person"), "Who decides"]),
    el("div", { class: "tile-main" }, main || "A person"),
    sub ? el("div", { class: "tile-sub" }, [sub, personId ? idChip(personId) : null]) : null,
  ]);
}

function actionsTile(actions) {
  const list = el("ul", { class: "tile-actions" });
  for (const action of actions) list.append(el("li", {}, [icon("action"), action.replace(/^./, function cap(c) { return c.toUpperCase(); })]));
  if (!actions.length) list.append(el("li", { class: "muted" }, "None declared: a person decides"));
  return el("div", { class: "tile tile-actions-box" }, [el("div", { class: "tile-label" }, [icon("action"), "Allowed actions"]), list]);
}

// The decision sheet at the top of every card: the change in plain words, verdict, who decides, what is allowed.
function renderHero(box, card, record, compact) {
  const request = card.request || {};
  const [big, sub] = VERDICT_TEXT[card.verdict] || [card.verdict, ""];
  const row = card.decision || { allowed_actions: [], row_id: "?" };
  box.className = `verdict hero ${card.verdict}`;
  box.innerHTML = "";
  const who = request.speaker ? (state.people[request.speaker] || {}).name || request.speaker : "";
  const parts = [
    el("div", { class: "hero-kicker" }, [
      el("span", { class: "hero-type" }, changeTypeText(request.type)), idChip(request.type),
      epistemicBadge(request.epistemic),
      el("span", { class: "hero-asof" }, `as of ${request.as_of || TODAY}`),
    ]),
    el("div", { class: "hero-change" }, changeSentence(request)),
    request.utterance && !compact ? el("div", { class: "hero-quote" }, `${who ? who + ": " : ""}“${request.utterance}”`) : null,
    el("div", { class: "hero-verdict" }, [icon(VERDICT_ICON[card.verdict] || "info"), el("div", {}, [
      el("div", { class: "big" }, big),
      el("div", { class: "sub" }, sub),
    ])]),
    el("div", { class: "hero-tiles" }, [deciderTile(row.decider, request), actionsTile(row.allowed_actions || [])]),
    el("div", { class: "hero-meta" }, [
      el("span", {}, ["Table row ", el("b", {}, row.row_id)]),
      record && record.rules_version ? el("span", { title: record.rules_version }, ["Rules version ", el("b", { class: "mono" }, shortHash(record.rules_version))]) : null,
      record && record.record_id ? el("span", {}, ["Record ", el("b", { class: "mono" }, record.record_id)]) : null,
      el("span", { class: "hero-never" }, "Never an approval: a person decides"),
    ]),
  ];
  for (const part of parts) if (part) box.append(part);
}

function firstDocument(finding) {
  const seen = [];
  (function walk(steps) {
    for (const step of steps || []) {
      if (step.source && !String(step.source).startsWith("REG-")) seen.push(step.source);
      walk(step.premises);
    }
  })(finding.evidence);
  if (finding.consequence && finding.consequence.source) seen.unshift(finding.consequence.source);
  return seen[0] || null;
}

// ---- tabs: workspace, documents, decision table, records -------------------------------------------------

state.modalTab = "table";

function syncTab() {
  const modalOpen = $("modal") && !$("modal").hidden;
  const docsOpen = $("documents-section") && !$("documents-section").hidden;
  const tab = modalOpen ? state.modalTab : docsOpen ? "documents" : "workspace";
  document.body.dataset.tab = tab;
  for (const button of document.querySelectorAll("[data-tab-for]")) {
    const on = button.dataset.tabFor === tab;
    button.classList.toggle("active", on);
    button.setAttribute("aria-selected", on ? "true" : "false");
  }
}

function toWorkspace() {
  closeModal();
  if ($("documents-section")) $("documents-section").hidden = true;
  syncTab();
  window.scrollTo({ top: 0 });
}

function setProjector(on) {
  if (on) document.documentElement.dataset.theme = "projector";
  else delete document.documentElement.dataset.theme;
  try { localStorage.setItem("kva-theme", on ? "projector" : "light"); } catch (error) { /* storage blocked: theme still switches */ }
  const button = $("projector-toggle");
  if (button) { button.classList.toggle("on", on); button.setAttribute("aria-pressed", on ? "true" : "false"); }
}

async function loadNames() {
  try {
    const data = await Fallback.api("/api/names");
    state.names = { parts: data.parts || {}, people: data.people || {}, change_types: data.change_types || {} };
    Object.assign(state.people, data.people || {});
  } catch (error) {
    // names are a convenience: ids stay readable without them
  }
}

function label(id) {
  if (!id) return "";
  return state.labels[id] || id;
}

function personText(id) {
  const person = state.people[id];
  return person ? `${person.name} (${person.role})` : id;
}

function epistemicBadge(type) {
  if (!type) return null;
  return el("span", { class: `epi epi-${type.toLowerCase()}`, title: EPISTEMIC_TITLE[type] || type }, type.toLowerCase());
}

function urgencyLine(finding) {
  if (finding.urgency === undefined || finding.urgency === null) return null;
  const blocks = finding.blocks ? ` — blocks ${finding.blocks.part || ""} ${finding.blocks.change_type || ""}` : "";
  const inputs = `urgency = clamp(age_days/30 × 0.3 + blocking_edges × 0.2 + stakes × 0.5, 0, 1)\n`
    + `age_days ${finding.age_days ?? "?"} · blocking_edges ${finding.blocking_edges ?? "?"} · stakes ${finding.stakes ?? "?"}`;
  const level = finding.urgency >= 0.7 ? "high" : finding.urgency >= 0.4 ? "mid" : "low";
  return el("div", { class: `urgency u-${level}`, title: inputs }, [
    el("span", { class: "u-bar" }, el("span", { style: `width:${Math.round(finding.urgency * 100)}%` })),
    `urgency ${Number(finding.urgency).toFixed(2)}${blocks}`,
  ]);
}

function shortHash(value) { return value ? value.slice(0, 10) : ""; }

async function api(path, body) {
  // Fallback.api (offline.js): live server, or the recorded snapshot when offline (#17).
  const data = await Fallback.api(path, body);
  if (data.labels) state.labels = data.labels;
  return data;
}

function setStatus(text, isError) {
  const box = $("status");
  box.hidden = !text;
  box.textContent = text || "";
  box.className = "status" + (isError ? " error" : "");
}

function setBusy(busy) {
  for (const button of document.querySelectorAll("button.primary, .ctl button, .demo-buttons button")) {
    button.disabled = busy;
  }
}

// ---- meeting strip -------------------------------------------------------------------------------------

function fillSpeakers() {
  const select = $("speaker");
  select.innerHTML = "";
  select.append(el("option", { value: "" , text: "Speaker…" }));
  for (const [id, person] of Object.entries(state.people)) {
    select.append(el("option", { value: id, text: `${person.name} · ${person.role}` }));
  }
}

function demoButtonsFor(scenarios) {
  const ids = new Set(scenarios.map(function idOf(item) { return item.id; }));
  const buttons = [];
  for (const item of scenarios) {
    buttons.push({ text: item.title, title: item.utterance, run: function runScenario() { runScenarioDemo(item); } });
  }
  // Built-in demos for the steps of the demo plan that have no scenario entry yet.
  if (!ids.has("rule_change_r3") && !ids.has("rule_change_r4")) {
    buttons.push({ text: "The rule changed: coating June vs today", title: RULE_CHANGE_REMARK, run: runRuleChange });
  }
  if (!ids.has("no_rule")) {
    buttons.push({ text: "Move final inspection to the new CMM", title: NO_RULE_REMARK,
                   run: function runNoRule() {
                     $("remark").value = NO_RULE_REMARK; $("as-of").value = TODAY;
                     runCheck({ request: { ...NO_RULE_REQUEST, utterance: NO_RULE_REMARK, as_of: TODAY } }, "Checking");
                   } });
  }
  return buttons;
}

function renderDemoButtons() {
  const box = $("demo-buttons");
  box.innerHTML = "";
  for (const demo of demoButtonsFor(state.scenarios)) {
    box.append(el("button", { title: demo.title, onclick: demo.run }, demo.text));
  }
}

async function runScenarioDemo(item) {
  $("remark").value = item.utterance || "";
  $("as-of").value = item.as_of || TODAY;
  await runCheck({ scenario: item.id }, `Scenario “${item.title}”`);
}

async function checkRemark() {
  const remark = $("remark").value.trim();
  if (!remark) { setStatus("Type a remark first.", true); return; }
  await runCheck({ remark: remark, speaker: $("speaker").value || undefined, as_of: $("as-of").value || undefined },
                 "Parsing the remark and checking");
}

async function runCheck(body, what) {
  if (window.Meeting) Meeting.show("check");
  setBusy(true);
  setStatus(`${what}…`);
  try {
    const data = await api("/api/check", body);
    state.lastRequest = data.card.request;
    state.lastResponse = data;
    Fallback.hideForm();
    renderCard(data);
    setStatus("");
    return data;
  } catch (error) {
    if (error.parseFailed) {  // model gateway failed: offer the typed form, never a silent fake
      if (error.payload.labels) state.labels = error.payload.labels;
      setStatus(`Could not parse the remark: ${error.message}`, true);
      Fallback.showForm(error.payload, function submitForm(form) { runCheck({ form: form }, "Checking the typed form"); });
      return null;
    }
    setStatus(`Could not check: ${error.message}`, true);
    return null;
  } finally {
    setBusy(false);
  }
}

// ---- the card ------------------------------------------------------------------------------------------

function renderCard(data) {
  const card = data.card;
  if (window.Explain) Explain.setCard(card);  // explain.js: counterfactuals + explanation of this card
  $("result").hidden = false;
  renderParsed(card.request);
  renderHero($("verdict"), card, data.record, false);
  renderFindings(card.findings, data.replaced || {});
  renderContested(card.contested || []);
  renderExtra(card);
  renderNotChecked(card.not_checked || []);
  renderDecision(card, data);
  renderRecord(data.record, card);
  if (window.Explain) Explain.decorate($("record"), card);
  renderTimings(card.timings_ms || {});
}

function chip(name, value, title) {
  return el("span", { class: "chip", title: title || null }, [el("b", { text: name }), value]);
}

function renderParsed(request) {
  const box = $("parsed");
  box.innerHTML = "";
  box.append(el("span", { class: "chip" }, [el("b", { text: "change" }), changeTypeText(request.type), idChip(request.type)]));
  if (request.part) box.append(chip("part", nameWithId(request.part), label(request.part)));
  if (request.from_supplier) box.append(chip("from", nameWithId(request.from_supplier), request.from_supplier));
  if (request.to_supplier) box.append(chip("to", nameWithId(request.to_supplier), request.to_supplier));
  if (request.site) box.append(chip("site", nameWithId(request.site), request.site));
  if (request.new_material) box.append(chip("material", nameWithId(request.new_material), request.new_material));
  if (request.new_coating) box.append(chip("coating", nameWithId(request.new_coating), request.new_coating));
  if (request.scope) box.append(chip("scope", request.scope));
  box.append(chip("as of", request.as_of || TODAY));
  if (request.parse_confidence !== undefined) box.append(chip("names resolved", `${Math.round(request.parse_confidence * 100)}%`));
  for (const item of request.unresolved || []) {
    const candidates = (item.candidates || []).map(label).join(", ");
    box.append(el("span", { class: "chip unresolved", title: item.reason }, [
      el("b", { text: `${item.field}?` }),
      `“${item.text}” — ${item.reason}`,
      candidates ? el("span", { class: "cand" }, ` · candidates: ${candidates}`) : null,
    ]));
  }
}

function renderVerdict(box, verdict, withSub) {
  const [big, sub] = VERDICT_TEXT[verdict] || [verdict, ""];
  box.className = `verdict ${verdict}`;
  box.innerHTML = "";
  box.append(el("div", { class: "big" }, big));
  if (withSub) box.append(el("div", { class: "sub" }, sub));
}

function renderFindings(findings, replaced) {
  const box = $("findings");
  box.innerHTML = "";
  if (!findings.length) {
    box.append(el("p", { class: "muted" }, "No rule fired for this change."));
    return;
  }
  const shownReplaced = new Set();
  for (const finding of findings) {
    const items = (replaced[finding.rule] || []).filter(function notShown(item) {
      const key = `${finding.rule}:${item.id}`;
      if (shownReplaced.has(key)) return false;
      shownReplaced.add(key);
      return true;
    });
    box.append(renderFinding(finding, items));
  }
}

function renderFinding(finding, replacedItems) {
  const meta = el("div", { class: "f-meta" });
  const urgency = urgencyLine(finding);
  if (urgency) meta.append(urgency);
  if (finding.owner) meta.append(el("div", {}, [el("span", { class: "muted" }, "Who answers: "), el("span", { class: "owner" }, personText(finding.owner))]));
  if (finding.consequence) {
    const consequence = finding.consequence;
    meta.append(el("div", { class: "consequence" }, [
      el("b", {}, `Customer's consequence: ${consequence.type}`), " ",
      el("span", { class: "doc" }, consequence.source), " ",
      `“${consequence.quote}”`,
    ]));
  }
  if (finding.note) meta.append(el("div", { class: "note" }, `Note: ${finding.note}`));
  const doc = firstDocument(finding);
  const head = el("div", { class: "f-head", role: "button", tabindex: "0", title: finding.title }, [
    el("span", { class: `sev ${finding.severity}` }, [icon(SEVERITY_ICON[finding.severity] || "info"), el("span", { class: "sev-text" }, SEVERITY_TEXT[finding.severity] || finding.severity)]),
    el("span", { class: "f-title" }, humanize(finding.title)),
    doc ? el("span", { class: "doc-chip" }, [icon("doc"), doc]) : null,
    el("span", { class: "rule-id" }, finding.rule),
    epistemicBadge(finding.epistemic),
    icon("chevron", "f-chev"),
  ]);
  const bodyBox = el("div", { class: "f-body" }, [meta]);
  const node = el("div", { class: `finding ${finding.severity}` }, [head, bodyBox]);
  const toggleOpen = function toggleFinding(event) {
    if (event.type === "keydown" && event.key !== "Enter" && event.key !== " ") return;
    event.preventDefault();
    const open = !node.classList.contains("open");
    node.classList.toggle("open", open);
    const proof = node.querySelector("details.proof");
    if (proof) proof.open = open;
  };
  head.addEventListener("click", toggleOpen);
  head.addEventListener("keydown", toggleOpen);
  for (const item of replacedItems) bodyBox.append(renderReplaced(item));
  for (const item of replacedItems) if (item.source === item.id) bodyBox.append(impactButton(item.id));
  if ((finding.evidence || []).length) {
    const details = el("details", { class: "proof" }, [
      el("summary", {}, `Proof chain (${countLeaves(finding.evidence)} quotes)`),
      renderSteps(finding.evidence),
    ]);
    if (finding.severity === "blocker") details.open = false;
    bodyBox.append(details);
  }
  const clear = window.Explain ? Explain.lineFor(finding) : null;  // "What would clear this" (explain.js)
  if (clear) bodyBox.append(clear);
  return node;
}

function renderReplaced(item) {
  const when = [item.valid_from && `from ${item.valid_from}`, item.valid_to && `to ${item.valid_to}`].filter(Boolean).join(" ");
  const author = item.author ? ` · ${personText(item.author)}` : "";
  return el("div", { class: "replaced" }, [
    el("s", {}, `${item.id}${item.status ? ` (${String(item.status).replace(/"/g, "")})` : ""}`),
    el("span", { class: "by" }, ` replaced by ${item.replaced_by}${when ? ` · was in force ${when}` : ""}${author}`),
    item.quote ? el("div", {}, [el("span", { class: "doc" }, item.source), " ", el("s", {}, `“${item.quote}”`)]) : null,
  ]);
}

function countLeaves(steps) {
  let count = 0;
  for (const step of steps || []) {
    if (step.quote) count += 1;
    count += countLeaves(step.premises);
  }
  return count;
}

function renderSteps(steps) {
  const list = el("ul", { class: "steps" });
  for (const step of steps) {
    const item = el("li", { class: "step" }, [
      el("span", { class: "triple", title: tripleTitle(step.triple) }, step.triple),
      step.inferred ? el("span", { class: "inferred" }, `inferred by ${step.rule || "the ontology"}`) : null,
      epistemicBadge(step.epistemic),
    ]);
    if (step.context_quote) item.append(el("div", { class: "context-quote" }, step.context_quote));
    if (step.quote) {
      item.append(el("div", { class: "quote" }, [`“${step.quote}”`]));
      item.append(el("span", { class: "doc" }, step.source || "?"));
      if (step.fact_id) item.append(el("span", { class: "muted small" }, `  fact ${step.fact_id}`));
    }
    if ((step.premises || []).length) item.append(renderSteps(step.premises));
    list.append(item);
  }
  return list;
}

function tripleTitle(triple) {
  return (triple || "").split(" ").map(label).join(" · ");
}

function renderExtra(card) {
  // Only fields the card already provides. Nothing is rendered when the core does not send them.
  const box = $("extra");
  box.innerHTML = "";
  renderMaintenance(box, card);
  renderPastDecisions(box, card);
}

// ---- memory of decisions and maintenance (core/memory.py, issue #19) -------------------------------------

const REASON_STATE_CLASS = { "still holds": "holds", "superseded": "stale", "no longer in force": "stale", "changed": "stale" };

function quoteList(evidence) {
  const list = el("ul", { class: "steps" });
  for (const step of evidence || []) {
    if (!step || !step.quote) continue;
    list.append(el("li", { class: "step" }, [
      el("div", { class: "quote" }, [`“${step.quote}”`]),
      el("span", { class: "doc" }, step.source || "?"),
      step.fact_id ? el("span", { class: "muted small" }, `  fact ${step.fact_id}`) : null,
    ]));
  }
  return list;
}

function maintenanceMeta(item) {
  const parts = [];
  if (item.owner) parts.push(el("span", { class: "owner" }, `Owner: ${personText(item.owner)}`));
  if (item.urgency !== undefined && item.urgency !== null) {
    const level = item.urgency >= 0.7 ? "u-high" : "";
    parts.push(el("span", { class: `urgency ${level}`, title: "urgency = clamp(days_overdue/30 × 0.3 + blocking_edges × 0.2 + stakes × 0.5, 0, 1)" }, [
      el("span", { class: "u-bar" }, [el("span", { style: `width:${Math.round(item.urgency * 100)}%` })]),
      `urgency ${item.urgency.toFixed(2)}`,
    ]));
  }
  return parts;
}

function renderMaintenance(box, card) {
  const items = card.maintenance || [];
  if (!items.length) return;
  const known = card.request && card.request.known_at ? ` · as known on ${card.request.known_at}` : "";
  const strip = el("div", { class: "maint-strip" }, [
    el("h2", {}, "Maintenance"),
    el("p", { class: "muted small" }, `What needs a person at ${card.request.as_of || ""}${known}: promises past their date, deviations ending, decisions whose reasons changed, records that disagree.`),
  ]);
  for (const item of items) {
    const row = el("div", { class: `maint-item finding ${item.severity}${item.related ? " related" : ""}` }, [
      el("div", { class: "f-head" }, [
        el("span", { class: `sev ${item.severity}` }, item.kind.replace(/_/g, " ")),
        el("span", { class: "f-title" }, item.title),
        epistemicBadge(item.epistemic),
      ]),
    ]);
    const meta = maintenanceMeta(item);
    if (meta.length) row.append(el("div", { class: "f-meta maint-meta" }, meta));
    const proof = el("details", { class: "proof" }, [el("summary", {}, "Sources")]);
    proof.append(quoteList(item.evidence));
    row.append(proof);
    strip.append(row);
  }
  box.append(strip);
}

function renderPastDecisions(box, card) {
  const past = card.past_decisions || [];
  if (!past.length) return;
  const panel = el("div", { class: "past-panel" }, [el("h2", {}, "Past decisions")]);
  for (const item of past) {
    const status = item.status === "review" ? "question" : "info";
    const entry = el("div", { class: `finding ${status} past-decision` }, [
      el("div", { class: "f-head" }, [
        el("span", { class: "rule-id" }, item.id),
        el("span", { class: "f-title" }, `“${item.title}”`),
        epistemicBadge(item.epistemic),
        el("span", { class: `past-status ${{ review: "stale", stands: "holds" }[item.status] || ""}` }, item.status),
      ]),
      el("div", { class: "f-meta" }, [
        `${item.date || ""} · ${item.by ? personText(item.by) : ""} · `, el("span", { class: "doc" }, item.meeting || ""),
        item.reason ? el("div", {}, `Why: ${item.reason}`) : null,
      ]),
    ]);
    if ((item.reasons || []).length) {
      const list = el("ul", { class: "reason-list" });
      for (const reason of item.reasons) {
        list.append(el("li", {}, [
          el("span", { class: `reason-state ${REASON_STATE_CLASS[reason.state] || ""}` }, reason.state),
          el("b", {}, ` ${label(reason.record)} `),
          el("span", { class: "muted" }, reason.detail),
          reason.quote ? el("div", { class: "quote" }, [`“${reason.quote}”`]) : null,
          reason.source ? el("span", { class: "doc" }, reason.source) : null,
        ]));
      }
      entry.append(list);
    }
    panel.append(entry);
  }
  box.append(panel);
}

function renderNotChecked(items) {
  const box = $("not-checked");
  box.innerHTML = "";
  box.className = "notchecked";
  box.append(el("h2", {}, "Not checked"));
  if (!items.length) {
    box.append(el("p", { class: "muted small" }, "Every requirement in scope for this change is expressed in the ontology."));
    return;
  }
  box.append(el("p", { class: "muted small" }, "Requirements in scope that the ontology cannot express yet. A person reads them."));
  const list = el("ul");
  for (const item of items) {
    list.append(el("li", {}, [el("span", { class: "doc" }, item.source || item.id || "?"), " ",
                             item.summary ? `${item.summary} ` : "", item.quote ? `“${item.quote}”` : ""]));
  }
  box.append(list);
}

function renderDecision(card, data) {
  const row = card.decision;
  const box = $("decision");
  box.innerHTML = "";
  box.append(el("h3", {}, `Decision table row ${row.row_id}`));
  if (data.row_meaning) box.append(el("div", { class: "meaning" }, data.row_meaning));
  const actions = el("ul", { class: "actions" });
  for (const action of row.allowed_actions) actions.append(el("li", {}, action));
  if (!row.allowed_actions.length) actions.append(el("li", { class: "muted" }, "none declared: a person decides"));
  box.append(el("dl", { class: "kv" }, [
    el("dt", {}, "Allowed"), el("dd", {}, actions),
    el("dt", {}, "Decides"), el("dd", {}, [el("b", {}, row.decider), DECIDER_PERSON[row.decider] && state.people[DECIDER_PERSON[row.decider]] ? ` · ${state.people[DECIDER_PERSON[row.decider]].name}` : ""]),
    el("dt", {}, "Rests on"), el("dd", {}, row.rests_on.length ? row.rests_on.join(", ") : "—"),
  ]));
  if ((data.drop_rows || []).length) box.append(el("div", { class: "note small" }, `Table edited in memory: ${data.table_note}`));
  const cover = card.coverage || {};
  box.append(el("div", { class: "coverage" }, [
    `Table checked: ${cover.input_sets} input sets, ${cover.to_person} go to a person, ${cover.overlaps} overlap. `,
    el("button", { class: "link", onclick: function openTable() { showTable(row.row_id, data.drop_rows || []); } }, "View the whole table"),
  ]));
}

function renderRecord(record, card) {
  const box = $("record");
  box.innerHTML = "";
  box.append(el("h3", {}, "Decision record"));
  box.append(el("dl", { class: "kv" }, [
    el("dt", {}, "Record"), el("dd", { class: "mono" }, record.record_id),
    el("dt", {}, "Rules version"), el("dd", { class: "mono", title: record.rules_version }, shortHash(record.rules_version)),
    el("dt", {}, "As of"), el("dd", {}, record.as_of),
    el("dt", {}, "Facts in force"), el("dd", {}, String((record.facts_in_force || []).length)),
    el("dt", {}, "Rules fired"), el("dd", {}, (record.rules_fired || []).join(", ") || "none"),
    el("dt", {}, "Decided by"), el("dd", {}, record.decided_by || el("span", { class: "muted" }, `open — ${card.decision.decider}`)),
  ]));
}

function renderTimings(timings) {
  const order = ["parse", "snapshot", "closure", "rules", "total"];
  const parts = order.filter(function has(key) { return timings[key] !== undefined; })
                     .map(function fmt(key) { return `${key} ${Math.round(timings[key])} ms`; });
  $("timings").textContent = parts.join(" · ");
}

// ---- comparisons (#16) ---------------------------------------------------------------------------------

async function compare(bodyA, bodyB, titleA, titleB, lead) {
  setBusy(true);
  setStatus("Checking both…");
  const box = $("compare");
  try {
    const a = await api("/api/check", bodyA);
    const b = await api("/api/check", bodyB);
    box.innerHTML = "";
    box.append(compareColumn(a, b, titleA), compareColumn(b, a, titleB));
    if (lead) box.prepend(el("p", { class: "muted", style: "grid-column: 1 / -1; margin: 0" }, lead));
    setStatus("");
    box.scrollIntoView({ behavior: "smooth", block: "start" });
  } catch (error) {
    setStatus(`Could not compare: ${error.message}`, true);
  } finally {
    setBusy(false);
  }
}

function compareColumn(data, other, title) {
  const card = data.card;
  const record = data.record;
  const otherRules = new Set(other.card.findings.map(function key(f) { return `${f.rule}:${f.severity}`; }));
  const findings = el("ul", { class: "cmp-list" });
  for (const finding of card.findings) {
    const isNew = !otherRules.has(`${finding.rule}:${finding.severity}`);
    findings.append(el("li", { class: isNew ? "new" : null }, [
      el("span", { class: `sev ${finding.severity}` }, finding.severity), " ", el("b", {}, finding.rule), " ", finding.title,
      finding.note ? el("div", { class: "note small" }, finding.note) : null,
    ]));
  }
  const mine = new Set(card.findings.map(function key(f) { return `${f.rule}:${f.severity}`; }));
  for (const finding of other.card.findings) {
    if (!mine.has(`${finding.rule}:${finding.severity}`)) {
      findings.append(el("li", { class: "gone" }, `not here (only in the other answer): ${finding.rule} ${finding.severity}`));
    }
  }
  if (!card.findings.length) findings.append(el("li", { class: "muted" }, "no rule fired"));
  const verdict = el("div");
  renderVerdict(verdict, card.verdict, false);
  const diffClass = function differs(a, b) { return a !== b ? "diff" : null; };
  const row = card.decision;
  return el("div", { class: "cmp-col" }, [
    el("h3", {}, title),
    verdict,
    el("dl", { class: "kv" }, [
      el("dt", {}, "Row"), el("dd", {}, el("span", { class: diffClass(row.row_id, other.card.decision.row_id) }, `${row.row_id} — ${data.row_meaning || ""}`)),
      el("dt", {}, "Allowed"), el("dd", {}, row.allowed_actions.join("; ") || "none declared"),
      el("dt", {}, "Decides"), el("dd", {}, row.decider),
      el("dt", {}, "Record"), el("dd", { class: "mono" }, record.record_id),
      el("dt", {}, "Rules version"), el("dd", { class: "mono" }, el("span", { class: diffClass(record.rules_version, other.record.rules_version) }, shortHash(record.rules_version))),
      el("dt", {}, "As of"), el("dd", {}, el("span", { class: diffClass(record.as_of, other.record.as_of) }, record.as_of)),
      el("dt", {}, "Facts in force"), el("dd", {}, el("span", { class: diffClass((record.facts_in_force || []).length, (other.record.facts_in_force || []).length) }, String((record.facts_in_force || []).length))),
      el("dt", {}, "Rules fired"), el("dd", {}, (record.rules_fired || []).join(", ") || "none"),
    ]),
    el("div", { class: "label", style: "margin-top:10px" }, "Findings"),
    findings,
  ]);
}

function runRuleChange() {
  const r3 = state.scenarios.find(function isR3(item) { return item.id === "rule_change_r3"; });
  const r4 = state.scenarios.find(function isR4(item) { return item.id === "rule_change_r4"; });
  // The same remark, parsed the same way, asked on two dates.
  const bodyA = r3 ? { scenario: r3.id } : { remark: RULE_CHANGE_REMARK, as_of: "2026-06-15" };
  const bodyB = r4 ? { scenario: r4.id } : { remark: RULE_CHANGE_REMARK, as_of: TODAY };
  $("remark").value = (r4 && r4.utterance) || RULE_CHANGE_REMARK;
  return compare(bodyA, bodyB, `As of ${r3 ? r3.as_of : "15 Jun 2026"} — Aurelia manual rev 3`,
                 `As of ${r4 ? r4.as_of : "14 Nov 2026"} — Aurelia manual rev 4`,
                 "Same question, same code. Only the customer's manual in force changed: rev 3 asked for a notification, rev 4 asks for approval.");
}

function currentRequest() {
  if (state.lastRequest) return { ...state.lastRequest };
  return null;
}

async function runTimeTravel() {
  let request = currentRequest();
  if (!request) {
    const data = await runCheck({ scenario: "main" }, "Checking the main scenario first");
    if (!data) return;
    request = { ...data.card.request };
  }
  const dateA = $("cmp-a").value;
  const dateB = $("cmp-b").value;
  await compare({ request: { ...request, as_of: dateA } }, { request: { ...request, as_of: dateB } },
                `As of ${dateA}`, `As of ${dateB}`, "Same request on two dates: the facts in force change, the rules do not.");
}

async function runTableEdit() {
  let request = currentRequest();
  if (!request) {
    const data = await runCheck({ scenario: "main" }, "Checking the main scenario first");
    if (!data) return;
    request = { ...data.card.request };
  }
  const drop = $("drop-row").value;
  await compare({ request: request }, { request: request, drop_rows: [drop] },
                "Declared table (core/decision_table.yaml)", `Edited in memory: row ${drop} removed`,
                "Same request and facts. One row of the decision table removed: a different row answers, and the rules version in the record changes.");
}

// ---- #28 contested values, side by side -----------------------------------------------------------------

function contestedBox() {
  let box = $("contested");
  if (!box) {
    box = el("div", { id: "contested" });
    $("findings").after(box);
  }
  return box;
}

function renderContested(pairs) {
  const box = contestedBox();
  box.innerHTML = "";
  if (!pairs.length) return;
  box.append(el("h3", { class: "contested-head" }, `Two current values (${pairs.length}): a person decides`));
  for (const pair of pairs) box.append(renderContestedPair(pair));
}

function renderContestedPair(pair) {
  const [subject, predicate] = pair.key || [];
  const sides = (pair.sides || []).map(function side(item) {
    return el("div", { class: `contested-side ${item.status === "in force" ? "in-force" : ""}` }, [
      el("div", { class: "contested-value" }, String(item.value)),
      el("div", { class: "muted" }, item.status || ""),
      el("div", {}, [el("span", { class: "doc" }, item.source || ""), " ", `“${item.quote || ""}”`]),
      item.rank ? el("div", { class: "muted" }, `rank ${item.rank}${item.valid_from ? ` · from ${item.valid_from}` : ""}`) : null,
    ]);
  });
  return el("div", { class: "contested-pair" }, [
    el("div", { class: "contested-key" }, [el("b", {}, `${label(subject)} · ${predicate || ""}`),
      el("span", { class: "muted" }, ` ${pair.reason || ""}`)]),
    el("div", { class: "contested-sides" }, sides),
    pair.owner ? el("div", {}, [el("span", { class: "muted" }, "Who decides: "), el("span", { class: "owner" }, personText(pair.owner))]) : null,
  ]);
}

// ---- #29 a document changed: what is affected ----------------------------------------------------------

function impactButton(doc) {
  return el("button", { class: "link impact-btn", onclick: function openImpact() { showImpact(doc); } },
            "What does this document change affect?");
}

function impactSection(title, items, line) {
  const list = el("ul", { class: "impact-list" }, items.map(function li(item) { return el("li", {}, line(item)); }));
  return el("div", {}, [el("h3", {}, `${title} (${items.length})`), items.length ? list : el("p", { class: "muted" }, "None.")]);
}

async function showImpact(doc) {
  try {
    const data = await api(`/api/impact?doc=${encodeURIComponent(doc)}`);
    const report = data.impact;
    const lead = report.superseded
      ? `${doc} is superseded by ${report.replaced_by.join(", ")}. Each item below: ${report.status}.`
      : `${doc} is not superseded by a record in force. Listing what cites it.`;
    const body = el("div", { class: "impact" }, [
      el("p", {}, lead),
      impactSection("Facts", report.facts, function factLine(item) {
        return [el("span", { class: "mono" }, `${item.s} ${item.p} ${item.o}`), " ", el("span", { class: "doc" }, item.source),
                el("span", { class: "muted" }, ` ${item.why} · ${item.status}`)];
      }),
      impactSection("Decision-table rows", report.table_rows, function rowLine(row) {
        const how = row.cites.length ? `cites ${row.cites.join(", ")}` : `via ${row.via_rules.join(", ")} (reads ${row.reads.join(", ")})`;
        return [el("b", {}, row.row_id), ` ${row.meaning || ""} `, el("span", { class: "muted" }, `${how} · ${row.status}`)];
      }),
      impactSection("Recorded decisions", report.recorded_decisions, function recordLine(entry) {
        return [el("span", { class: "mono" }, entry.record_id), ` as of ${entry.as_of}: row ${entry.decision_row}, ${entry.verdict} `,
                el("span", { class: "muted" }, `${entry.facts_used.length} facts from ${doc} · ${entry.status}`)];
      }),
      impactSection("Past decisions", report.past_decisions, function pastLine(item) {
        return [el("b", {}, item.id), ` ${item.reason || ""} `, el("span", { class: "muted" }, `${item.from} · ${item.status}`)];
      }),
    ]);
    openModal(`What changes with ${doc}`, body);
  } catch (error) {
    setStatus(`Could not load the impact report: ${error.message}`, true);
  }
}

// ---- table and records ---------------------------------------------------------------------------------

function openModal(title, body, tab) {
  state.modalTab = tab || "panel";
  if ($("documents-section")) $("documents-section").hidden = true;
  $("modal-title").textContent = title;
  const box = $("modal-body");
  box.innerHTML = "";
  box.append(body);
  $("modal").hidden = false;
  syncTab();
  window.scrollTo({ top: 0 });
}

function closeModal() { $("modal").hidden = true; syncTab(); }

function conditionText(when) {
  const parts = [];
  for (const key of ["classes", "all", "any", "none"]) {
    if (when[key] === undefined) continue;
    const value = Array.isArray(when[key]) ? when[key].join(", ") : when[key];
    parts.push(`${key}: ${value}`);
  }
  return parts.join(" · ") || "(no condition)";
}

async function showTable(hitRow, dropRows) {
  try {
    const declared = await api("/api/table");
    const table = declared.table;
    const report = declared.coverage;
    const body = el("div");
    body.append(el("p", { class: "muted" }, [
      `${table.version_note} · hit policy ${table.hit_policy} (first matching row answers) · rules version `,
      el("span", { class: "mono" }, shortHash(declared.rules_version)),
    ]));
    body.append(el("p", {}, `Table checked: ${report.input_sets} input sets (2^${report.rules.length} rule sets × ${report.change_classes} change classes), `
                            + `${report.to_person} go to a person, ${report.overlaps} overlap (the first row wins).`));
    const head = el("tr", {}, ["Row", "Meaning", "When", "Allowed actions", "Decides"].map(function th(text) { return el("th", {}, text); }));
    const tbody = el("tbody");
    for (const row of table.rows) {
      const classes = [row.id === hitRow ? "hit" : null, (dropRows || []).includes(row.id) ? "dropped" : null].filter(Boolean).join(" ");
      tbody.append(el("tr", { class: classes || null }, [
        el("td", {}, row.id),
        el("td", {}, row.meaning || ""),
        el("td", { class: "small" }, conditionText(row.when || {})),
        el("td", {}, (row.actions || []).join("; ") || "—"),
        el("td", {}, row.decider),
      ]));
    }
    body.append(el("table", { class: "dt" }, [el("thead", {}, head), tbody]));
    const view = typeof DmnTab !== "undefined" ? DmnTab.wrap(body, hitRow, dropRows) : body;  // DMN tab (dmn.js)
    openModal(hitRow ? `Decision table — row ${hitRow} matched` : "Decision table", view, "table");
  } catch (error) {
    setStatus(`Could not load the table: ${error.message}`, true);
  }
}

async function showRecords() {
  try {
    const data = await api("/api/records?limit=40");
    const head = el("tr", {}, ["Record", "Created (UTC)", "Change", "As of", "Verdict", "Row", "Rules fired", "Rules version", ""].map(function th(text) { return el("th", {}, text); }));
    const tbody = el("tbody");
    for (const record of data.records) {
      const request = record.request || {};
      tbody.append(el("tr", {}, [
        el("td", { class: "mono" }, record.record_id),
        el("td", {}, (record.created_at || "").replace("T", " ").replace("+00:00", "")),
        el("td", {}, `${changeTypeText(request.type)} ${request.part || ""}${request.to_supplier ? " → " + shortName(request.to_supplier) : ""}`),
        el("td", {}, record.as_of),
        el("td", {}, (VERDICT_TEXT[record.verdict] || [record.verdict])[0]),
        el("td", {}, record.decision_row),
        el("td", {}, (record.rules_fired || []).join(", ")),
        el("td", { class: "mono" }, shortHash(record.rules_version)),
        el("td", {}, window.Explain ? el("button", { class: "link", onclick: function explainRecord() { Explain.showRecord(record.record_id); } }, "Explain") : ""),
      ]));
    }
    const body = el("div", {}, [
      el("p", { class: "muted" }, "Append-only log (data/decisions.jsonl): every check writes one record with the hash of the rules that produced it."),
      el("table", { class: "dt records" }, [el("thead", {}, head), tbody]),
    ]);
    openModal("Decision records", body, "records");
  } catch (error) {
    setStatus(`Could not load records: ${error.message}`, true);
  }
}

// ---- start ---------------------------------------------------------------------------------------------

async function start() {
  $("check-btn").addEventListener("click", checkRemark);
  $("tab-workspace").addEventListener("click", toWorkspace);
  $("projector-toggle").addEventListener("click", function flipTheme() {
    setProjector(document.documentElement.dataset.theme !== "projector");
  });
  setProjector(document.documentElement.dataset.theme === "projector");
  for (const id of ["modal", "documents-section"]) {
    new MutationObserver(syncTab).observe($(id), { attributes: true, attributeFilter: ["hidden"] });
  }
  syncTab();
  $("remark").addEventListener("keydown", function onKey(event) {
    if (event.key === "Enter" && (event.metaKey || event.ctrlKey)) checkRemark();
  });
  $("cmp-rule").addEventListener("click", runRuleChange);
  $("cmp-time").addEventListener("click", runTimeTravel);
  $("cmp-table").addEventListener("click", runTableEdit);
  $("open-table").addEventListener("click", function openTable() {
    showTable(state.lastResponse ? state.lastResponse.card.decision.row_id : null, state.lastResponse ? state.lastResponse.drop_rows : []);
  });
  $("open-records").addEventListener("click", showRecords);
  $("modal-close").addEventListener("click", closeModal);
  $("modal").addEventListener("click", function outside(event) { if (event.target === $("modal")) closeModal(); });
  document.addEventListener("keydown", function esc(event) { if (event.key === "Escape") closeModal(); });
  try {
    const data = await api("/api/scenarios");
    state.scenarios = data.scenarios || [];
    state.people = { ...state.people, ...(data.people || {}) };
    await loadNames();
    fillSpeakers();
    renderDemoButtons();
    const table = await api("/api/table");
    const select = $("drop-row");
    for (const row of table.table.rows) {
      if (row.id === "R0") continue;
      select.append(el("option", { value: row.id, text: `drop ${row.id}` }));
    }
    select.value = "D2";
  } catch (error) {
    setStatus(`Server not reachable: ${error.message}`, true);
  }
}

start();
