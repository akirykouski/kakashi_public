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

const state = { labels: {}, people: {}, scenarios: [], lastRequest: null, lastResponse: null, table: null };

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
  attachSources(data);
  return data;
}

// Blocker source chips (server: finding_sources, parallel to card.findings): {name, id, clause}.
function attachSources(data) {
  const sources = data && data.finding_sources;
  if (!sources || !data.card || !data.card.findings) return;
  data.card.findings.forEach(function tag(finding, index) { finding._sources = sources[index] || []; });
}

function sourceChips(sources) {
  return el("div", { class: "f-chips" }, sources.map(function chip(source) {
    const text = [source.name, source.id + (source.clause ? ` \u00a7${source.clause}` : "")].join(" \u00b7 ");
    return el("span", { class: "src-chip", title: source.id }, text);
  }));
}

function setStatus(text, isError) {
  const box = $("status");
  box.hidden = !text;
  box.textContent = text || "";
  box.className = "status" + (isError ? " error" : "");
}

function setBusy(busy) {
  for (const button of document.querySelectorAll("button.primary, .ctl button, .demo-buttons button, .live-chip, #more-select")) {
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
  if (state.people["PER-FERRI"]) select.value = "PER-FERRI";  // the purchasing lead
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

const SHORT_LABEL = {
  main: "Supplier switch", main_after_audit: "After the re-audit", elv: "Cheaper passivation", silence: "Postpone delivery",
  subtier: "Sub-tier heat treat", rule_change_r3: "Coating, June rule", rule_change_r4: "Coating, today",
  no_rule: "New CMM inspection", known_at_11_08: "Known on 8 Nov", dev_expired: "Expired deviation", contradiction: "Yield contradiction",
};

function renderDemoButtons() {
  const select = $("more-select");
  if (!select) return;
  select.innerHTML = "";
  select.append(el("option", { value: "", text: "More\u2026" }));
  const demos = demoButtonsFor(state.scenarios);
  demos.forEach(function add(demo, index) {
    const scenario = state.scenarios[index];
    const short = scenario && SHORT_LABEL[scenario.id] || demo.text.split(" ").slice(0, 4).join(" ");
    select.append(el("option", { value: String(index), text: short, title: demo.title }));
  });
  select.onchange = function pick() {
    const demo = demos[Number(select.value)];
    select.value = "";
    if (demo) demo.run();
  };
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
  renderVerdict($("verdict"), card.verdict, true, card.findings, verdictOpts(card, false));
  if (data.row_meaning) $("verdict").append(el("div", { class: "vsub" }, data.row_meaning));
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

function bareName(id) {
  return String(label(id) || "").replace(/\s+(S\.?\s?r\.?\s?l\.?|S\.?\s?p\.?\s?A\.?)$/i, "").trim();
}

function shortName(id) {
  const words = bareName(id).split(/\s+/).filter(Boolean);
  return words.length > 1 ? words[words.length - 1] : (words[0] || "");
}

function camelWords(text) {
  return String(text || "").replace(/([a-z])([A-Z])/g, "$1 $2").toLowerCase().replace(/^./, function up(c) { return c.toUpperCase(); });
}

function changeLine(request) {
  const bits = [request.part || camelWords(request.type)];
  if (request.from_supplier || request.to_supplier) {
    bits.push(`${bareName(request.from_supplier) || "?"} \u2192 ${bareName(request.to_supplier) || "?"}`);
  } else if (request.new_coating) bits.push(`coating \u2192 ${label(request.new_coating)}`);
  else if (request.new_material) bits.push(`material \u2192 ${label(request.new_material)}`);
  else if (request.part) bits.push(camelWords(request.type));
  return bits.join(" \u00b7 ");
}

function renderParsed(request) {
  const box = $("parsed");
  box.innerHTML = "";
  if (request.utterance) {
    const who = request.speaker ? `${personText(request.speaker)}: ` : "";
    box.append(el("div", { class: "who" }, `${who}\u201c${request.utterance}\u201d`));
  }
  box.append(el("div", { class: "change-line" }, changeLine(request)));
  for (const item of request.unresolved || []) {
    const candidates = (item.candidates || []).map(label).join(", ");
    box.append(el("span", { class: "chip unresolved", title: item.reason }, [
      el("b", { text: `${item.field}?` }),
      `\u201c${item.text}\u201d \u2014 ${item.reason}`,
      candidates ? el("span", { class: "cand" }, ` \u00b7 candidates: ${candidates}`) : null,
    ]));
  }
}

function capitalize(text) { return String(text || "").replace(/^./, function up(c) { return c.toUpperCase(); }); }

function shortDate(iso) {
  const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  const m = /^(\d{4})-(\d{2})-(\d{2})/.exec(iso || "");
  return m ? `${Number(m[3])} ${months[Number(m[2]) - 1]}` : "";
}

// Headline options: who decides, and the "As of 5 Nov: " prefix (always in the meeting, only off-today on the Check card).
function verdictOpts(card, alwaysDate) {
  const asOf = card.request && card.request.as_of;
  const date = asOf && (alwaysDate || asOf !== TODAY) ? shortDate(asOf) : "";
  return { decider: card.decision && card.decision.decider, date: date };
}

function verdictHeadline(verdict, findings, opts) {
  const blockers = (findings || []).filter(function isBlocker(f) { return f.severity === "blocker"; }).length;
  const who = opts && opts.decider ? ` ${capitalize(opts.decider)} decides.` : "";
  let text;
  if (verdict === "blockers_found" && findings) text = `${blockers} blocker${blockers === 1 ? "" : "s"}.${who}`;
  else if (verdict === "needs_info") text = `Needs information.${who}`;
  else if (verdict === "no_blockers_found") text = "No blockers found. Not an approval.";
  else if (verdict === "not_covered") text = `Not covered.${who || " A person decides."}`;
  else text = (VERDICT_TEXT[verdict] || [verdict])[0];
  return opts && opts.date ? `As of ${opts.date}: ${text}` : text;
}

function renderVerdict(box, verdict, withSub, findings, opts) {
  box.className = `verdict ${verdict}`;
  box.innerHTML = "";
  box.append(el("div", { class: "big" }, verdictHeadline(verdict, findings, opts)));
}

function renderFindings(findings, replaced) {
  const box = $("findings");
  box.innerHTML = "";
  if (!findings.length) {
    box.append(el("p", { class: "muted" }, "No rule fired for this change."));
    return;
  }
  const shownReplaced = new Set();
  cfSeen = new Set();
  for (const finding of findings) {
    const items = (replaced[finding.rule] || []).filter(function notShown(item) {
      const key = `${finding.rule}:${item.id}`;
      if (shownReplaced.has(key)) return false;
      shownReplaced.add(key);
      return true;
    });
    box.append(renderFinding(finding, items));
  }
  cfSeen = null;
}

let cfSeen = null;  // "What would clear this" lines already shown on this card: a repeat is not drawn again

// ---- plain-language sources (frontend only; built from fields the card already carries) -------------------

const SOURCE_NAMES = {
  "REG-ASL": "Approved supplier list", "REG-PARTS": "Parts register", "REG-PROGRAMS": "Programs register",
  "REG-CUSTOMERS": "Customer register", "REG-CAPABILITIES": "Supplier capability register",
  "REG-MATERIALS": "Materials register", "REG-SUPPLIER_QUALIFICATION": "Supplier qualification register",
};

function sourceName(id) {
  if (!id) return "";
  if (SOURCE_NAMES[id]) return SOURCE_NAMES[id];
  if (/^REG-/.test(id)) return id.slice(4).replace(/_/g, " ").toLowerCase().replace(/^./, function up(c) { return c.toUpperCase(); }) + " register";
  if (/^QP-/.test(id)) return `Quality procedure ${id}`;
  if (/^CSR-/.test(id)) return `Customer requirement ${id}`;
  if (/^8D-/.test(id)) return `8D report ${id}`;
  if (/^DEV-/.test(id)) return `Deviation ${id}`;
  const named = state.labels[id];
  return named && named !== id ? named : id;
}

function csvFields(line) {
  const out = [];
  let cur = "", quoted = false;
  for (const ch of line) {
    if (ch === '"') quoted = !quoted;
    else if (ch === "," && !quoted) { out.push(cur); cur = ""; }
    else cur += ch;
  }
  out.push(cur);
  return out;
}

function readableQuote(source, quote) {
  const text = String(quote || "").replace(/\s+/g, " ").trim();
  if (!/^REG-/.test(source || "") || !text.includes(",")) return { text: text, raw: false };
  const f = csvFields(text);
  const L = function lab(x) { return x ? label(x) : ""; };
  const join = function j(parts) { return parts.filter(Boolean).join(", "); };
  let out = null;
  if (source === "REG-PARTS" && f.length >= 6) out = `${f[0]} ${f[1]}: rev ${f[3]}, made of ${L(f[4])}, coating ${L(f[5])}`;
  else if (source === "REG-ASL" && f.length >= 7) out = `${L(f[1])} is ${f[5]} for ${f[2]} at ${L(f[3])} for ${L(f[4])}, since ${f[6]}`;
  else if (source === "REG-CAPABILITIES" && f.length >= 4) out = `${L(f[1])} is qualified for ${L(f[2])}, since ${f[3]}`;
  else if (source === "REG-PROGRAMS" && f.length >= 3) out = join([f[1], `customer ${L(f[2])}`, L(f[3])]);
  else if (source === "REG-CUSTOMERS" && f.length >= 4) out = join([f[1], L(f[2]), `requirements ${f[3].replace(/;/g, ", ")}`]);
  else if (source === "REG-MATERIALS" && f.length >= 6) out = join([f[1], f[5] ? `typical yield ${f[5]} MPa` : ""]);
  else if (source === "REG-SUPPLIER_QUALIFICATION" && f.length >= 4) out = join([`${L(f[1])} ${f[2]} since ${f[3]}`, f[7]]);
  return out ? { text: out, raw: false } : { text: text, raw: true };
}

function bestQuote(steps) {
  const leaves = [];
  (function walk(list) {
    for (const step of list || []) {
      if (step.quote) leaves.push(step);
      walk(step.premises);
    }
  })(steps);
  return leaves.find(function policy(step) { return !/^REG-/.test(step.source || ""); }) || leaves[0] || null;
}

function renderFinding(finding, replacedItems) {
  const meta = el("div", { class: "f-meta" });
  if (finding.owner) meta.append(el("div", {}, [el("span", { class: "muted" }, "Who answers: "), el("span", { class: "owner" }, personText(finding.owner))]));
  if (finding.consequence) {
    const consequence = finding.consequence;
    meta.append(el("div", { class: "consequence" }, [
      `Customer consequence: ${consequence.type}. `, `\u201c${consequence.quote}\u201d `,
      el("span", { class: "f-src" }, sourceName(consequence.source)),
    ]));
  }
  if (finding.note) meta.append(el("div", { class: "note" }, finding.note));
  const node = el("div", { class: `finding ${finding.severity}` }, [
    el("div", { class: "f-head" }, [
      el("span", { class: `sev ${finding.severity}` }, SEVERITY_TEXT[finding.severity] || finding.severity),
      el("span", { class: "f-title" }, finding.title),
      el("span", { class: "rule-id", title: "Rule code" }, finding.rule),
    ]),
  ]);
  let best = bestQuote(finding.evidence);
  if (best && /^REG-/.test(best.source || "") && (finding._sources || []).length) {
    // decisive register row (the first source chip) instead of the generic part row
    const lead = finding._sources[0].id;
    const walkLeaves = function find(list) {
      for (const step of list || []) {
        if (step.quote && String(step.quote).startsWith(lead + ",")) return step;
        const inner = find(step.premises);
        if (inner) return inner;
      }
      return null;
    };
    best = walkLeaves(finding.evidence) || best;
  }
  let sourceLine = null;
  const chips = finding.severity === "blocker" && (finding._sources || []).length ? sourceChips(finding._sources) : null;
  if (best) {
    const shown = readableQuote(best.source, best.quote);
    const clipped = shown.text.length > 220 ? shown.text.slice(0, 217).trimEnd() + "\u2026" : shown.text;
    sourceLine = el("div", { class: "f-source" }, [
      el("span", { class: shown.raw ? "f-quote mono" : "f-quote" }, `\u201c${clipped}\u201d`),
      chips ? null : el("span", { class: "f-src" }, ` ${sourceName(best.source)}`),
    ]);
  }
  const hasProof = (finding.evidence || []).length || finding.urgency !== undefined && finding.urgency !== null;
  // Blockers show their quote; warnings, questions and info show the title only, the quote sits behind the proof toggle.
  if (chips) node.append(chips);
  if (sourceLine && (finding.severity === "blocker" || !hasProof)) node.append(sourceLine);
  node.append(meta);
  if (hasProof) {
    const body = el("div", { class: "proof-body" });
    if (sourceLine && finding.severity !== "blocker") body.append(sourceLine);
    for (const item of replacedItems) body.append(renderReplaced(item));
    for (const item of replacedItems) if (item.source === item.id) body.append(impactButton(item.id));
    const urgency = urgencyLine(finding);
    if (urgency) body.append(urgency);
    if ((finding.evidence || []).length) body.append(renderSteps(finding.evidence));
    const summaryText = `Show proof (${countLeaves(finding.evidence)} quotes)`;
    const details = el("details", { class: "proof" }, [el("summary", {}, summaryText), body]);
    details.addEventListener("toggle", function flip() {
      details.querySelector("summary").textContent = details.open ? "Hide proof" : summaryText;
    });
    node.append(details);
  } else {
    for (const item of replacedItems) node.append(renderReplaced(item));
  }
  const clear = window.Explain ? Explain.lineFor(finding) : null;  // "What would clear this" (explain.js)
  if (clear) {
    const head = clear.querySelector("summary");
    const key = (head || clear).textContent;
    if (!cfSeen || !cfSeen.has(key)) node.append(clear);
    if (cfSeen) cfSeen.add(key);
  }
  return node;
}

function renderReplaced(item) {
  const when = [item.valid_from && `from ${item.valid_from}`, item.valid_to && `to ${item.valid_to}`].filter(Boolean).join(" ");
  const author = item.author ? ` · ${personText(item.author)}` : "";
  return el("div", { class: "replaced" }, [
    el("s", {}, `${item.id}${item.status ? ` (${String(item.status).replace(/"/g, "")})` : ""}`),
    el("span", { class: "by" }, ` replaced by ${item.replaced_by}${when ? ` · was in force ${when}` : ""}${author}`),
    item.quote ? el("div", {}, [el("s", {}, `“${readableQuote(item.source, item.quote).text}”`), el("span", { class: "f-src" }, sourceName(item.source))]) : null,
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
  box.append(el("details", { class: "maint-wrap" }, [
    el("summary", {}, `${items.length} open item${items.length === 1 ? "" : "s"}`), strip]));
}

function renderPastDecisions(box, card) {
  const past = card.past_decisions || [];
  if (!past.length) return;
  const panel = el("details", { class: "past-panel" }, [
    el("summary", {}, `${past.length} past decision${past.length === 1 ? "" : "s"}`)]);
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
          reason.detail && String(reason.detail).trim().toLowerCase() !== String(reason.state || "").trim().toLowerCase()
            ? el("span", { class: "muted" }, reason.detail) : null,
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
  box.hidden = !items.length;  // nothing to say when every requirement in scope is covered
  if (!items.length) return;
  box.append(el("h2", {}, "Not checked"));
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
  box.append(el("h3", {}, `Rule ${row.row_id}`));
  const actions = el("ul", { class: "actions" });
  for (const action of row.allowed_actions) actions.append(el("li", {}, action));
  if (!row.allowed_actions.length) actions.append(el("li", { class: "muted" }, "none declared: a person decides"));
  const basis = (row.rests_on || []).filter(function notRuleId(item) { return !/^R\d+[a-z]?$/.test(item); });
  box.append(el("dl", { class: "kv" }, [
    el("dt", {}, "Allowed"), el("dd", {}, actions),
    el("dt", {}, "Rests on"), el("dd", {}, basis.length ? basis.join(", ") : "\u2014"),
  ]));
  if ((data.drop_rows || []).length) box.append(el("div", { class: "note small" }, `Table edited in memory: ${data.table_note}`));
  box.append(el("div", { class: "coverage" }, [
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
  renderVerdict(verdict, card.verdict, false, card.findings, verdictOpts(card, false));
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

function openModal(title, body) {
  $("modal-title").textContent = title;
  const box = $("modal-body");
  box.innerHTML = "";
  box.append(body);
  $("modal").hidden = false;
}

function closeModal() { $("modal").hidden = true; }

function conditionText(when) {
  const list = function asList(value) { return Array.isArray(value) ? value : [value]; };
  const parts = [];
  if (when.classes !== undefined) parts.push(list(when.classes).map(camelWords).join(" or ").replace(/^./, function up(c) { return c.toUpperCase(); }));
  if (when.all !== undefined) parts.push(...list(when.all));
  if (when.any !== undefined) parts.push(`any of ${list(when.any).join(", ")}`);
  if (when.none !== undefined) parts.push(`not ${list(when.none).join(", ")}`);
  return parts.join(" + ") || "(no condition)";
}

async function showTable(hitRow, dropRows) {
  try {
    const declared = await api("/api/table");
    const table = declared.table;
    const report = declared.coverage;
    const body = el("div");
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
    openModal(hitRow ? `Decision table — row ${hitRow} matched` : "Decision table", view);
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
        el("td", {}, `${request.type || ""} ${request.part || ""}${request.to_supplier ? " → " + label(request.to_supplier) : ""}`),
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
    openModal("Decision records", body);
  } catch (error) {
    setStatus(`Could not load records: ${error.message}`, true);
  }
}

// ---- start ---------------------------------------------------------------------------------------------

async function start() {
  $("check-btn").addEventListener("click", checkRemark);
  $("remark").addEventListener("keydown", function onKey(event) {
    if (event.key === "Enter") checkRemark();
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
    state.people = data.people || {};
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
