// Live demo helpers: one-click remark presets, one-click card actions, a QR link. Every click calls the same
// functions and routes the existing buttons use (runCheck, compare, showTable, Docs, Meeting, Explain); nothing is
// faked and all of it replays offline (routes recorded by web/snapshot.py). Uses el, $, state, runCheck (app.js).
"use strict";

const Live = (function makeLive() {
  const SITE = "change-check.onrender.com";
  const AUDIT_DOC = "DEV-AUR-26-044";
  const WRONG_PROPOSAL = "X-DEV-AUR-26-044-004";
  const PRESETS = [
    { label: "Switch supplier", speaker: "PER-FERRI",
      remark: "Bormida is two weeks late. Let's take the BR-220 blanks from Chisone, same alloy." },
    { label: "Coating rule changed", speaker: "PER-ROSSI", rule: true,
      remark: "Can we switch BR-220 from anodising to trivalent conversion coating?" },
    { label: "New CMM", speaker: "PER-ROMANO",
      remark: "Let's move the BR-220 final inspection to the new CMM next week." },
    { label: "Delay delivery", speaker: "PER-FERRI",
      remark: "We postpone the BR-220 delivery to Aurelia by one week." },
  ];

  function pause(ms) { return new Promise(function wait(resolve) { setTimeout(resolve, ms); }); }
  function today() { return "2026-11-14"; }

  function showCheckTab() { if (window.Meeting) Meeting.show("check"); }

  async function runPreset(preset) {
    showCheckTab();
    $("documents-section").hidden = true;
    $("remark").value = preset.remark;
    $("speaker").value = preset.speaker;
    $("as-of").value = today();
    if (preset.rule) {
      await runRuleChange();
      $("compare").scrollIntoView({ behavior: "smooth", block: "start" });
    } else {
      await runCheck({ remark: preset.remark, speaker: preset.speaker, as_of: today() }, "Parsing the remark and checking");
    }
  }

  async function playMeeting() {
    Meeting.show("meeting");
    await Meeting.ready();
    Meeting.reset();
    const play = $("mt-play");
    if (play) play.click();
  }

  function mountPresets() {
    const strip = document.querySelector(".strip");
    if (!strip || $("live-presets")) return;
    strip.prepend(el("p", { class: "home-line" }, "Say a change. See what blocks it and who decides."));
    const row = el("div", { id: "live-presets", class: "live-presets" });
    for (const preset of PRESETS) {
      row.append(el("button", { class: "live-chip", title: preset.remark, onclick: function click() { runPreset(preset); } }, preset.label));
    }
    row.append(el("button", { class: "live-chip live-play", onclick: playMeeting }, "Play meeting"));
    row.append(el("select", { id: "more-select", class: "more-select", "aria-label": "More scenarios" }, [el("option", { value: "" }, "More\u2026")]));
    $("remark").closest(".remark-row").before(row);
    if (typeof renderDemoButtons === "function" && state.scenarios.length) renderDemoButtons();
  }

  function mountQr() {
    const top = document.querySelector(".top");
    if (!top || $("live-qr")) return;
    top.append(el("a", { id: "live-qr", class: "live-qr", href: `https://${SITE}`, target: "_blank", rel: "noopener",
                         title: "Scan to try it yourself" }, [
      el("img", { src: "/static/vendor/qr-change-check.svg", alt: `QR code for ${SITE}`, width: 36, height: 36 }),
      el("span", {}, SITE),
    ]));
  }

  // ---- card actions ------------------------------------------------------------------------------------------

  function firstBlocker() {
    return document.querySelector("#findings .finding.blocker") || document.querySelector("#findings .finding");
  }

  function why() {
    const finding = firstBlocker();
    if (!finding) return;
    const proof = finding.querySelector("details.proof");
    if (proof) proof.open = true;
    finding.scrollIntoView({ behavior: "smooth", block: "center" });
  }

  function clears() {
    const finding = firstBlocker();
    const line = finding && finding.querySelector("details.cf-line");
    if (line) { line.open = true; line.scrollIntoView({ behavior: "smooth", block: "center" }); }
  }

  function plain() {
    const button = document.querySelector("#record .explain-btn");
    if (button) button.click();
  }

  function openTable() {
    const response = state.lastResponse;
    if (response) showTable(response.card.decision.row_id, response.drop_rows || []);
  }

  async function dropRow(row) {
    const request = { ...state.lastRequest };
    closeModal();
    const select = $("drop-row");
    if (![...select.options].some(function has(option) { return option.value === row; })) select.append(el("option", { value: row, text: `drop ${row}` }));
    select.value = row;
    await compare({ request: request }, { request: request, drop_rows: [row] },
                  "Declared table (core/decision_table.yaml)", `Edited in memory: row ${row} removed`,
                  "Same request and facts. The fired row removed: a different row answers, and the rules version in the record changes.");
    $("compare").scrollIntoView({ behavior: "smooth", block: "start" });
  }

  function firedRow() { return state.lastResponse && state.lastResponse.card.decision.row_id; }

  async function ensureAuditCard() {
    const request = state.lastRequest;
    if (request && request.to_supplier && String(request.to_supplier).toLowerCase().includes("chisone")
        && request.part === "BR-220" && (request.as_of || today()) >= "2026-11-06") return;
    $("as-of").value = today();
    await runCheck({ scenario: "main_after_audit" }, "Checking the change after the re-audit");
  }

  async function addAudit() {
    await ensureAuditCard();
    $("documents-section").hidden = false;
    await Docs.loadDemo(AUDIT_DOC);
    $("documents-section").scrollIntoView({ behavior: "smooth" });
    mountDocsAction();
  }

  // After the audit email is read: one click accepts the right facts (rejects the wrong one) and re-checks.
  function mountDocsAction() {
    const view = $("docs-view");
    if (!view || $("live-accept")) return;
    view.before(el("button", { id: "live-accept", class: "live-big", onclick: acceptAndRecheck }, "Accept the facts and re-check"));
  }

  async function acceptAndRecheck() {
    const proposals = (Docs.state.current && Docs.state.current.proposals) || [];
    const wrong = proposals.find(function isWrong(p) { return p.id === WRONG_PROPOSAL; });
    if (wrong) await Docs.review(wrong, "reject");
    const rest = proposals.filter(function isRest(p) { return p.kind !== "unclassified" && p.id !== WRONG_PROPOSAL; });
    await Docs.reviewMany(rest);
    await pause(300);
    await Docs.recheck();
    $("verdict").scrollIntoView({ behavior: "smooth", block: "start" });
  }

  async function know8Nov() {
    if (!state.lastRequest) await runCheck({ scenario: "main_after_audit" }, "Checking");
    $("as-of").value = "2026-11-08";
    await runCheck({ request: { ...state.lastRequest, as_of: "2026-11-08" } }, "Checking as of 8 Nov");  // headline shows "As of 8 Nov"
    $("cmp-a").value = "2026-11-08";
    $("cmp-b").value = today();
    await runTimeTravel();
    $("compare").scrollIntoView({ behavior: "smooth", block: "start" });
  }

  function turnOff() {
    const row = firedRow();
    if (!row || row === "R0") { openTable(); return; }
    dropRow(row);
  }

  function openCompare() {
    const section = $("compare-section");
    section.hidden = false;
    section.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  function renderBar(data) {
    let bar = $("live-bar");
    if (!bar) {
      bar = el("div", { id: "live-bar", class: "live-bar" });
      $("verdict").after(bar);
    }
    const total = ((data.card.timings_ms || {}).total);
    const verdict = $("verdict");
    if (total !== undefined) {
      verdict.append(el("span", { class: "v-time", title: "Server time: snapshot, closure, rules" },
                        `checked in ${total < 10 ? total.toFixed(1) : Math.round(total)} ms`));
    }
    const button = function btn(text, action) { return el("button", { class: "live-btn", onclick: action }, text); };
    const row = firedRow();
    const more = el("details", { class: "live-more" }, [
      el("summary", { class: "live-btn" }, "More"),
      el("div", { class: "live-more-pop" }, [
        button("What would clear it", clears), button("Plain words", plain), button("Compare\u2026", openCompare)]),
    ]);
    bar.innerHTML = "";
    bar.append(
      button("Why", why),
      button(row && row !== "R0" ? `Turn ${row} off` : "Turn rule off", turnOff),
      button("Add audit email", addAudit),
      button("As of 8 Nov", know8Nov),
      more);
  }

  function resetDemo() {
    closeModal();
    if (window.Docs) Docs.reset();
    state.lastRequest = null;
    state.lastResponse = null;
    $("result").hidden = true;
    $("documents-section").hidden = true;
    $("compare-section").hidden = true;
    $("compare").innerHTML = "";
    if ($("drop-row")) $("drop-row").value = "D2";
    $("remark").value = "";
    $("as-of").value = today();
    $("cmp-a").value = "2026-11-05";
    $("cmp-b").value = today();
    setStatus("");
    document.body.classList.remove("has-result");
    if ($("live-accept")) $("live-accept").remove();
    showCheckTab();
    window.scrollTo(0, 0);
  }

  function mountReset() {
    const pop = $("menu-pop");
    if (!pop || $("reset-demo")) return;
    pop.append(el("button", { id: "reset-demo", class: "link", onclick: resetDemo }, "Reset demo"));
  }

  // The table modal: a one-click "turn this row off" in the modal head (not on the table).
  const baseOpenModal = window.openModal;
  window.openModal = function openModalClean() {
    for (const stale of document.querySelectorAll(".modal-head .live-drop")) stale.remove();
    return baseOpenModal.apply(this, arguments);
  };
  const baseShowTable = window.showTable;
  window.showTable = async function showTableWithDrop(hitRow, dropRows) {
    await baseShowTable(hitRow, dropRows);
    const head = document.querySelector(".modal-head");
    if (head && hitRow && hitRow !== "R0" && !head.querySelector(".live-drop")) {
      head.insertBefore(el("button", { class: "live-drop", onclick: function click() { dropRow(hitRow); } }, `Turn ${hitRow} off`), $("modal-close"));
    }
  };

  const baseRenderCard = window.renderCard;
  window.renderCard = function renderCardWithBar(data) {
    baseRenderCard(data);
    renderBar(data);
    document.body.classList.add("has-result");
  };

  const baseCompare = window.compare;
  window.compare = function compareShown() {
    $("compare-section").hidden = false;
    return baseCompare.apply(this, arguments);
  };

  document.addEventListener("click", function closeMore(event) {
    for (const more of document.querySelectorAll("details.live-more[open]")) {
      if (!more.contains(event.target) || event.target.closest(".live-more-pop button")) more.open = false;
    }
  });
  window.addEventListener("DOMContentLoaded", function init() { mountPresets(); mountQr(); mountReset(); });
  return { run: runPreset, presets: PRESETS };
})();
