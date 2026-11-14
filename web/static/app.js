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
  const options = body ? { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) } : {};
  const response = await fetch(path, options);
  const data = await response.json();
  if (!response.ok || data.error) throw new Error(data.error || `HTTP ${response.status}`);
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
  setBusy(true);
  setStatus(`${what}…`);
  try {
    const data = await api("/api/check", body);
    state.lastRequest = data.card.request;
    state.lastResponse = data;
    renderCard(data);
    setStatus("");
    return data;
  } catch (error) {
    setStatus(`Could not check: ${error.message}`, true);
    return null;
  } finally {
    setBusy(false);
  }
}

// ---- the card ------------------------------------------------------------------------------------------

function renderCard(data) {
  const card = data.card;
  $("result").hidden = false;
  renderParsed(card.request);
  renderVerdict($("verdict"), card.verdict, true);
  renderFindings(card.findings, data.replaced || {});
  renderExtra(card);
  renderNotChecked(card.not_checked || []);
  renderDecision(card, data);
  renderRecord(data.record, card);
  renderTimings(card.timings_ms || {});
}

function chip(name, value, title) {
  return el("span", { class: "chip", title: title || null }, [el("b", { text: name }), value]);
}

function renderParsed(request) {
  const box = $("parsed");
  box.innerHTML = "";
  if (request.utterance) {
    const who = request.speaker ? `${personText(request.speaker)}: ` : "";
    box.append(el("div", { class: "who" }, `${who}“${request.utterance}”`));
  }
  box.append(el("span", { class: "chip" }, [el("b", { text: "change" }), request.type, epistemicBadge(request.epistemic)]));
  if (request.part) box.append(chip("part", `${request.part}`, label(request.part)));
  if (request.from_supplier) box.append(chip("from", label(request.from_supplier), request.from_supplier));
  if (request.to_supplier) box.append(chip("to", label(request.to_supplier), request.to_supplier));
  if (request.site) box.append(chip("site", label(request.site), request.site));
  if (request.new_material) box.append(chip("material", label(request.new_material), request.new_material));
  if (request.new_coating) box.append(chip("coating", label(request.new_coating), request.new_coating));
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
  const node = el("div", { class: `finding ${finding.severity}` }, [
    el("div", { class: "f-head" }, [
      el("span", { class: `sev ${finding.severity}` }, SEVERITY_TEXT[finding.severity] || finding.severity),
      el("span", { class: "rule-id" }, finding.rule),
      el("span", { class: "f-title" }, finding.title),
      epistemicBadge(finding.epistemic),
    ]),
    meta,
  ]);
  for (const item of replacedItems) node.append(renderReplaced(item));
  if ((finding.evidence || []).length) {
    const details = el("details", { class: "proof" }, [
      el("summary", {}, `Proof chain (${countLeaves(finding.evidence)} quotes)`),
      renderSteps(finding.evidence),
    ]);
    if (finding.severity === "blocker") details.open = false;
    node.append(details);
  }
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
  const past = card.past_decisions || card.precedents || [];
  if (past.length) {
    box.append(el("h2", {}, "Decided before"));
    for (const item of past) {
      box.append(el("div", { class: "finding info" }, [
        el("div", { class: "f-head" }, [el("span", { class: "rule-id" }, item.id || item.decision_id || ""),
                                         el("span", { class: "f-title" }, item.title || item.summary || item.outcome || "")]),
        el("div", { class: "f-meta" }, [item.date ? `${item.date} · ` : "", item.by ? personText(item.by) : "",
                                         item.reason ? ` · ${item.reason}` : ""]),
      ]));
    }
  }
  const maintenance = card.maintenance || [];
  if (maintenance.length) {
    box.append(el("h2", {}, "Memory maintenance"));
    for (const item of maintenance) {
      box.append(el("div", { class: "finding question" }, [
        el("div", { class: "f-head" }, [el("span", { class: "rule-id" }, item.kind || item.id || ""),
                                         el("span", { class: "f-title" }, item.title || item.summary || "")]),
      ]));
    }
  }
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
    el("dt", {}, "Decides"), el("dd", {}, el("b", {}, row.decider)),
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
    openModal(hitRow ? `Decision table — row ${hitRow} matched` : "Decision table", body);
  } catch (error) {
    setStatus(`Could not load the table: ${error.message}`, true);
  }
}

async function showRecords() {
  try {
    const data = await api("/api/records?limit=40");
    const head = el("tr", {}, ["Record", "Created (UTC)", "Change", "As of", "Verdict", "Row", "Rules fired", "Rules version"].map(function th(text) { return el("th", {}, text); }));
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
