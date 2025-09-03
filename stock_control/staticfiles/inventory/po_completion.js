document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("po-completion-form");
  if (!form) {
    console.warn("❌ Completion form not found");
    return;
  }
  // Toggle single vs multiple lots
  const singleSection = document.getElementById("single-lot-section");
  const multiSection = document.getElementById("multi-lot-section");
  const singleQtyWrap = document.getElementById("single-qty-wrap");
  const addLotRowBtn = document.getElementById("add_lot_row");
  const lotsContainer = document.getElementById("lots_container");
  const orderedQtyHint = document.getElementById("ordered_qty_hint");
  const multiTotalQty = document.getElementById("multi_total_qty");
  const multiQtyWarning = document.getElementById("multi_qty_warning");

  function updateLotModeUI() {
    const mode = document.querySelector('input[name="lot_mode"]:checked')?.value || 'single';
    if (mode === 'single') {
      singleSection.style.display = '';
      multiSection.style.display = 'none';
      singleQtyWrap.style.display = '';
    } else {
      singleSection.style.display = 'none';
      multiSection.style.display = '';
      singleQtyWrap.style.display = 'none';
      // Ensure at least one row exists
      if (!lotsContainer.children.length) addLotRow();
      computeMultiTotals();
    }
  }
  document.querySelectorAll('input[name="lot_mode"]').forEach(r => r.addEventListener('change', updateLotModeUI));

  function addLotRow() {
    const row = document.createElement('div');
    row.className = 'lot-row';
    row.style.display = 'grid';
    row.style.gridTemplateColumns = '1fr 1fr 1fr auto';
    row.style.gap = '8px';
    row.style.marginBottom = '10px';
    row.innerHTML = `
      <input type="text" name="multi_lot_number[]" placeholder="Lot number" class="form-control" required>
      <input type="date" name="multi_expiry_date[]" class="form-control" required>
      <input type="number" name="multi_quantity[]" min="1" class="form-control lot-qty" placeholder="Qty" required>
      <button type="button" class="btn btn-small btn-danger remove-lot-row">✕</button>
    `;
    lotsContainer.appendChild(row);
    const qty = row.querySelector('.lot-qty');
    qty?.addEventListener('input', computeMultiTotals);
    row.querySelector('.remove-lot-row')?.addEventListener('click', () => { row.remove(); computeMultiTotals(); });
    computeMultiTotals();
  }

  addLotRowBtn?.addEventListener('click', addLotRow);

  function computeMultiTotals() {
    const qtyInputs = lotsContainer.querySelectorAll('.lot-qty');
    let total = 0;
    qtyInputs.forEach(inp => {
      const v = parseInt(inp.value, 10);
      if (!isNaN(v)) total += v;
    });
    if (multiTotalQty) multiTotalQty.textContent = String(total);
    const ordered = parseInt((document.getElementById('id_quantity_ordered')?.value || orderedQtyHint?.textContent || '0'), 10) || 0;
    if (orderedQtyHint) orderedQtyHint.textContent = String(ordered);
    if (multiQtyWarning) {
      if (ordered && total !== ordered) {
        multiQtyWarning.textContent = `⚠ quantities differ (ordered ${ordered})`;
        multiQtyWarning.style.color = '#b45309';
      } else {
        multiQtyWarning.textContent = '';
      }
    }
  }

  // Initialize UI state on load
  updateLotModeUI();

  // 🖱️ Fill form when 'Complete' button is clicked
  document.querySelectorAll(".fill-form-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      const code = btn.dataset.productCode;
      const name = btn.dataset.productName;
      const quantity = btn.dataset.quantity;
      const poRef = btn.dataset.poRef || '';

      document.getElementById("id_product_code").value = code;
      const nameEl = document.getElementById("id_product_name");
      if (nameEl) nameEl.value = name || "";
      const poRefEl = document.getElementById("id_po_reference");
      if (poRefEl) poRefEl.value = poRef;
      document.getElementById("id_quantity_ordered").value = quantity;
      document.getElementById("id_status").value = "Delivered";
      if (orderedQtyHint) orderedQtyHint.textContent = String(quantity || 0);
      // We leave product name as-is; view may populate by code if needed
    });
  });

  // 🚀 AJAX submit form + update table
  form.addEventListener("submit", async (e) => {
    e.preventDefault();

    const formData = new FormData(form);
    const lotMode = document.querySelector('input[name="lot_mode"]:checked')?.value || 'single';
    formData.append('lot_mode', lotMode);
    if (lotMode === 'multiple') {
      // Ensure multiple rows exist
      if (!lotsContainer.children.length) addLotRow();
    }
    const productCode = document.getElementById("id_product_code").value.trim();

    try {
      const res = await fetch(window.location.href, {
        method: "POST",
        body: formData,
        headers: {
          "X-Requested-With": "XMLHttpRequest"
        }
      });

      if (!res.ok) {
        let msg = 'Form submit failed';
        try { const j = await res.json(); if (j && j.error) msg = j.error; } catch {}
        throw new Error(msg);
      }

      // 🔍 Find matching row
      const row = document.querySelector(`tr[data-product-code="${productCode}"]`);
      if (row) {
        row.querySelector("td:nth-child(5)").innerHTML = '<span class="status-delivered">✅ Delivered</span>';
        row.querySelector("td:nth-child(6)").innerHTML = '<span class="text-muted">Complete</span>';
        row.classList.remove("delayed-row");

        // 🌟 Optional: visual highlight
        row.style.transition = "background-color 0.5s";
        row.style.backgroundColor = "#d4edda";
        setTimeout(() => row.style.backgroundColor = "", 1500);
      } else {
        console.warn("⚠️ No matching row found for:", productCode);
      }

      form.reset();
      // Reset UI to single mode by default
      document.querySelector('input[name="lot_mode"][value="single"]').checked = true;
      singleSection.style.display = '';
      multiSection.style.display = 'none';
      singleQtyWrap.style.display = '';
      lotsContainer.innerHTML = '';
      if (orderedQtyHint) orderedQtyHint.textContent = '0';
      if (multiTotalQty) multiTotalQty.textContent = '0';
      if (multiQtyWarning) multiQtyWarning.textContent = '';
    } catch (err) {
      alert("❌ Submit error: " + err.message);
      console.error(err);
    }
  });
});
