// Bring your documents (ws/ingest): upload -> proposed facts with highlighted quotes -> a person accepts or
// rejects -> "Re-check the current change" shows what changed on the card. Server: web/documents.py.
// Uses el, $, state, renderCard, runCheck and epistemicBadge from app.js. Offline: replays
// /static/snapshot/documents.json (recorded by web/snapshot.py) for the two synthetic demo documents.
"use strict";

const Docs = (function makeDocs() {
  const docState = { demo: [], real: null, current: null, before: null, offline: null, offlineAccepted: {} };
  const SEVERITY = { blocker: 0, warning: 1, question: 2, info: 3 };

  function offline() { return typeof Fallback !== "undefined" && Fallback.isOffline(); }

  async function call(path, body) {
    if (offline()) return replay(path, body);
    const options = body === undefined ? {} : { method: "POST", headers: { "Content-Type": "application/json" },
                                                body: JSON.stringify(body) };
    let response;
    try {
      response = await fetch(path, options);
    } catch (networkError) {
      return replay(path, body);
    }
    const data = await response.json();
    if (!response.ok || data.error) throw new Error(data.error || `HTTP ${response.status}`);
    return data;
  }

  async function bundle() {
    if (!docState.offline) {
      const response = await fetch("/static/snapshot/documents.json", { cache: "no-store" });
      if (!response.ok) throw new Error("offline: the documents demo was not recorded (python -m web.snapshot)");
      docState.offline = await response.json();
    }
    return docState.offline;
  }

  async function replay(path, body) {
    const recorded = await bundle();
    if (path === "/api/documents/demo") return { demo: recorded.demo, real: recorded.real };
    if (path === "/api/documents/reset") { docState.offlineAccepted = {}; return { reset: true }; }
    if (path === "/api/documents" && body && body.demo && recorded.docs[body.demo]) {
      return JSON.parse(JSON.stringify(recorded.docs[body.demo].upload));
    }
    const match = /^\/api\/proposals\/([^/]+)\/(accept|reject)$/.exec(path);
    if (match) {
      docState.offlineAccepted[decodeURIComponent(match[1])] = match[2] === "accept" ? "accepted" : "rejected";
      return match[2] === "accept" ? { accepted: [decodeURIComponent(match[1])], contested: [] } : { rejected: [] };
    }
    if (path === "/api/proposals/accept") {
      for (const id of body.ids || []) docState.offlineAccepted[id] = "accepted";
      return { accepted: body.ids || [], contested: [] };
    }
    throw new Error("offline: documents other than the two recorded demo documents need the server and the model");
  }

  function setNote(text, isError) {
    const box = $("docs-status");
    box.hidden = !text;
    box.textContent = text || "";
    box.className = isError ? "status error" : "status";
  }

  // ---- input --------------------------------------------------------------------------------------------

  function renderInputs() {
    const demo = $("docs-demo");
    demo.innerHTML = "";
    for (const item of docState.demo) {
      demo.append(el("button", { class: "demo-btn", title: item.expect,
                                 onclick: function load() { upload({ demo: item.id }, item); } }, item.label));
    }
    if (docState.real) {
      demo.append(el("button", { class: "demo-btn live-only", title: docState.real.url,
                                 onclick: function loadReal() { upload({ real: true }, null); } },
                     ["Real public document (live: network + model key): ", docState.real.title]));
    }
  }

  async function upload(body, demoItem) {
    setNote(body.demo ? "Reading the document (recorded extraction)…" : "Reading the document (model extraction, may take ~30 s)…");
    try {
      if (demoItem) await ensureCurrentChange(demoItem.scenario);
      docState.before = state.lastResponse;
      const data = await call("/api/documents", body);
      docState.current = data;
      renderDocument();
      const extraction = data.extraction || {};
      const facts = data.proposals.filter(function isFact(p) { return p.kind !== "unclassified"; }).length;
      setNote(`${facts} facts proposed, ${data.proposals.length - facts} requirements not checkable, ` +
              `${(data.failed || []).length} rejected by the checks. Answers from: ${(extraction.answers_from || ["offline replay"]).join(", ")}. ` +
              "Nothing counts until a person accepts it.");
    } catch (error) {
      setNote(`Could not read the document: ${error.message}`, true);
    }
  }

  async function ensureCurrentChange(scenarioId) {
    // The demo documents speak to one change; check it first so the re-check has a "before".
    const wanted = state.scenarios.find(function isIt(item) { return item.id === scenarioId; });
    if (!wanted) return;
    const same = state.lastRequest && state.lastRequest.type === wanted.change.type &&
                 state.lastRequest.part === wanted.change.part &&
                 (state.lastRequest.to_supplier || "") === (wanted.change.to_supplier || "") &&
                 (state.lastRequest.new_coating || "") === (wanted.change.new_coating || "");
    if (!same) {
      $("remark").value = wanted.utterance || "";
      $("as-of").value = wanted.as_of || "2026-11-14";
      await runCheck({ scenario: wanted.id }, `Checking the current change “${wanted.title}”`);
    }
  }

  async function uploadPasted() {
    const text = $("docs-text").value;
    if (!text.trim()) { setNote("Paste a document first.", true); return; }
    await upload({ text: text, name: $("docs-name").value || "Pasted document", type: $("docs-type").value }, null);
  }

  async function uploadUrl() {
    const url = $("docs-url").value.trim();
    if (!url) { setNote("Give a URL first.", true); return; }
    await upload({ url: url, type: $("docs-type").value }, null);
  }

  async function uploadFile() {
    const file = $("docs-file").files[0];
    if (!file) { setNote("Choose a file first.", true); return; }
    if (file.size > 5 * 1024 * 1024) { setNote("The file is larger than 5 MB.", true); return; }
    if (offline()) { setNote("offline: uploading a file needs the server and the model", true); return; }
    setNote("Reading the file (model extraction, may take ~30 s)…");
    const form = new FormData();
    form.append("file", file);
    form.append("name", file.name);
    form.append("type", $("docs-type").value);
    try {
      docState.before = state.lastResponse;
      const response = await fetch("/api/documents", { method: "POST", body: form });
      const data = await response.json();
      if (!response.ok || data.error) throw new Error(data.error || `HTTP ${response.status}`);
      docState.current = data;
      renderDocument();
      setNote(`${data.proposals.length} items proposed from ${file.name}. Nothing counts until a person accepts it.`);
    } catch (error) {
      setNote(`Could not read the file: ${error.message}`, true);
    }
  }

  // ---- the document with highlighted quotes ---------------------------------------------------------------

  function statusOf(proposal) {
    return docState.offlineAccepted[proposal.id] || proposal.status;
  }

  function renderText(doc) {
    const text = doc.text;
    const marks = new Array(text.length);
    for (const proposal of doc.proposals) {
      if (statusOf(proposal) === "rejected" || statusOf(proposal) === "dismissed") continue;
      if (proposal.context_span) {
        for (let i = proposal.context_span[0]; i < proposal.context_span[1]; i += 1) {
          marks[i] = marks[i] || { quotes: [], context: false };
          marks[i].context = true;
        }
      }
      if (proposal.quote_span) {
        for (let i = proposal.quote_span[0]; i < proposal.quote_span[1]; i += 1) {
          marks[i] = marks[i] || { quotes: [], context: false };
          marks[i].quotes.push(proposal.id);
        }
      }
    }
    const box = el("pre", { class: "doc-text", id: "docs-text-view" });
    let start = 0;
    function keyAt(i) {
      const mark = marks[i];
      if (!mark) return "";
      return mark.quotes.length ? `q:${mark.quotes.join(",")}` : (mark.context ? "c" : "");
    }
    while (start < text.length) {
      const key = keyAt(start);
      let end = start + 1;
      while (end < text.length && keyAt(end) === key) end += 1;
      const piece = text.slice(start, end);
      if (!key) box.append(document.createTextNode(piece));
      else if (key === "c") box.append(el("mark", { class: "ctx", title: "context quote (the sentence that states the obligation)" }, piece));
      else {
        const ids = marks[start].quotes;
        box.append(el("mark", { class: "q", "data-ids": ids.join(" "),
                                title: ids.map(function plainOf(id) {
                                  const p = doc.proposals.find(function f(x) { return x.id === id; });
                                  return p ? p.plain : id;
                                }).join("\n") }, piece));
      }
      start = end;
    }
    return box;
  }

  function flash(proposal) {
    for (const mark of document.querySelectorAll("#docs-text-view mark.q")) {
      const ids = (mark.getAttribute("data-ids") || "").split(" ");
      if (ids.includes(proposal.id)) {
        mark.classList.add("flash");
        mark.scrollIntoView({ block: "center", behavior: "smooth" });
        setTimeout(function unflash() { mark.classList.remove("flash"); }, 1600);
      }
    }
  }

  function rankText(rank) {
    return { 1: "rank 1 · law / customer", 2: "rank 2 · controlled record", 3: "rank 3 · informal" }[rank] || `rank ${rank}`;
  }

  function renderProposal(proposal) {
    const status = statusOf(proposal);
    const actions = [];
    if (proposal.kind === "unclassified") {
      actions.push(el("span", { class: "doc-status notchecked-tag" }, "not checked: a person reads it"));
    } else if (status === "proposed") {
      actions.push(el("button", { class: "primary small-btn", onclick: function acceptIt() { review(proposal, "accept"); } }, "Accept"));
      actions.push(el("button", { class: "small-btn", onclick: function rejectIt() { review(proposal, "reject"); } }, "Reject"));
    } else {
      actions.push(el("span", { class: `doc-status st-${status}` }, status));
    }
    const triple = proposal.kind === "unclassified" ? null
      : el("div", { class: "mono small muted" }, `${proposal.s} · ${proposal.p} · ${proposal.o}`);
    return el("div", { class: `doc-prop st-${status}`, onclick: function show(event) {
      if (event.target.tagName !== "BUTTON") flash(proposal);
    } }, [
      el("div", { class: "doc-prop-head" }, [
        el("span", { class: "doc-plain" }, proposal.plain),
        epistemicBadge(proposal.epistemic),
        el("span", { class: "doc-rank" }, rankText(proposal.rank)),
      ]),
      triple,
      el("div", { class: "quote" }, `“${proposal.quote}”`),
      proposal.context_quote ? el("div", { class: "context-quote small muted" }, `under: “${proposal.context_quote}”`) : null,
      el("div", { class: "doc-actions" }, actions),
    ]);
  }

  function renderDocument() {
    const doc = docState.current;
    const box = $("docs-view");
    box.innerHTML = "";
    if (!doc) return;
    const header = doc.header || {};
    const facts = doc.proposals.filter(function isFact(p) { return p.kind !== "unclassified"; });
    const unclassified = doc.proposals.filter(function isU(p) { return p.kind === "unclassified"; });
    const open = facts.filter(function isOpen(p) { return statusOf(p) === "proposed"; });
    const reviewCol = el("div", { class: "doc-review" }, [
      el("h3", {}, "Proposed facts"),
      el("p", { class: "muted small" }, "Click a fact to see its quote in the document. Accepting runs the fact log's conflict check; a contradiction becomes “contested” with a question, never a silent overwrite."),
      open.length > 1 ? el("button", { class: "link", onclick: function acceptAll() { reviewMany(open); } }, `Accept all ${open.length} proposed facts`) : null,
      ...facts.map(renderProposal),
      unclassified.length ? el("h3", {}, "Not checked") : null,
      unclassified.length ? el("p", { class: "muted small" }, "Requirements that fit no predicate of the ontology. The reasoner never sees them; the card lists them under “Not checked”.") : null,
      ...unclassified.map(renderProposal),
      (doc.failed || []).length ? el("details", { class: "small" }, [
        el("summary", {}, `${doc.failed.length} model outputs rejected by the checks (never proposed)`),
        el("ul", {}, doc.failed.map(function li(item) {
          return el("li", {}, `${item.s} ${item.p} ${item.o}: ${item.reason}`);
        })),
      ]) : null,
      (doc.questions || []).length ? el("div", { class: "panel" }, [
        el("h3", {}, "Open questions"),
        ...doc.questions.map(function q(item) {
          return el("p", { class: "small" }, `${item.contested_record} contradicts ${item.current_record} (${item.class_name}). Decides: ${item.owner || "a person"}.`);
        }),
      ]) : null,
    ]);
    box.append(el("div", { class: "doc-head" }, [
      el("strong", {}, header.title || doc.id), " ",
      el("span", { class: "muted small" }, `${doc.id} · ${header.type || ""} · valid ${header.valid_from || "?"} → ${header.valid_to || "open end"}` +
                                            (header.supersedes ? ` · replaces ${header.supersedes}` : "")),
    ]));
    box.append(el("div", { class: "doc-grid" }, [el("div", { class: "doc-left" }, [renderText(doc)]), reviewCol]));
    renderRecheck();
  }

  async function review(proposal, action) {
    try {
      const result = await call(`/api/proposals/${encodeURIComponent(proposal.id)}/${action}`, { reviewer: reviewer() });
      afterReview(result);
    } catch (error) {
      setNote(`Could not ${action}: ${error.message}`, true);
    }
  }

  async function reviewMany(proposals) {
    try {
      const result = await call("/api/proposals/accept", { ids: proposals.map(function id(p) { return p.id; }), reviewer: reviewer() });
      afterReview(result);
    } catch (error) {
      setNote(`Could not accept: ${error.message}`, true);
    }
  }

  async function afterReview(result) {
    if (result.refused) setNote(`Refused: ${result.refused}`, true);
    else if ((result.contested || []).length) setNote(`Contested, not in force: ${result.message || ""} A question was opened.`, true);
    else setNote("Saved in the fact log. Re-check the current change to see what moved.");
    if (!offline()) {
      const all = await call("/api/proposals");
      docState.current = all.documents.find(function same(d) { return d.id === docState.current.id; }) || docState.current;
    }
    renderDocument();
  }

  function reviewer() {
    const speaker = $("speaker");
    return (speaker && speaker.value) || "reviewer";
  }

  // ---- re-check: what changed on the card -------------------------------------------------------------------

  function renderRecheck() {
    const box = $("docs-recheck");
    box.innerHTML = "";
    const request = state.lastRequest;
    box.append(el("div", { class: "inline" }, [
      el("button", { class: "primary", onclick: recheck, disabled: request ? null : "disabled" }, "Re-check the current change"),
      el("span", { class: "muted small" }, request ? ` ${request.type} · ${request.part || ""}${request.to_supplier ? " → " + request.to_supplier : ""}${request.new_coating ? " → " + request.new_coating : ""} · as of ${request.as_of || ""}`
                                                  : " Check a change first (top of the page)."),
    ]));
  }

  function findingKey(finding) { return `${finding.rule}|${finding.severity}|${finding.title}`; }

  async function recheck() {
    const before = docState.before || state.lastResponse;
    if (!before) { setNote("Check a change first.", true); return; }
    let after;
    if (offline()) {
      const recorded = await bundle();
      const entry = Object.values(recorded.docs).find(function sameDoc(d) { return docState.current && d.upload.id === docState.current.id; });
      if (!entry) { setNote("offline: no recorded re-check for this document", true); return; }
      after = entry.after;
      state.lastRequest = after.card.request;
      state.lastResponse = after;
      renderCard(after);
      setNote("Offline replay: the card recorded after accepting every proposed fact of this document.");
    } else {
      after = await runCheck({ request: before.card.request }, "Re-checking the current change with the accepted facts");
    }
    if (!after) return;
    const beforeKeys = new Set(before.card.findings.map(findingKey));
    const afterKeys = new Set(after.card.findings.map(findingKey));
    const added = after.card.findings.filter(function isNew(f) { return !beforeKeys.has(findingKey(f)); });
    const removed = before.card.findings.filter(function isGone(f) { return !afterKeys.has(findingKey(f)); });
    const line = function lineOf(finding, sign) {
      return el("li", { class: `diff-${sign === "+" ? "new" : "gone"}` }, [
        el("span", { class: `sev ${finding.severity}` }, finding.severity), ` ${sign} ${finding.rule}: ${finding.title}`]);
    };
    const box = $("docs-diff");
    box.innerHTML = "";
    box.append(el("div", { class: "panel" }, [
      el("h3", {}, "What changed on the card"),
      el("p", { class: "small" }, [`Verdict: ${before.card.verdict} → `, el("strong", {}, after.card.verdict)]),
      added.length || removed.length ? el("ul", { class: "diff-list" }, [
        ...removed.map(function r(f) { return line(f, "−"); }), ...added.map(function a(f) { return line(f, "+"); })])
        : el("p", { class: "muted small" }, "No finding changed."),
      el("p", { class: "muted small" }, "The full card is at the top of the page."),
    ]));
    docState.before = after;
  }

  async function resetDemo() {
    try {
      await call("/api/documents/reset", {});
      docState.current = null;
      docState.before = null;
      $("docs-view").innerHTML = "";
      $("docs-diff").innerHTML = "";
      renderRecheck();
      setNote("The fact log is back to the original company memory.");
    } catch (error) {
      setNote(`Could not reset: ${error.message}`, true);
    }
  }

  function toggle() {
    // a full-width tab: always opens (the Workspace tab goes back)
    const section = $("documents-section");
    if (!$("modal").hidden) closeModal();
    section.hidden = false;
    renderRecheck();
    window.scrollTo({ top: 0 });
  }

  async function init() {
    if (!$("documents-section")) return;
    $("open-documents").addEventListener("click", toggle);
    $("docs-paste-btn").addEventListener("click", uploadPasted);
    $("docs-url-btn").addEventListener("click", uploadUrl);
    $("docs-file-btn").addEventListener("click", uploadFile);
    $("docs-reset").addEventListener("click", resetDemo);
    try {
      const data = await call("/api/documents/demo");
      docState.demo = data.demo || [];
      docState.real = data.real || null;
    } catch (error) {
      setNote(`Demo documents unavailable: ${error.message}`, true);
    }
    renderInputs();
    renderRecheck();
  }

  // Public hooks for the presenter mode (demo.js): the same actions as the buttons, awaitable.
  function loadDemo(id) {
    const item = docState.demo.find(function isIt(entry) { return entry.id === id; });
    return upload({ demo: id }, item || null);
  }
  return { init: init, state: docState, reset: resetDemo, loadDemo: loadDemo, review: review, reviewMany: reviewMany,
           recheck: recheck };
})();

window.addEventListener("DOMContentLoaded", function startDocs() { Docs.init(); });
