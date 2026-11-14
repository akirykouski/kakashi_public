// "DMN" tab of the decision-table view: the declared table exported as a standard OMG DMN 1.3 file
// (core/dmn.py, GET /api/table.dmn) and rendered with dmn-js, so the same rules open in Camunda Modeler, Drools or
// Trisotech. dmn-js is vendored (web/static/vendor/dmn-js-17.12.3, bpmn.io licence: the bpmn.io watermark the
// viewer draws must stay visible, so nothing here hides or overlaps it). Offline, the committed export
// web/static/dmn/decision.dmn is shown instead of the live route.
//
// Hook: app.js showTable() passes its table body through DmnTab.wrap(body, hitRow, dropRows).
"use strict";

const DmnTab = (function makeDmnTab() {
  const VENDOR = "/static/vendor/dmn-js-17.12.3/";
  const STATIC_EXPORT = "/static/dmn/decision.dmn";
  const STYLES = ["assets/diagram-js.css", "assets/dmn-js-shared.css", "assets/dmn-js-drd.css",
                  "assets/dmn-js-decision-table.css", "assets/dmn-js-literal-expression.css",
                  "assets/dmn-font/css/dmn.css"];
  let loading = null;

  function addStyle() {
    if (document.getElementById("dmn-tab-style")) return;
    const style = document.createElement("style");
    style.id = "dmn-tab-style";
    style.textContent = [
      ".dmn-tabs { display: flex; gap: 4px; border-bottom: 1px solid #d8dde6; margin: 4px 0 12px 0; }",
      ".dmn-tabs button { background: none; border: 0; border-bottom: 2px solid transparent; padding: 6px 12px; cursor: pointer; font-weight: 600; color: #4a5568; }",
      ".dmn-tabs button.on { border-bottom-color: var(--accent, #2456c9); color: var(--accent, #2456c9); }",
      ".dmn-bar { display: flex; flex-wrap: wrap; gap: 8px 14px; align-items: center; margin-bottom: 8px; }",
      ".dmn-canvas { position: relative; border: 1px solid #d8dde6; border-radius: 8px; background: #fff; min-height: 420px; overflow: auto; }",
      ".dmn-canvas .dmn-decision-table-container { font-size: 12px; }",
      ".dmn-canvas .dmn-hit td, .dmn-canvas td.dmn-hit { background: #fff4c2 !important; }",
      ".dmn-hit-note { background: #fff4c2; padding: 2px 8px; border-radius: 6px; font-weight: 600; }",
    ].join("\n");
    document.head.append(style);
  }

  function loadViewer() {
    if (window.DmnJS) return Promise.resolve(window.DmnJS);
    if (loading) return loading;
    for (const href of STYLES) {
      document.head.append(el("link", { rel: "stylesheet", href: VENDOR + href }));
    }
    loading = new Promise(function load(resolve, reject) {
      const script = el("script", { src: VENDOR + "dmn-viewer.production.min.js" });
      script.addEventListener("load", function loaded() { resolve(window.DmnJS); });
      script.addEventListener("error", function failed() { loading = null; reject(new Error("dmn-js did not load")); });
      document.head.append(script);
    });
    return loading;
  }

  function offline() {
    return typeof Fallback !== "undefined" && Fallback.isOffline && Fallback.isOffline();
  }

  function liveUrl(path, dropRows) {
    const drop = (dropRows || []).join(",");
    return drop ? `${path}${path.includes("?") ? "&" : "?"}drop=${encodeURIComponent(drop)}` : path;
  }

  async function fetchXml(dropRows) {
    if (!offline()) {
      try {
        const response = await fetch(liveUrl("/api/table?format=dmn", dropRows), { cache: "no-store" });
        if (response.ok) return { xml: await response.text(), source: "live", url: liveUrl("/api/table.dmn", dropRows) };
      } catch (error) {
        // fall through to the committed export
      }
    }
    const response = await fetch(STATIC_EXPORT, { cache: "no-store" });
    if (!response.ok) throw new Error("no DMN export on this machine (python -m core.dmn --out web/static/dmn/decision.dmn)");
    return { xml: await response.text(), source: "offline", url: STATIC_EXPORT };
  }

  function highlight(canvas, hitRow) {
    if (!hitRow) return 0;
    const id = `Rule_${hitRow}`;
    const cells = canvas.querySelectorAll(`[data-row-id="${id}"], [data-row-id^="${id}_any"]`);
    for (const cell of cells) {
      cell.classList.add("dmn-hit");
      if (cell.parentElement && cell.parentElement.tagName === "TR") cell.parentElement.classList.add("dmn-hit");
    }
    if (cells.length) cells[0].scrollIntoView({ block: "nearest" });
    return cells.length;
  }

  async function render(panel, hitRow, dropRows) {
    panel.innerHTML = "";
    const status = el("span", { class: "muted small" }, "loading the DMN export…");
    const download = el("a", { class: "link", href: liveUrl("/api/table.dmn", dropRows), download: "decision.dmn" }, "Download .dmn");
    const viewButtons = el("span", { class: "dmn-views" });
    const hitNote = el("span", {});
    panel.append(el("p", { class: "muted small" }, [
      "The same table as a standard OMG DMN 1.3 decision (hit policy FIRST, FEEL unary tests). Opens in Camunda Modeler, ",
      "Drools, Trisotech or any DMN 1.3 tool: the rules are not locked in this product.",
    ]));
    panel.append(el("div", { class: "dmn-bar" }, [download, viewButtons, hitNote, status]));
    const canvas = el("div", { class: "dmn-canvas" });
    panel.append(canvas);
    try {
      const [DmnJS, loaded] = await Promise.all([loadViewer(), fetchXml(dropRows)]);
      download.setAttribute("href", loaded.url);
      const viewer = new DmnJS({ container: canvas });
      await viewer.importXML(loaded.xml);
      const views = viewer.getViews();
      const tableView = views.find(function isTable(view) { return view.type === "decisionTable"; });
      const showView = async function showView(view) {
        await viewer.open(view);
        for (const button of viewButtons.querySelectorAll("button")) button.classList.toggle("on", button.dataset.type === view.type);
        if (view.type === "decisionTable") {
          const count = highlight(canvas, hitRow);
          hitNote.className = count ? "dmn-hit-note" : "";
          hitNote.textContent = hitRow ? (count ? `Matched row ${hitRow} highlighted` : `Matched row: ${hitRow}`) : "";
        } else {
          hitNote.textContent = hitRow ? `Matched row: ${hitRow}` : "";
        }
      };
      for (const view of views) {
        const name = view.type === "drd" ? "Diagram (rules version note)" : "Decision table";
        viewButtons.append(el("button", { class: "link", "data-type": view.type, onclick: function open() { showView(view); } }, name));
      }
      await showView(tableView || views[0]);
      status.textContent = loaded.source === "offline"
        ? "offline: showing the committed export web/static/dmn/decision.dmn (declared table, no in-memory edit)"
        : ((dropRows || []).length ? `exported live, edited in memory: ${dropRows.join(", ")} dropped` : "exported live from core/decision_table.yaml");
    } catch (error) {
      status.textContent = `Could not show the DMN model: ${error.message}`;
    }
  }

  function wrap(tableBody, hitRow, dropRows) {
    addStyle();
    const dmnPanel = el("div", { hidden: true });
    const tableTab = el("button", { class: "on" }, "Table");
    const dmnTab = el("button", {}, "DMN");
    let rendered = false;
    tableTab.addEventListener("click", function showTablePanel() {
      tableTab.classList.add("on"); dmnTab.classList.remove("on");
      tableBody.hidden = false; dmnPanel.hidden = true;
    });
    dmnTab.addEventListener("click", function showDmnPanel() {
      dmnTab.classList.add("on"); tableTab.classList.remove("on");
      tableBody.hidden = true; dmnPanel.hidden = false;
      if (!rendered) { rendered = true; render(dmnPanel, hitRow, dropRows); }
    });
    return el("div", {}, [el("div", { class: "dmn-tabs", role: "tablist" }, [tableTab, dmnTab]), tableBody, dmnPanel]);
  }

  return { wrap: wrap };
})();
