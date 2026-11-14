// Header housekeeping for the minimal layout: tools that other modules append to the nav (offline toggle,
// presenter-mode button) are moved into the "..." menu. No behaviour changes.
"use strict";
(function minimalHeader() {
  function relocate() {
    const pop = document.getElementById("menu-pop");
    const nav = document.querySelector(".topnav");
    if (!pop || !nav) return;
    for (const id of ["offline-toggle", "demo-start"]) {
      const node = document.getElementById(id);
      if (node && node.parentNode !== pop) pop.append(node);
    }
  }
  window.addEventListener("DOMContentLoaded", function init() {
    relocate();
    new MutationObserver(relocate).observe(document.querySelector(".topnav"), { childList: true, subtree: true });
    document.addEventListener("click", function outside(event) {
      const menu = document.getElementById("more-menu");
      if (menu && menu.open && !menu.contains(event.target)) menu.open = false;
      else if (menu && menu.open && event.target.closest && event.target.closest(".menu-pop button")) menu.open = false;
    });
  });
})();
