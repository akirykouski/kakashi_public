// Meeting mode (#32): a transcript plays line by line; each line goes to POST /api/meeting/line. Lines the model
// flags as change proposals light up and their card appears on the right. Loaded after app.js and uses its
// helpers (el, label, personText, renderVerdict, renderFinding, state). Offline replay through Fallback.api.
"use strict";

const Meeting = (function makeMeeting() {
  const SPEEDS = [["0.5×", 2], ["1×", 1], ["2×", 0.5], ["4×", 0.25]];
  const BASE_DELAY_MS = 2600;
  const m = {
    lines: [], next: 0, playing: false, timer: null, busy: false, delayFactor: 1,
    processed: 0, flagged: 0, cards: [], recognizer: null, listening: false, built: false, spoken: 0,
  };

  function q(id) { return document.getElementById(id); }

  // ---- view switch ------------------------------------------------------------------------------------------

  function mountTabs() {
    const nav = document.querySelector(".topnav");
    const tabs = el("div", { class: "mt-tabs", role: "tablist" }, [
      el("button", { class: "mt-tab", id: "tab-meeting", onclick: function toMeeting() { show("meeting"); } }, "Meeting"),
      el("button", { class: "mt-tab", id: "tab-check", onclick: function toCheck() { show("check"); } }, "Check"),
    ]);
    nav.prepend(tabs);
    // Documents lives inside the Check view: opening it from Meeting switches there first
    const docs = q("open-documents");
    if (docs) docs.addEventListener("click", function toDocs() { if (document.body.classList.contains("view-meeting")) show("check"); });
    show(new URLSearchParams(location.search).get("view") === "check" ? "check" : "meeting");
  }

  function show(view) {
    const meeting = view === "meeting";
    document.querySelector("main").hidden = meeting;
    document.body.classList.toggle("view-meeting", meeting);
    q("tab-check").classList.toggle("active", !meeting);
    q("tab-meeting").classList.toggle("active", meeting);
    if (meeting && !m.built) build();
    if (!meeting && m.built) pause();
    const box = q("meeting-view");
    if (box) box.hidden = !meeting;
  }

  // ---- layout -----------------------------------------------------------------------------------------------

  function build() {
    m.built = true;
    const speed = el("select", { id: "mt-speed", "aria-label": "Speed",
      onchange: function setSpeed(event) { m.delayFactor = Number(event.target.value); } });
    for (const [text, factor] of SPEEDS) speed.append(el("option", { value: String(factor), text: text }));
    speed.value = "1";
    const view = el("section", { id: "meeting-view", class: "mt-view" }, [
      el("div", { class: "mt-bar" }, [
        el("div", { class: "mt-controls" }, [
          el("button", { id: "mt-mic", class: "mt-btn primary", onclick: toggleMic, title: "Speak: each finished sentence is checked like a line of the meeting (Chrome speech recognition)" }, "Talk live"),
          el("span", { id: "mt-listening", class: "mt-listening", hidden: true }, "\u25CF Listening"),
          el("button", { id: "mt-play", class: "mt-btn", onclick: togglePlay, title: "Replay the recorded change board meeting" }, "▶ Play recorded meeting"),
          el("button", { id: "mt-step", class: "mt-btn", onclick: stepOnce }, "Step"),
          el("button", { id: "mt-reset", class: "mt-btn", onclick: reset }, "Reset"),
          el("label", { class: "mt-speed" }, ["Speed ", speed]),
        ]),
        el("div", { id: "mt-counter", class: "mt-counter" }),
      ]),
      el("div", { id: "mt-status", class: "mt-status", hidden: true }),
      tryPanel(),
      el("div", { class: "mt-grid" }, [
        el("div", { class: "mt-transcript-wrap" }, [
          el("div", { class: "label" }, "Transcript"),
          el("p", { id: "mt-hint", class: "muted mt-hint" }, "Click Talk live and say a sentence, or click one of the sentences above."),
          el("ol", { id: "mt-transcript", class: "mt-transcript" }),
        ]),
        el("div", { class: "mt-cards-wrap" }, [
          el("div", { class: "label" }, "Change proposals · checked before the decision"),
          el("div", { id: "mt-cards", class: "mt-cards" }, [
            el("p", { class: "muted mt-empty", id: "mt-empty" }, "No change proposed yet. Ordinary lines pass; a line that proposes a change lights up here."),
          ]),
        ]),
      ]),
    ]);
    document.querySelector("main").after(view);
    m.loading = loadDemo();
  }

  // ---- "Try saying": sentences for jurors, verified against the running server (docs/demo-live/try-saying.json) --

  const TRY_SAYING = [
    { title: "Nothing to check", note: "Plain meeting talk. The product ignores it.", items: [
      { text: "Good morning, we have four items today.", speaker: "PER-CONTI" },
      { text: "Beinasco ran at ninety-two percent last week.", speaker: "PER-CONTI" },
      { text: "Let's take a five-minute break.", speaker: "PER-CONTI" },
    ] },
    { title: "A change worth checking", note: "Flagged, checked against plant documents, and a card appears.", items: [
      { text: "Bormida is two weeks late, let's take the BR-220 blanks from Chisone.", speaker: "PER-FERRI" },
      { text: "Let's switch the CL-115 coating to cheaper yellow chromate.", speaker: "PER-ROSSI" },
      { text: "Move the BR-220 final inspection to the new CMM.", speaker: "PER-ROMANO" },
    ] },
  ];

  function tryPanel() {
    const groups = TRY_SAYING.map(function group(g) {
      return el("div", { class: "mt-try-group" }, [
        el("div", { class: "mt-try-title" }, [el("b", {}, g.title), el("span", { class: "muted" }, ` · ${g.note}`)]),
        ...g.items.map(function item(entry) {
          return el("button", { class: "mt-try", title: "Click to send if the mic is off",
            onclick: function send() { sendTyped(entry); } }, `\u201C${entry.text}\u201D`);
        }),
      ]);
    });
    return el("div", { class: "mt-try-panel" }, [
      el("div", { class: "label" }, [
        "Try saying ", el("span", { class: "muted mt-try-hint" }, "click to send if the mic is off"),
      ]),
      el("div", { class: "mt-try-groups" }, groups),
    ]);
  }

  async function sendTyped(entry) {
    if (m.listening && m.recognizer) m.recognizer.stop();
    pause();
    if (m.next > 0) { reset(); m.spoken = 0; }
    status("");
    await addSpokenLine(entry.text, entry.speaker);
  }

  async function loadDemo() {
    try {
      const data = await Fallback.api("/api/meeting/demo");
      Object.assign(state.people, data.people || {});
      m.lines = data.lines || [];
      reset();
    } catch (error) {
      status(`Could not load the demo transcript: ${error.message}`, true);
    }
  }

  function status(text, isError) {
    const box = q("mt-status");
    box.hidden = !text;
    box.textContent = text || "";
    box.classList.toggle("error", Boolean(isError));
  }

  function offerRecorded(text) {
    const box = q("mt-status");
    box.hidden = false;
    box.classList.add("error");
    box.textContent = `${text} `;
    box.append(el("button", { class: "link", onclick: function playRecorded() { status(""); reset(); play(); } }, "Play the recorded meeting"));
  }

  function renderCounter() {
    q("mt-counter").innerHTML = "";
    q("mt-counter").append(
      el("span", {}, [el("b", {}, String(m.processed)), " lines"]),
      el("span", { class: "flag" }, [el("b", {}, String(m.flagged)), " flagged"]),
    );
  }

  function flaggedReason(data) {
    const request = (data.card && data.card.request) || data.request || {};
    const short = function shortOf(id) { return shortName(id); };
    if (request.part && (request.from_supplier || request.to_supplier)) {
      return `Change proposed: ${request.part}${request.from_supplier ? ` from ${short(request.from_supplier)}` : ""}${request.to_supplier ? ` to ${short(request.to_supplier)}` : ""}`;
    }
    if (request.part && request.new_coating) return `Change proposed: ${request.part} coating to ${label(request.new_coating)}`;
    if (request.part && request.new_material) return `Change proposed: ${request.part} material to ${label(request.new_material)}`;
    if (request.part) return `Change proposed: ${camelWords(request.type)} on ${request.part}`;
    return `Change proposed: ${data.reason || ""}`;
  }

  function speakerNode(id, you) {
    if (you) return el("span", { class: "mt-who" }, [el("span", { class: "mt-avatar", "aria-hidden": "true" }, "YO"), el("span", { class: "mt-name" }, "You")]);
    const person = state.people[id];
    if (!person) return el("span", { class: "mt-who" }, id || "Speaker");
    const initials = String(person.name || "").split(/\s+/).filter(Boolean).slice(0, 2)
      .map(function first(word) { return word[0]; }).join("").toUpperCase();
    return el("span", { class: "mt-who", title: person.role }, [
      el("span", { class: "mt-avatar", "aria-hidden": "true" }, initials),
      el("span", { class: "mt-name" }, person.name),
      el("span", { class: "mt-role" }, person.role),
    ]);
  }

  function lineNode(item, index) {
    const node = el("li", { class: "mt-line pending", id: `mt-line-${index}` }, [
      speakerNode(item.speaker, item.you),
      el("div", { class: "mt-text" }, item.text),
      el("div", { class: "mt-why" }),
    ]);
    return node;
  }

  function reset() {
    pause();
    m.next = 0;
    m.processed = 0;
    m.flagged = 0;
    m.cards = [];
    const list = q("mt-transcript");
    list.innerHTML = "";
    let session = null;
    m.lines.forEach(function add(item, index) {
      if (item.session && item.session !== session) {
        session = item.session;
        list.append(el("li", { class: "mt-session" }, item.session));
      }
      const node = lineNode(item, index);
      node.hidden = true;
      list.append(node);
    });
    q("mt-cards").innerHTML = "";
    q("mt-cards").append(el("p", { class: "muted mt-empty", id: "mt-empty" }, "No change proposed yet. Ordinary lines pass; a line that proposes a change lights up here."));
    q("mt-hint").hidden = false;
    document.dispatchEvent(new CustomEvent("mt:reset"));
    status("");
    renderCounter();
    renderSessions();
  }

  function renderSessions() {
    // a session header shows once its first line is visible
    for (const header of document.querySelectorAll(".mt-session")) {
      const next = header.nextElementSibling;
      header.hidden = Boolean(next && next.hidden);
    }
  }

  // ---- playback ---------------------------------------------------------------------------------------------

  function togglePlay() { if (m.playing) pause(); else play(); }

  function play() {
    if (m.next >= m.lines.length || m.spoken) { reset(); m.spoken = 0; }
    m.playing = true;
    q("mt-play").textContent = "❚❚ Pause";
    tick();
  }

  function pause() {
    m.playing = false;
    clearTimeout(m.timer);
    const button = q("mt-play");
    if (button) button.textContent = "▶ Play";
  }

  async function tick() {
    if (!m.playing) return;
    if (m.next >= m.lines.length) { pause(); status("End of the transcript."); return; }
    const flagged = await stepOnce();
    if (m.playing) m.timer = setTimeout(tick, BASE_DELAY_MS * m.delayFactor * (flagged ? 1.8 : 1));
  }

  async function stepOnce() {
    if (m.busy || m.next >= m.lines.length) return false;
    const index = m.next;
    m.next += 1;
    const node = q(`mt-line-${index}`);
    q("mt-hint").hidden = true;
    node.hidden = false;
    renderSessions();
    return processLine(m.lines[index], node);
  }

  // ---- one line ---------------------------------------------------------------------------------------------

  function pad(ms) { return new Promise(function wait(resolve) { setTimeout(resolve, ms); }); }
  function seconds(ms) { return `${(ms / 1000).toFixed(1)} s`; }

  function traceStep(text, detail) {
    const li = el("li", { class: "mt-step-on" }, [el("span", { class: "mt-tick", "aria-hidden": "true" }, "\u2713"), el("span", {}, text)]);
    if (detail) li.append(el("span", { class: "mt-step-time" }, ` (${detail})`));
    return li;
  }

  function resultText(card) {
    const who = card.decision && card.decision.decider ? capitalize(card.decision.decider) : "";
    if (card.verdict === "not_covered") return "No rule covers this. A person decides.";
    return verdictHeadline(card.verdict, card.findings, { decider: card.decision && card.decision.decider }) || who;
  }

  // The trail under a flagged line. Timings are the server's wall-clock for the model steps and the card's own
  // timings_ms.total for the document check; an offline replay has no timings, so the step shows none.
  async function drawTrace(node, data, trail, held) {
    const timing = data.timing_ms || {};
    const modelMs = (timing.classify || 0) + (timing.parse || 0);
    const checkMs = data.card && data.card.timings_ms ? data.card.timings_ms.total : null;
    held.remove();
    trail.append(traceStep(data.stage === "model" ? "change detected" : "change detected by code", data.stage === "model" && timing.classify !== undefined ? (modelMs < 100 ? "model, cached answer" : `model, ${seconds(modelMs)}`) : data.stage === "model" ? "model" : ""));
    await pad(280);
    if (data.card) {
      trail.append(traceStep("checked against plant documents", checkMs !== null ? `${checkMs < 10 ? checkMs.toFixed(1) : Math.round(checkMs)} ms` : ""));
      await pad(280);
      const final = traceStep(resultText(data.card), "");
      final.classList.add("mt-result", data.card.verdict);
      trail.append(final);
    } else {
      const final = traceStep(data.card_error || "Flagged, not checked", "");
      final.classList.add("mt-result");
      trail.append(final);
    }
    await pad(260);
  }

  async function processLine(item, node) {
    m.busy = true;
    node.className = "mt-line processing";
    node.scrollIntoView({ behavior: "smooth", block: "nearest" });
    const why = node.querySelector(".mt-why");
    why.textContent = "Checking against plant documents\u2026";
    const bar = el("div", { class: "mt-progress", "aria-hidden": "true" }, el("i"));
    why.after(bar);
    const old = node.querySelector(".mt-trace");
    if (old) old.remove();
    const trail = el("ol", { class: "mt-trace", "aria-label": "What happened to this sentence" });
    trail.append(traceStep("heard", ""));
    bar.before(trail);
    const held = el("li", { class: "mt-wait" }, "model reading the sentence\u2026");
    trail.append(held);
    let data = null;
    try {
      data = await Fallback.api("/api/meeting/line", { line: item.text, speaker: item.speaker, as_of: item.as_of });
      attachSources(data);
    } catch (error) {
      bar.remove();
      trail.remove();
      node.className = "mt-line unclassified";
      why.textContent = `not classified: ${error.message}`;
      if (item.you) offerRecorded(/offline/.test(error.message) ? "Live checking needs network (this sentence is not in the offline recording)." : "Could not check what you said (network or model credits).");
      m.busy = false;
      return false;
    }
    bar.remove();
    m.processed += 1;
    if (data.labels) Object.assign(state.labels, data.labels);
    if (!data.classified) {
      trail.remove();
      node.className = "mt-line unclassified";
      why.textContent = data.reason;
    } else if (!data.flagged) {
      trail.remove();
      node.className = `mt-line passed ${data.stage === "model" ? "by-model" : "by-code"}`;
      why.textContent = data.stage === "model" ? `model: ${data.reason}` : `skipped by code: ${data.reason}`;
      await recheckOpenCards(item, data, node);
    } else {
      m.flagged += 1;
      node.className = "mt-line flagged";
      why.textContent = flaggedReason(data);
      await drawTrace(node, data, trail, held);
      addCard(item, data, node);
      document.dispatchEvent(new CustomEvent("mt:flagged", { detail: { item: item, data: data } }));
    }
    renderCounter();
    m.busy = false;
    return Boolean(data.flagged);
  }

  // ---- cards ------------------------------------------------------------------------------------------------

  function addCard(item, data, node) {
    const empty = q("mt-empty");
    if (empty) empty.remove();
    const holder = el("article", { class: "mt-card fresh" });
    const entry = { item: item, data: data, holder: holder, node: node, history: [] };
    m.cards.push(entry);
    node.addEventListener("click", function focusCard() { flash(holder); });
    holder.addEventListener("click", function focusLine() { flash(node); });
    drawCard(entry);
    q("mt-cards").prepend(holder);
    setTimeout(function settle() { holder.classList.remove("fresh"); }, 1600);
  }

  function flash(target) {
    target.scrollIntoView({ behavior: "smooth", block: "nearest" });
    target.classList.remove("flash");
    void target.offsetWidth;
    target.classList.add("flash");
  }

  function requestChips(request) {
    const chips = [el("span", { class: "chip" }, [el("b", {}, "change"), request.type || "?"])];
    if (request.part) chips.push(el("span", { class: "chip", title: label(request.part) }, [el("b", {}, "part"), request.part]));
    if (request.from_supplier) chips.push(el("span", { class: "chip" }, [el("b", {}, "from"), label(request.from_supplier)]));
    if (request.to_supplier) chips.push(el("span", { class: "chip" }, [el("b", {}, "to"), label(request.to_supplier)]));
    if (request.new_coating) chips.push(el("span", { class: "chip" }, [el("b", {}, "coating"), label(request.new_coating)]));
    if (request.new_material) chips.push(el("span", { class: "chip" }, [el("b", {}, "material"), label(request.new_material)]));
    chips.push(el("span", { class: "chip" }, [el("b", {}, "as of"), request.as_of || ""]));
    for (const note of request.notes || []) {
      chips.push(el("span", { class: "chip noted", title: note.note }, [el("b", {}, note.field === "from_supplier" ? "from?" : "heard"), note.note]));
    }
    for (const item of request.unresolved || []) {
      chips.push(el("span", { class: "chip unresolved", title: item.reason }, [el("b", {}, `${item.field}?`), `“${item.text}” — ${item.reason}`]));
    }
    return el("div", { class: "mt-chips" }, chips);
  }

  function drawCard(entry) {
    const { item, data, holder } = entry;
    holder.innerHTML = "";
    holder.append(el("div", { class: "mt-quote" }, [speakerNode(item.speaker, item.you), el("span", {}, `“${item.text}”`)]));
    if (!data.card) {
      holder.append(el("div", { class: "verdict not_covered" }, el("div", { class: "big" }, "Flagged, no card")));
      holder.append(el("p", { class: "muted" }, data.card_error || "The line was flagged but not checked."));
      if (data.request) holder.append(requestChips(data.request));
      return;
    }
    const card = data.card;
    holder.append(requestChips(card.request));
    const verdict = el("div");
    renderVerdict(verdict, card.verdict, false, card.findings, verdictOpts(card, true));
    holder.append(verdict);
    for (const update of entry.history) holder.append(update);
    const findings = el("div", { class: "mt-findings" });
    for (const finding of card.findings.filter(function notInfo(f) { return f.severity !== "info"; })) {
      findings.append(renderFinding(finding, []));
    }
    if (!findings.childElementCount) findings.append(el("p", { class: "muted" }, "No rule fired."));
    holder.append(findings);
    const row = card.decision;
    const whyBox = el("div", { class: "mt-whybox" }, [
      el("div", { class: "label" }, "Decision table row that fired"),
      el("p", {}, [el("b", {}, `Row ${row.row_id}`), ` \u2014 ${(data.row_meaning || "").trim()}`]),
      el("div", { class: "label" }, "Proof, step by step: each blocker below opens to its quote and chain"),
    ]);
    holder.append(el("div", { class: "mt-decision" }, [
      el("span", { class: "mt-row" }, `Row ${row.row_id}`),
      el("span", {}, [el("span", { class: "muted" }, "Decides: "), el("b", {}, row.decider)]),
      row.allowed_actions.length ? el("span", { class: "muted" }, ` · ${row.allowed_actions.join("; ")}`) : null,
    ]));
    holder.append(el("button", { class: "mt-why-btn link", "aria-expanded": String(Boolean(entry.whyOpen)),
      onclick: function toggleWhy(event) { event.stopPropagation(); entry.whyOpen = !entry.whyOpen; applyWhy(entry); if (entry.whyOpen) holder.scrollIntoView({ behavior: "smooth", block: "start" }); } },
      entry.whyOpen ? "Hide" : "Why?"));
    holder.append(whyBox);
    applyWhy(entry);
  }

  function applyWhy(entry) {
    const holder = entry.holder;
    holder.classList.toggle("why", Boolean(entry.whyOpen));
    const button = holder.querySelector(".mt-why-btn");
    if (button) { button.textContent = entry.whyOpen ? "Hide" : "Why?"; button.setAttribute("aria-expanded", String(Boolean(entry.whyOpen))); }
    for (const proof of holder.querySelectorAll("details.proof")) proof.open = Boolean(entry.whyOpen);
  }

  function cardEntities(request) {
    const suppliers = [request.to_supplier, request.from_supplier].filter(Boolean);
    return suppliers.length ? suppliers : [request.part].filter(Boolean);
  }

  // A later line that names a supplier on an open card (or its part, when the card names no supplier) re-checks
  // that card on the later date. Same request, new date: the record shows why the answer moved.
  async function recheckOpenCards(item, data, node) {
    const named = new Set(data.mentions || []);
    for (const entry of m.cards) {
      if (!entry.data.card) continue;
      const request = entry.data.card.request;
      if (!item.as_of || !request.as_of || item.as_of <= request.as_of) continue;
      if (!cardEntities(request).some(function isNamed(id) { return named.has(id); })) continue;
      const before = entry.data.card;
      const body = { request: requestFields(request), as_of: item.as_of };
      let fresh = null;
      try {
        fresh = await Fallback.api("/api/check", body);
        attachSources(fresh);
      } catch (error) {
        continue;
      }
      if (fresh.labels) Object.assign(state.labels, fresh.labels);
      node.classList.add("rechecked");
      node.querySelector(".mt-why").textContent += ` · re-checked the ${label(request.to_supplier || request.part)} card as of ${item.as_of}`;
      entry.history = [updateNote(before, fresh.card, item)];
      entry.data = { ...entry.data, card: fresh.card };
      drawCard(entry);
      entry.holder.classList.add("fresh");
      setTimeout(function settle() { entry.holder.classList.remove("fresh"); }, 1600);
      q("mt-cards").prepend(entry.holder);
    }
  }

  function requestFields(request) {
    const fields = ["type", "part", "to_supplier", "from_supplier", "site", "at_supplier", "new_material",
                    "new_coating", "scope", "known_at", "utterance", "speaker"];
    const out = {};
    for (const field of fields) if (request[field]) out[field] = request[field];
    return out;
  }

  function updateNote(before, after, item) {
    const keyOf = function key(f) { return `${f.rule}:${f.severity}`; };
    const now = new Set(after.findings.map(keyOf));
    const was = new Set(before.findings.map(keyOf));
    const gone = before.findings.filter(function goneF(f) { return f.severity !== "info" && !now.has(keyOf(f)); });
    const added = after.findings.filter(function addedF(f) { return f.severity !== "info" && !was.has(keyOf(f)); });
    const count = function blockers(card) { return card.findings.filter(function b(f) { return f.severity === "blocker"; }).length; };
    const parts = [`Re-checked as of ${after.request.as_of} (was ${before.request.as_of}) after “${item.text}”`,
                   `blockers ${count(before)} → ${count(after)}`];
    const lines = gone.map(function g(f) { return el("div", { class: "mt-gone" }, [el("s", {}, `${f.rule} ${f.title}`), " — no longer fires"]); });
    lines.push(...added.map(function a(f) { return el("div", { class: "mt-added" }, `+ ${f.rule} ${f.title}`); }));
    return el("div", { class: "mt-update" }, [el("b", {}, parts.join(" · ")), ...lines]);
  }

  // ---- microphone (Web Speech API, Chrome) --------------------------------------------------------------------

  function interimNode() {
    let node = q("mt-interim");
    if (!node) {
      node = el("li", { id: "mt-interim", class: "mt-interim" });
      q("mt-transcript").append(node);
    }
    return node;
  }

  function stopListening() {
    m.listening = false;
    const mic = q("mt-mic");
    if (mic) { mic.classList.remove("on"); mic.textContent = "Talk live"; }
    q("mt-listening").hidden = true;
    const interim = q("mt-interim");
    if (interim) interim.remove();
  }

  function toggleMic() {
    const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!m.built) show("meeting");
    if (!Recognition) { offerRecorded("This browser has no speech recognition (use Chrome)."); return; }
    if (m.listening) { m.recognizer.stop(); return; }
    pause();
    status("");
    if (m.next > 0 || m.cards.length) reset();
    const recognizer = new Recognition();
    recognizer.lang = "en-GB";
    recognizer.continuous = true;
    recognizer.interimResults = true;
    recognizer.onresult = function onResult(event) {
      let interim = "";
      for (let i = event.resultIndex; i < event.results.length; i += 1) {
        const text = event.results[i][0].transcript.trim();
        if (event.results[i].isFinal) { if (text) addSpokenLine(text); } else interim += `${text} `;
      }
      const node = interimNode();
      node.textContent = interim.trim();
      node.hidden = !interim.trim();
    };
    recognizer.onend = function onEnd() { stopListening(); };
    recognizer.onerror = function onError(event) {
      if (event.error === "no-speech" || event.error === "aborted") return;
      const denied = event.error === "not-allowed" || event.error === "service-not-allowed";
      offerRecorded(denied ? "Microphone permission was denied." : `Speech recognition failed (${event.error}).`);
    };
    m.recognizer = recognizer;
    m.listening = true;
    q("mt-mic").classList.add("on");
    q("mt-mic").textContent = "\u25A0 Stop";
    q("mt-listening").hidden = false;
    try { recognizer.start(); } catch (error) { stopListening(); offerRecorded("Could not start the microphone."); }
  }

  async function addSpokenLine(text, speaker) {
    while (m.busy) await new Promise(function wait(resolve) { setTimeout(resolve, 150); });
    q("mt-hint").hidden = true;
    const who = speaker || "PER-FERRI";
    const item = { speaker: state.people[who] ? who : undefined, you: true, text: text, as_of: TODAY };
    m.spoken += 1;
    const node = lineNode(item, `mic-${m.spoken}`);
    const interim = q("mt-interim");
    if (interim) interim.before(node); else q("mt-transcript").append(node);
    node.scrollIntoView({ behavior: "smooth", block: "nearest" });
    await processLine(item, node);
  }

  // Public hooks for the presenter mode (demo.js): build + wait for the transcript, reset, step one line.
  function ready() { if (!m.built) build(); return m.loading; }
  function position() { return m.next; }

  document.addEventListener("DOMContentLoaded", function init() { mountTabs(); });
  return { show: show, ready: ready, say: sendTyped, toggleWhy: function toggleLastWhy() {
    const entry = m.cards[m.cards.length - 1];
    if (entry) { entry.whyOpen = !entry.whyOpen; applyWhy(entry); }
  }, reset: reset, step: stepOnce, position: position };
})();
