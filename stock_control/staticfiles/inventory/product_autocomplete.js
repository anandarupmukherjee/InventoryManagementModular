document.addEventListener("DOMContentLoaded", function () {
  const input = document.getElementById("id_product_autocomplete");
  const hiddenId = document.getElementById("id_product_dropdown"); // backend expects this name
  const suggestionsWrap = document.getElementById("product_suggestions");
  const datalist = document.getElementById("productOptions");

  if (!input || !hiddenId || !suggestionsWrap) return;

  let abortCtrl = null;
  let listEl = null;
  let activeIndex = -1;
  let lastResults = [];

  function clearList() {
    activeIndex = -1;
    if (listEl && listEl.parentNode) suggestionsWrap.removeChild(listEl);
    listEl = null;
  }

  function renderList(items) {
    clearList();
    lastResults = items;
    // Populate native datalist as a fallback/alternative UI
    if (datalist) {
      datalist.innerHTML = "";
      items.forEach((it) => {
        const opt = document.createElement("option");
        opt.value = `${it.name} — ${it.product_code}`;
        datalist.appendChild(opt);
      });
    }
    listEl = document.createElement("ul");
    if (!items.length) {
      const empty = document.createElement("div");
      empty.className = "autocomplete-empty";
      empty.textContent = "No matches";
      suggestionsWrap.appendChild(empty);
      setTimeout(() => empty.remove(), 1500);
      return;
    }
    items.forEach((it, idx) => {
      const li = document.createElement("li");
      li.textContent = `${it.name} — ${it.product_code}`;
      li.dataset.index = String(idx);
      li.addEventListener("mousedown", (e) => {
        e.preventDefault();
        const i = parseInt(li.dataset.index, 10);
        pick(lastResults[i]);
      });
      listEl.appendChild(li);
    });
    suggestionsWrap.appendChild(listEl);
  }

  function highlight(delta) {
    if (!listEl) return;
    const items = Array.from(listEl.children);
    if (!items.length) return;
    activeIndex = (activeIndex + delta + items.length) % items.length;
    items.forEach((el, i) => el.classList.toggle("active", i === activeIndex));
  }

  async function pick(item) {
    input.value = `${item.name} — ${item.product_code}`;
    hiddenId.value = item.id;
    clearList();
    // hydrate manual details
    try {
      const res = await fetch(`/data/get-product-by-id/?id=${encodeURIComponent(item.id)}`);
      if (!res.ok) return;
      const data = await res.json();
      const nameEl = document.getElementById("id_product_name");
      if (nameEl) nameEl.value = data.name || "";
      const ms = document.getElementById("manual-stock-display");
      if (ms) ms.textContent = data.current_stock ?? "";
      const mu = document.getElementById("manual-units-display");
      if (mu) mu.textContent = data.units_per_quantity ?? "";
      const up = document.getElementById("id_units_per_quantity");
      if (up) up.value = data.units_per_quantity ?? "";
      const barcodeManual = document.getElementById("id_barcode_manual");
      if (barcodeManual) barcodeManual.value = data.product_code || "";
      const volumeSection = document.getElementById("volume-withdrawal-section");
      if (volumeSection) volumeSection.style.display = (data.product_feature === "volume") ? "block" : "none";
    } catch {}
  }

  let debounceTimer = null;
  input.addEventListener("input", function () {
    const q = input.value.trim();
    hiddenId.value = ""; // reset selection when typing
    if (debounceTimer) clearTimeout(debounceTimer);
    if (!q || q.length < 2) { clearList(); return; }

    debounceTimer = setTimeout(async () => {
      try {
        if (abortCtrl) abortCtrl.abort();
        abortCtrl = new AbortController();
        const res = await fetch(`/data/search-products/?q=${encodeURIComponent(q)}&limit=12`, { signal: abortCtrl.signal });
        if (!res.ok) return;
        const data = await res.json();
        renderList(data.results || []);
      } catch (e) {
        // ignore aborts
      }
    }, 180);
  });

  input.addEventListener("keydown", function (e) {
    if (!listEl) return;
    if (e.key === "ArrowDown") { e.preventDefault(); highlight(+1); }
    else if (e.key === "ArrowUp") { e.preventDefault(); highlight(-1); }
    else if (e.key === "Enter") {
      const items = listEl ? Array.from(listEl.children) : [];
      if (items.length && activeIndex >= 0) {
        e.preventDefault();
        const i = parseInt(items[activeIndex].dataset.index, 10);
        if (!Number.isNaN(i) && lastResults[i]) pick(lastResults[i]);
      }
    } else if (e.key === "Escape") {
      clearList();
    }
  });

  document.addEventListener("click", function (e) {
    if (!suggestionsWrap.contains(e.target) && e.target !== input) {
      clearList();
    }
  });

  // When a user picks from native datalist, attempt to resolve to an id
  input.addEventListener("change", function () {
    const val = input.value.trim();
    const idx = lastResults.findIndex(r => `${r.name} — ${r.product_code}` === val);
    if (idx >= 0) {
      pick(lastResults[idx]);
    }
  });
});
