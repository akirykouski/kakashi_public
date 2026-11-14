// Presenter mode: "▶ Demo" in the top bar (or ?demo=1). → / Space advance, ← goes back, Esc exits.
// Every step drives the real page through the same functions the buttons call (app.js, meeting.js, documents.js);
// nothing is screenshotted or faked. Each beat re-applies its whole state, so going back is safe. Offline replay
// (?offline=1&demo=1) works because every route used here is recorded by web/snapshot.py.
// Uses el, $, state, runCheck, runRuleChange, showTable, closeModal (app.js), Meeting (meeting.js), Docs (documents.js).
"use strict";

const Demo = (function makeDemo() {
  const LIVE_URL = "https://change-check.onrender.com";
  const REPO_URL = "https://github.com/akirykouski/kakashi_public";
  const DEVIATION_DOC = "DEV-AUR-26-044";
  const WRONG_PROPOSAL = "X-DEV-AUR-26-044-004";   // "Chisone needs customer approval for source changes": not in the email's intent
  const d = { on: false, beats: [], index: 0, busy: false, pending: null, docsDirty: false };

  // ---- small helpers ------------------------------------------------------------------------------------------

  function pause(ms) { return new Promise(function wait(resolve) { setTimeout(resolve, ms); }); }

  async function waitFor(test, timeoutMs) {
    const end = Date.now() + (timeoutMs || 4000);
    while (Date.now() < end) {
      const found = test();
      if (found) return found;
      await pause(80);
    }
    return null;
  }

  function clearFocus() {
    for (const node of document.querySelectorAll(".demo-focus")) node.classList.remove("demo-focus");
  }

  function focus(node, noScroll, block) {
    if (!node) return;
    node.classList.remove("demo-focus");
    void node.offsetWidth;
    node.classList.add("demo-focus");
    if (!noScroll) node.scrollIntoView({ behavior: "smooth", block: block || "center" });
  }

  function findingIn(root, rule, severity) {
    for (const node of (root || document).querySelectorAll(".finding")) {
      const id = node.querySelector(".rule-id");
      if (!id || id.textContent.trim() !== rule) continue;
      if (severity && !node.classList.contains(severity)) continue;
      return node;
    }
    return null;
  }

  function openProof(finding) {
    if (!finding) return null;
    const details = finding.querySelector("details.proof");
    if (details) details.open = true;
    return details;
  }

  function meetingCardFor(text) {
    for (const card of document.querySelectorAll("#mt-cards .mt-card")) {
      if (card.querySelector(".mt-quote") && card.querySelector(".mt-quote").textContent.includes(text)) return card;
    }
    return null;
  }

  function closeAnyModal() { if (!$("modal").hidden) closeModal(); }

  function hideDocuments() { $("documents-section").hidden = true; }

  // ---- page states (each idempotent) ------------------------------------------------------------------------------

  async function resetDocuments(force) {
    if (!force && !d.docsDirty) return;
    await Docs.reset();
    d.docsDirty = false;
  }

  // Bring the meeting to "first n lines processed". Forward steps animate; going back replays from the start.
  async function meetingAt(count, delayMs) {
    Meeting.show("meeting");
    await Meeting.ready();
    if (Meeting.position() > count) {
      Meeting.reset();
      delayMs = 0;
    }
    while (Meeting.position() < count) {
      await Meeting.step();
      if (delayMs) await pause(delayMs);
    }
  }

  function scenario(id) {
    return state.scenarios.find(function isIt(item) { return item.id === id; });
  }

  async function checkScenario(id) {
    Meeting.show("check");
    hideDocuments();
    const item = scenario(id);
    $("remark").value = (item && item.utterance) || "";
    $("as-of").value = (item && item.as_of) || TODAY;
    return runCheck({ scenario: id }, `Scenario “${item ? item.title : id}”`);
  }

  async function documentsAt(stage) {
    // 0 uploaded · 1 wrong fact rejected · 2 the rest accepted · 3 re-checked
    await resetDocuments(true);
    d.docsDirty = true;
    await checkScenario("main_after_audit");  // the change the email speaks to, as of today (not 5 Nov)
    $("documents-section").hidden = false;
    await Docs.loadDemo(DEVIATION_DOC);
    const proposals = (Docs.state.current && Docs.state.current.proposals) || [];
    if (stage >= 1) {
      const wrong = proposals.find(function isWrong(p) { return p.id === WRONG_PROPOSAL; });
      if (wrong) await Docs.review(wrong, "reject");
      await waitFor(function rejected() { return document.querySelector("#docs-view .doc-prop.st-rejected"); }, 2000);
    }
    if (stage >= 2) {
      const rest = proposals.filter(function isRest(p) { return p.kind !== "unclassified" && p.id !== WRONG_PROPOSAL; });
      await Docs.reviewMany(rest);
    }
    if (stage >= 2) await waitFor(function settled() { return !document.querySelector("#docs-view .doc-prop.st-proposed"); }, 2000);
    if (stage >= 3) await Docs.recheck();
  }

  function docProposal(id) {
    for (const node of document.querySelectorAll("#docs-view .doc-prop")) {
      if (node.querySelector(".mono") && Docs.state.current) {
        const proposal = Docs.state.current.proposals.find(function isIt(p) { return p.id === id; });
        if (proposal && node.textContent.includes(proposal.plain)) return node;
      }
    }
    return null;
  }

  // ---- the script --------------------------------------------------------------------------------------------------

  const STEPS = [
    { title: "Change Check", caption: "A supplier-quality meeting. The decision is about to be taken.",
      beats: [async function titleCard() {
        await resetDocuments(true);
        closeAnyModal();
        hideDocuments();
        await Meeting.ready();
        Meeting.reset();
        Meeting.show("meeting");
        showCard("title");
      }] },
    { title: "Meeting", caption: "One sentence in a meeting — the model only turns it into a typed change request.",
      beats: [async function meetingLine4() {
        await resetDocuments();
        await meetingAt(4, 450);
        focus($("mt-line-3"), true);
        const card = await waitFor(function card() { return meetingCardFor("Bormida is two weeks late"); });
        focus(card, false, "start");
      }] },
    { title: "Proof", caption: "Every step is a fact with a verbatim quote; the chain is inferred over the ontology.",
      beats: [
        async function proofR6() {
          // the meeting card is compact (no proofs): open the full card of the same request, same date
          await resetDocuments();
          await checkScenario("main");
          const finding = findingIn($("findings"), "R6", "blocker");
          openProof(finding);
          focus(finding);
        },
        async function proofR2() {
          await resetDocuments();
          await checkScenario("main");
          openProof(findingIn($("findings"), "R6", "blocker"));
          const finding = findingIn($("findings"), "R2", "blocker");
          openProof(finding);
          focus(finding);
        },
      ] },
    { title: "Decision table", caption: "A declared decision table decides what may be done and who decides. It never approves.",
      beats: [async function decisionRow() {
        await resetDocuments();
        await checkScenario("main");
        focus($("decision"));
      }] },
    { title: "Past decision", caption: "The company already decided this once — and why still holds.",
      beats: [async function pastDecision() {
        await resetDocuments();
        await checkScenario("main");
        focus(document.querySelector(".past-panel"));
      }] },
    { title: "New facts", caption: "New facts replace old ones by date and authority; history stays.",
      beats: [
        async function meetingLine8() {
          await resetDocuments();
          await meetingAt(8, 450);
          const card = meetingCardFor("Bormida is two weeks late");
          focus(card && (card.querySelector(".mt-update") || card));
        },
        async function afterAudit() {
          await resetDocuments();
          await checkScenario("main_after_audit");
          const finding = findingIn($("findings"), "R4");
          focus(finding);
        },
      ] },
    { title: "Documents", caption: "Documents become facts only after a person accepts them.",
      beats: [
        async function upload() {
          await documentsAt(0);
          focus($("docs-view"));
        },
        async function reject() {
          await documentsAt(1);
          const node = await waitFor(function rejected() {
            const found = docProposal(WRONG_PROPOSAL);
            return found && found.classList.contains("st-rejected") ? found : null;
          });
          focus(node || docProposal(WRONG_PROPOSAL));
        },
        async function accept() {
          await documentsAt(2);
          await waitFor(function settled() {
            return document.querySelector("#docs-view .doc-prop.st-accepted") && !document.querySelector("#docs-view .doc-prop.st-proposed");
          });
          focus(document.querySelector("#docs-view .doc-review"));
        },
        async function recheck() {
          await documentsAt(3);
          const finding = findingIn($("findings"), "R2");
          focus($("docs-diff"), true);
          focus(finding);
        },
      ] },
    { title: "The rule changed", caption: "Same question, different rules in force, different answer — and the record says which.",
      beats: [async function ruleChange() {
        Meeting.show("check");
        hideDocuments();
        closeAnyModal();
        await runRuleChange();
        focus($("compare"));
      }] },
    { title: "No rule", caption: "No rule covers it: a person decides, not the model.",
      beats: [async function meetingLine12() {
        closeAnyModal();
        await meetingAt(12, 450);
        focus($("mt-line-11"), true);
        focus(meetingCardFor("final inspection"), false, "start");
      }] },
    { title: "DMN", caption: "The rules are a standard DMN table — open them in any DMN engine.",
      beats: [
        async function coverage() {
          closeAnyModal();
          await checkScenario("main");
          focus(document.querySelector("#decision .coverage"));
        },
        async function table() {
          closeAnyModal();
          await checkScenario("main");
          await showTable(state.lastResponse.card.decision.row_id, []);
          focus(document.querySelector("#modal-body tr.hit"));
        },
        async function dmnTab() {
          closeAnyModal();
          await checkScenario("main");
          await showTable(state.lastResponse.card.decision.row_id, []);
          const tab = document.querySelectorAll("#modal-body .dmn-tabs button")[1];
          if (tab) tab.click();
          const download = await waitFor(function link() { return document.querySelector("#modal-body a[download]"); });
          focus(download, true);
        },
      ] },
    { title: "Explain", caption: "Each decision is reproducible and explainable.",
      beats: [
        async function whatClears() {
          closeAnyModal();
          await checkScenario("main");
          const line = document.querySelector("#findings details.cf-line");
          if (line) line.open = true;
          focus(line || document.querySelector("#findings .cf-line"));
        },
        async function explain() {
          closeAnyModal();
          await checkScenario("main");
          const button = document.querySelector("#record .explain-btn");
          if (button) button.click();
          const auditor = await waitFor(function pre() { return document.querySelectorAll("#modal-body .ex-text")[1]; });
          focus(auditor, true);
        },
      ] },
    { title: "Change Check", caption: "Inferred blockers: 0.90 recall vs 0.19 for retrieval. The model reads; the company's rules decide.",
      beats: [async function closing() {
        closeAnyModal();
        showCard("closing");
      }] },
  ];

  // ---- overlay cards -----------------------------------------------------------------------------------------------

  function showCard(kind) {
    hideCard();
    const content = kind === "title"
      ? [el("div", { class: "demo-card-kicker" }, "Change Check · Valsangone Componenti · change board"),
         el("h1", {}, "A supplier-quality meeting."),
         el("p", { class: "demo-card-lead" }, "The decision is about to be taken."),
         el("p", { class: "demo-card-small" }, "Fictional company, real code: every screen that follows is the live page.")]
      : [el("div", { class: "demo-card-kicker" }, "Pre-registered, synthetic data"),
         el("h1", {}, [el("span", { class: "demo-num" }, "0.90"), " recall of inferred blockers"]),
         el("p", { class: "demo-card-lead" }, ["vs ", el("b", {}, "0.19"), " for retrieval."]),
         el("p", { class: "demo-card-motto" }, "The model reads; the company's rules decide."),
         el("p", { class: "demo-card-links" }, [
           el("a", { href: LIVE_URL, target: "_blank", rel: "noopener" }, LIVE_URL.replace("https://", "")),
           el("span", {}, " · "),
           el("a", { href: REPO_URL, target: "_blank", rel: "noopener" }, REPO_URL.replace("https://", "")),
         ])];
    document.body.append(el("div", { id: "demo-card", class: `demo-card ${kind}` }, el("div", { class: "demo-card-box" }, content)));
  }

  function hideCard() {
    const card = $("demo-card");
    if (card) card.remove();
  }

  // ---- the caption bar ---------------------------------------------------------------------------------------------

  function buildBeats() {
    d.beats = [];
    STEPS.forEach(function add(step, stepIndex) {
      step.beats.forEach(function addBeat(apply, beatIndex) {
        d.beats.push({ step: stepIndex, beat: beatIndex, beatCount: step.beats.length, apply: apply });
      });
    });
  }

  function renderBar() {
    let bar = $("demo-bar");
    if (!bar) {
      bar = el("div", { id: "demo-bar", class: "demo-bar", role: "region", "aria-label": "Demo captions" }, [
        el("button", { class: "demo-nav", id: "demo-prev", title: "Back (←)", onclick: back }, "←"),
        el("div", { class: "demo-text" }, [
          el("div", { class: "demo-meta" }, [el("span", { id: "demo-count" }), el("span", { id: "demo-step-title" }), el("span", { id: "demo-beat" })]),
          el("div", { id: "demo-caption", class: "demo-caption" }),
        ]),
        el("button", { class: "demo-nav", id: "demo-next", title: "Next (→ or Space)", onclick: next }, "→"),
        el("button", { class: "demo-exit", title: "Exit the demo (Esc)", onclick: stop }, "Esc ✕"),
      ]);
      document.body.append(bar);
    }
    const beat = d.beats[d.index];
    const step = STEPS[beat.step];
    $("demo-count").textContent = `${beat.step}/${STEPS.length - 1}`;
    $("demo-step-title").textContent = step.title;
    $("demo-beat").textContent = beat.beatCount > 1 ? `· ${beat.beat + 1}/${beat.beatCount}` : "";
    $("demo-caption").textContent = step.caption;
    $("demo-prev").disabled = d.index === 0;
    $("demo-next").disabled = d.index === d.beats.length - 1;
    bar.classList.toggle("busy", d.busy);
  }

  async function go(index) {
    if (index < 0 || index >= d.beats.length) return;
    if (d.busy) { d.pending = index; return; }
    d.busy = true;
    d.index = index;
    renderBar();
    clearFocus();
    const beat = d.beats[index];
    hideCard();  // the title and closing beats draw it again
    try {
      await beat.apply();
    } catch (error) {
      console.warn(`demo step ${beat.step}.${beat.beat}: ${error.message}`);
    } finally {
      d.busy = false;
      renderBar();
    }
    if (d.pending !== null) {
      const wanted = d.pending;
      d.pending = null;
      if (wanted !== d.index) go(wanted);
    }
  }

  function next() { go((d.pending !== null ? d.pending : d.index) + 1); }
  function back() { go((d.pending !== null ? d.pending : d.index) - 1); }

  function start() {
    if (d.on) return;
    d.on = true;
    buildBeats();
    document.body.classList.add("demo-on");
    go(0);
  }

  function stop() {
    d.on = false;
    d.pending = null;
    document.body.classList.remove("demo-on");
    clearFocus();
    hideCard();
    const bar = $("demo-bar");
    if (bar) bar.remove();
  }

  function onKey(event) {
    if (!d.on) return;
    const tag = (event.target && event.target.tagName) || "";
    if (tag === "TEXTAREA" || tag === "INPUT" || tag === "SELECT") return;
    if (event.key === "ArrowRight" || event.key === " " || event.key === "PageDown") {
      event.preventDefault();
      next();
    } else if (event.key === "ArrowLeft" || event.key === "PageUp") {
      event.preventDefault();
      back();
    } else if (event.key === "Escape") {
      stop();
    }
  }

  function mountButton() {
    const nav = document.querySelector(".topnav");
    if (!nav || $("demo-start")) return;
    nav.append(el("button", { id: "demo-start", class: "demo-start", title: "Presenter mode: → / Space next, ← back, Esc exit",
                              onclick: function startDemo(event) { event.currentTarget.blur(); start(); } }, "▶ Demo"));
  }

  async function init() {
    mountButton();
    document.addEventListener("keydown", onKey, true);
    if (new URLSearchParams(location.search).get("demo") === "1") {
      await waitFor(function loaded() { return state.scenarios.length && Docs.state.demo.length; }, 8000);
      start();
    }
  }

  window.addEventListener("DOMContentLoaded", init);
  return { start: start, stop: stop, go: go, steps: STEPS };
})();
