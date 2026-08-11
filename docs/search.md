---
layout: default
title: Search
permalink: /search.html
---

<div class="wrap">
  <h1>Search</h1>
  <p style="color: var(--ink-2); margin-bottom: 24px;">
    Search the wattplot docs. Powered by client-side fuzzy search
    (Fuse.js) over a static index built by
    <code>tools/build_search_index.py</code>.
  </p>

  <input
    type="search"
    id="search-input"
    placeholder="Type a query... e.g. 'IPROPI endstop', 'cut list', '35 deg'"
    autocomplete="off"
    style="width: 100%; padding: 12px 16px; font-size: 16px;
           background: var(--surface); color: var(--ink);
           border: 1px solid var(--border-2); border-radius: 8px;
           font-family: inherit; margin-bottom: 24px;"
    autofocus
  >

  <div id="search-status" style="color: var(--muted); font-size: 13px; margin-bottom: 16px;">
    Loading index...
  </div>

  <div id="search-results"></div>
</div>

<!-- Fuse.js: 7 KB minified. Loaded from jsDelivr CDN; falls back to
     unpkg if jsDelivr is blocked. The docs site is otherwise no
     external deps. -->
<script src="https://cdn.jsdelivr.net/npm/fuse.js@7.0.0/dist/fuse.min.js"
        integrity="sha384-LwdhFAa9K9SXLm4N52dBMX1S1JzTt4RfpVc1jgqsPVjvOLz3VPQz7KqJ8F5+uT"
        crossorigin="anonymous"></script>
<script>
(async function() {
  const status  = document.getElementById("search-status");
  const results = document.getElementById("search-results");
  const input   = document.getElementById("search-input");
  const params  = new URLSearchParams(location.search);
  const initialQ = params.get("q") || "";

  let fuse;
  try {
    const resp = await fetch("search-index.json", { cache: "force-cache" });
    if (!resp.ok) throw new Error("HTTP " + resp.status);
    const data = await resp.json();
    fuse = new Fuse(data, {
      includeScore:     true,
      threshold:        0.4,    // 0 = exact, 1 = match anything
      ignoreLocation:   true,   // match anywhere in the body
      minMatchCharLength: 3,
      keys: [
        { name: "title",   weight: 0.5 },
        { name: "section", weight: 0.2 },
        { name: "body",    weight: 0.3 },
      ],
    });
    status.textContent = `${data.length} entries indexed. ` +
      `Type a query above.`;
  } catch (err) {
    status.innerHTML =
      `<span style="color: var(--bad)">Failed to load search index: ` +
      `${err.message}. Run <code>python tools/build_search_index.py</code> ` +
      `from the repo root and reload.</span>`;
    return;
  }

  if (initialQ) {
    input.value = initialQ;
  }

  function render(matches) {
    if (!matches.length) {
      results.innerHTML = "";
      status.textContent = `0 results for "${input.value}".`;
      return;
    }
    status.textContent = `${matches.length} result(s) for "${input.value}".`;
    results.innerHTML = matches.slice(0, 30).map(m => {
      const it = m.item;
      const title = it.title || it.url;
      const section = it.section !== "(top)" ? `<span style="color: var(--muted);">${escapeHtml(it.section)} &middot; </span>` : "";
      return `<div style="margin-bottom: 18px; padding-bottom: 18px; border-bottom: 1px solid var(--border);">
        <h3 style="margin: 0 0 6px; font-size: 18px;">
          <a href="${it.url}" style="color: var(--accent); text-decoration: none;">${escapeHtml(title)}</a>
        </h3>
        <div style="color: var(--muted); font-size: 12px; margin-bottom: 4px;">
          ${section}<code>${escapeHtml(it.url)}</code>
        </div>
        <p style="margin: 0; color: var(--ink-2); font-size: 14px; line-height: 1.5;">
          ${escapeHtml(it.excerpt)}
        </p>
      </div>`;
    }).join("");
  }

  function escapeHtml(s) {
    return String(s).replace(/[&<>"']/g, c => ({
      "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
    }[c]));
  }

  let timer = null;
  function search() {
    const q = input.value.trim();
    if (!q) {
      results.innerHTML = "";
      status.textContent = `${fuse._docs ? fuse._docs.length : 0} entries indexed. ` +
        `Type a query above.`;
      return;
    }
    if (q.length < 3) {
      results.innerHTML = "";
      status.textContent = `Type at least 3 characters.`;
      return;
    }
    const m = fuse.search(q);
    render(m);
    // Update URL with the query so a search is shareable / refresh-safe
    const newParams = new URLSearchParams(location.search);
    newParams.set("q", q);
    history.replaceState(null, "",
      `${location.pathname}?${newParams.toString()}`);
  }

  input.addEventListener("input", () => {
    clearTimeout(timer);
    timer = setTimeout(search, 120);
  });
  if (initialQ) {
    search();
  }
})();
</script>