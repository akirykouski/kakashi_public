// "What would clear this" under each blocker and "Explain this decision" (two registers, copy button).
// Reads only card keys set by core/counterfactual.py and core/explain_text.py, and GET /api/explain for past
// records. Uses el(), $(), api(), openModal() and setStatus() from app.js. Written 14 Nov 2026 (ws/counterfactual).
"use strict";

window.Explain = (function makeExplain() {
  let current = null;

  function setCard(card) { current = card; }

  function itemFor(finding) {
    if (!current || !current.counterfactuals) return null;
    for (const item of current.counterfactuals) {
      if (item.blocker_rule === finding.rule && item.title === finding.title) return item;
    }
    return null;
  }

  function editList(edits) {
    const list = el("ul", { class: "cf-edits" });
    for (const edit of edits) {
      if (edit.replaced_by_next) continue;
      list.append(el("li", {}, [
        el("span", { class: "cf-tag" }, "hypothetical"), " ", edit.plain,
        el("div", { class: "mono small muted" }, `${edit.action} ${edit.triple}`),
      ]));
    }
    return list;
  }

  // Under a blocker / warning: one summary line, expandable to the hypothetical edits and the verified re-run.
  function lineFor(finding) {
    const item = itemFor(finding);
    if (!item) return null;
    if (!item.verified) {
      return el("div", { class: "cf-line cf-none" }, [el("b", {}, "What would clear this: "), item.reason || "no verified change"]);
    }
    const first = item.edits.filter(function shown(edit) { return !edit.replaced_by_next; })[0];
    const body = el("div", { class: "cf-body" }, [
      editList(item.edits),
      el("div", { class: "small" }, [
        `Verified by re-running the same check on a copy of the snapshot with this record: the finding goes; `,
        `table row would be ${item.row_if_applied}. `,
        item.clears && item.clears.length > 1 ? `Also clears: ${item.clears.join(", ")}. ` : "",
        "Nothing was written to the fact log.",
      ]),
    ]);
    for (const alternative of item.alternatives || []) {
      body.append(el("div", { class: "small" }, [el("b", {}, "Or: "), alternative.edits.filter(function shown(edit) { return !edit.replaced_by_next; }).map(function plain(edit) { return edit.plain; }).join("; "), ` (row ${alternative.row_if_applied})`]));
    }
    for (const effect of item.side_effects || []) {
      body.append(el("div", { class: "small note" }, `New in that case: ${effect.rule} ${effect.severity}: ${effect.title}`));
    }
    return el("details", { class: "cf-line" }, [
      el("summary", {}, [el("b", {}, "What would clear this: "), first ? first.plain : "see edits"]),
      body,
    ]);
  }

  function combinedLine(card) {
    const all = card.counterfactual_all;
    if (!all) return null;
    const verdicts = { blockers_found: "blockers found", needs_info: "needs information", no_blockers_found: "no blockers found", not_covered: "not covered" };
    const count = (all.changes || []).length;
    let text = `With these ${count} hypothetical change${count === 1 ? "" : "s"} the table row would be ${all.row_id}: ${verdicts[all.verdict] || all.verdict}`;
    if (all.verdict === "no_blockers_found") text += " — still not an approval";
    const left = Array.from(new Set((all.remaining || []).map(function rule(item) { return item.rule; })));
    if (left.length) text += ` (still open: ${left.join(", ")})`;
    return el("div", { class: "cf-all" }, text + ".");
  }

  function copyButton(textOf) {
    const button = el("button", { class: "link" }, "Copy");
    button.addEventListener("click", async function copy() {
      try {
        await navigator.clipboard.writeText(textOf());
        button.textContent = "Copied";
      } catch (error) {
        button.textContent = "Copy failed: select the text";
      }
      setTimeout(function reset() { button.textContent = "Copy"; }, 1500);
    });
    return button;
  }

  function registers(explanation, notes) {
    const box = el("div", { class: "explain" });
    const sections = [["customer", "For the customer / supplier"], ["auditor", "For the auditor"]];
    for (const [key, title] of sections) {
      box.append(el("div", { class: "ex-head" }, [el("h3", {}, title), copyButton(function text() { return explanation[key]; })]));
      box.append(el("pre", { class: "ex-text" }, explanation[key]));
    }
    for (const note of notes || []) box.append(el("div", { class: "note" }, note));
    box.append(el("p", { class: "muted small" }, "Built from the decision record and the card by fixed templates, no language model. Hypothetical changes are never written to the fact log."));
    return box;
  }

  function showCard(card) {
    if (!card.explanation) return;
    openModal(`Explain this decision — row ${card.explanation.row_id}`, registers(card.explanation));
  }

  // Under the decision record panel: the combined counterfactual and the explain button.
  function decorate(box, card) {
    const line = combinedLine(card);
    if (line) box.append(line);
    if (card.explanation) {
      box.append(el("button", { class: "explain-btn", onclick: function open() { showCard(card); } }, "Explain this decision"));
    }
  }

  async function showRecord(recordId) {
    try {
      const data = await api(`/api/explain?record_id=${encodeURIComponent(recordId)}`);
      openModal(`Explain ${recordId}`, registers(data.explanation, data.explanation.notes));
    } catch (error) {
      setStatus(`Could not explain ${recordId}: ${error.message}`, true);
    }
  }

  return { setCard: setCard, lineFor: lineFor, decorate: decorate, showRecord: showRecord };
})();
