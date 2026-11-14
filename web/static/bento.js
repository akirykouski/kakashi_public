// Bento layout for the Meeting view. Moves the existing Meeting nodes (mic, transcript, Try saying, cards) into
// tiles and fills the verdict / latency / rule / blockers tiles from the same response the card is drawn from
// ("mt:flagged" event from meeting.js). No new routes; offline replay is unchanged. Uses el, renderFinding, capitalize.
"use strict";

(function makeBento() {
  const g = function g(id) { return document.getElementById(id); };
  let tiles = {};
  let last = null;

  function tile(name, title, body, extra) {
    const node = el("section", { class: `bn bn-${name}`, "data-tile": name }, [
      el("div", { class: "bn-head" }, [el("span", { class: "bn-title" }, title), extra || null]),
      body,
    ]);
    tiles[name] = node;
    return node;
  }

  const fmtMs = function fmtMs(ms) { return ms < 10 ? ms.toFixed(1) : String(Math.round(ms)); };

  function build() {
    const view = g("meeting-view");
    if (!view || view.querySelector(".bento")) return;
    const controls = view.querySelector(".mt-controls");
    const counter = g("mt-counter");
    const tryPanel = view.querySelector(".mt-try-panel");
    const transcriptWrap = view.querySelector(".mt-transcript-wrap");
    const cardsWrap = view.querySelector(".mt-cards-wrap");
    const bar = view.querySelector(".mt-bar");

    const level = el("div", { class: "bn-level", id: "bn-level", "aria-hidden": "true" },
      [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11].map(function b(i) { return el("i", { style: `--i:${i}` }); }));
    const caption = el("p", { class: "bn-caption empty", id: "bn-caption" }, "Say a change…");
    const talkBody = el("div", { class: "bn-talk-body" }, [
      el("div", { class: "bn-talk-top" }, [level]),
      caption,
    ]);
    const talk = tile("talk", "Talk live", talkBody, el("span", { class: "bn-state", id: "bn-state" }, "Idle"));
    talk.insertBefore(controls, talkBody);

    const why = el("button", { class: "bn-why", id: "bn-why", disabled: true, onclick: openSheet }, "Why?");
    const verdict = tile("verdict", "Verdict",
      el("div", { id: "bn-verdict", class: "bn-verdict empty" }, [
        el("div", { class: "bn-big" }, "Say a change…"),
        el("div", { class: "bn-sub" }, "The verdict and who decides appear here."),
      ]), why);

    const latency = tile("latency", "Latency", el("div", { class: "bn-lat", id: "bn-lat" }, [
      el("div", {}, [el("div", { class: "bn-num", id: "bn-detect" }, "–"), el("div", { class: "bn-cap" }, "change detected")]),
      el("div", {}, [el("div", { class: "bn-num", id: "bn-check" }, "–"), el("div", { class: "bn-cap" }, "checked")]),
    ]));

    const rule = tile("rule", "Rule that fired", el("div", { class: "bn-rule empty", id: "bn-rule" }, "No rule yet."));

    const blockers = tile("blockers", "Blockers",
      el("div", { class: "bn-blockers empty", id: "bn-blockers" }, "Nothing to check yet. A flagged line lists its blockers here."));

    const trans = tile("transcript", "Transcript", transcriptWrap, counter);
    transcriptWrap.querySelector(".label").remove();
    const tryTile = tile("try", "Try saying", tryPanel);
    tryPanel.querySelector(".label").remove();

    const sheet = el("div", { class: "bn-sheet", id: "bn-sheet", hidden: true, onclick: function bg(e) { if (e.target === sheet) closeSheet(); } }, [
      el("div", { class: "bn-sheet-box", role: "dialog", "aria-modal": "true", "aria-label": "Proof chain" }, [
        el("div", { class: "bn-head" }, [el("span", { class: "bn-title" }, "Why? Proof chain"),
          el("button", { class: "bn-close", onclick: closeSheet }, "Close")]),
        cardsWrap,
      ]),
    ]);
    cardsWrap.querySelector(".label").remove();

    const grid = el("div", { class: "bento" }, [talk, tryTile, verdict, blockers, trans, latency, rule]);
    bar.replaceWith(grid);
    view.append(sheet);
    view.querySelector(".mt-grid").remove();
    document.body.classList.add("bento-on");
    watchMic();
    watchCaption();
    document.addEventListener("keydown", function esc(e) { if (e.key === "Escape") closeSheet(); });
  }

  function openSheet() {
    const holder = document.querySelector("#mt-cards .mt-card");
    if (holder && !holder.classList.contains("why")) Meeting.toggleWhy();
    g("bn-sheet").hidden = false;
  }
  function closeSheet() { g("bn-sheet").hidden = true; }

  // ---- mic level: real input level when the browser gives us the stream, else a CSS pulse -------------------
  let audio = null;
  function stopAudio() {
    if (!audio) return;
    cancelAnimationFrame(audio.raf);
    audio.stream.getTracks().forEach(function stop(t) { t.stop(); });
    try { audio.ctx.close(); } catch (e) { /* ignore */ }
    audio = null;
    for (const b of g("bn-level").children) b.style.removeProperty("--h");
  }
  async function startAudio() {
    if (audio || !navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) return;
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const ctx = new (window.AudioContext || window.webkitAudioContext)();
      const an = ctx.createAnalyser();
      an.fftSize = 64;
      ctx.createMediaStreamSource(stream).connect(an);
      const data = new Uint8Array(an.frequencyBinCount);
      audio = { stream: stream, ctx: ctx, raf: 0 };
      const bars = [...g("bn-level").children];
      const loop = function loop() {
        an.getByteFrequencyData(data);
        bars.forEach(function set(b, i) { b.style.setProperty("--h", `${Math.max(8, Math.round(data[i + 1] / 255 * 100))}%`); });
        audio.raf = requestAnimationFrame(loop);
      };
      loop();
      g("bn-level").classList.add("real");
    } catch (e) { g("bn-level").classList.remove("real"); }
  }
  function watchMic() {
    const mic = g("mt-mic");
    const apply = function apply() {
      const on = mic.classList.contains("on");
      document.body.classList.toggle("bn-listening", on);
      g("bn-state").textContent = on ? "Listening" : "Idle";
      if (on) startAudio(); else stopAudio();
    };
    new MutationObserver(apply).observe(mic, { attributes: true, attributeFilter: ["class"] });
  }

  // ---- caption: interim text while speaking, else the last heard line ----------------------------------------
  function setCaption(text, interim) {
    const c = g("bn-caption");
    c.textContent = text || "Say a change…";
    c.classList.toggle("empty", !text);
    c.classList.toggle("interim", Boolean(interim));
  }
  function watchCaption() {
    const list = g("mt-transcript");
    new MutationObserver(function changed() {
      const interim = g("mt-interim");
      if (interim && interim.textContent.trim()) { setCaption(interim.textContent.trim(), true); return; }
      const lines = [...list.querySelectorAll(".mt-line:not([hidden]) .mt-text")];
      if (lines.length) setCaption(lines[lines.length - 1].textContent, false);
    }).observe(list, { childList: true, subtree: true, characterData: true, attributes: true, attributeFilter: ["hidden"] });
  }

  // ---- fill the tiles from a flagged response -----------------------------------------------------------------
  function status(card) {
    if (card.verdict === "blockers_found") return "red";
    if (card.verdict === "no_blockers_found") return "green";
    return "amber";
  }

  function fill(detail) {
    const data = detail.data;
    const card = data.card;
    last = detail;
    const v = g("bn-verdict");
    if (!card) {
      v.className = "bn-verdict amber";
      v.replaceChildren(el("div", { class: "bn-big" }, "Flagged, not checked"), el("div", { class: "bn-sub" }, data.card_error || ""));
      return;
    }
    const decider = card.decision && card.decision.decider;
    const blockers = card.findings.filter(function b(f) { return f.severity === "blocker"; });
    let big;
    if (card.verdict === "not_covered") big = "No rule covers this. A person decides.";
    else if (card.verdict === "blockers_found") big = `${blockers.length} blocker${blockers.length === 1 ? "" : "s"}. ${capitalize(decider || "A person")} decides.`;
    else big = verdictHeadline(card.verdict, card.findings, { decider: decider });
    const req = card.request || {};
    v.className = `bn-verdict ${status(card)}`;
    v.replaceChildren(el("div", { class: "bn-big" }, big),
      el("div", { class: "bn-sub" }, `“${detail.item.text}”`));
    g("bn-why").disabled = false;

    const t = data.timing_ms || {};
    const modelMs = (t.classify || 0) + (t.parse || 0);
    const detect = g("bn-detect");
    if (data.stage === "model" && t.classify !== undefined) detect.replaceChildren(`${(modelMs / 1000).toFixed(1)}`, el("small", {}, " s"));
    else detect.replaceChildren("code", el("small", {}, ""));
    const total = card.timings_ms && card.timings_ms.total;
    const chk = g("bn-check");
    if (total !== undefined && total !== null) chk.replaceChildren(fmtMs(total), el("small", {}, " ms"));
    else chk.replaceChildren("–");

    const row = card.decision || {};
    g("bn-rule").className = "bn-rule";
    g("bn-rule").replaceChildren(
      el("div", { class: "bn-rule-top" }, [el("span", { class: "bn-id" }, row.row_id || "?"),
        el("span", { class: "bn-meaning" }, (data.row_meaning || "").trim() || "No meaning recorded.")]),
      row.allowed_actions && row.allowed_actions.length
        ? el("ul", { class: "bn-actions" }, row.allowed_actions.map(function a(x) { return el("li", {}, x); }))
        : el("div", { class: "bn-cap" }, "No action is allowed by this row."));

    const box = g("bn-blockers");
    const shown = card.findings.filter(function f(x) { return x.severity !== "info"; });
    box.className = "bn-blockers";
    box.replaceChildren();
    if (!shown.length) { box.className = "bn-blockers empty"; box.append("No rule fired. Not an approval."); return; }
    for (const f of shown) box.append(renderFinding(f, []));
  }

  function clear() {
    last = null;
    const v = g("bn-verdict");
    if (!v) return;
    v.className = "bn-verdict empty";
    v.replaceChildren(el("div", { class: "bn-big" }, "Say a change…"), el("div", { class: "bn-sub" }, "The verdict and who decides appear here."));
    g("bn-why").disabled = true;
    g("bn-detect").textContent = "–";
    g("bn-check").textContent = "–";
    g("bn-rule").className = "bn-rule empty";
    g("bn-rule").textContent = "No rule yet.";
    g("bn-blockers").className = "bn-blockers empty";
    g("bn-blockers").textContent = "Nothing to check yet. A flagged line lists its blockers here.";
    setCaption("", false);
    closeSheet();
  }

  document.addEventListener("mt:flagged", function onFlag(e) { if (g("bn-verdict")) fill(e.detail); });
  document.addEventListener("mt:reset", clear);
  window.addEventListener("DOMContentLoaded", build);
})();
