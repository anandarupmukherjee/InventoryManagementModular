const barcodeInput = document.getElementById("id_barcode");

function localParseGS1(raw) {
  if (!raw) return null;
  const gs = /\x1D/g;
  let s = String(raw).replace(gs, "");
  const flat = s.replace(/[^A-Za-z0-9]+/g, "");
  const out = { product_code: "", lot_number: "", expiry_date: "", format: null };
  const m01 = flat.match(/01(\d{14})/);
  if (!m01) return null;
  out.product_code = m01[1];
  const after01 = flat.slice(m01.index + 16);
  const m17 = after01.match(/17(\d{6})/);
  if (m17) {
    const d = m17[1];
    out.expiry_date = `${d.slice(4,6)}.${d.slice(2,4)}.20${d.slice(0,2)}`;
  }
  const m10 = after01.match(/10([A-Za-z0-9\-_.\/]+?)(?=(?:01|17|21|15|11|30|37)\d|$)/);
  if (m10) out.lot_number = m10[1];
  out.format = "GS1_flat";
  return out;
}

async function parseRemote(raw) {
  const response = await fetch(`/data/parse-barcode/?raw=${encodeURIComponent(raw)}`);
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.error || "Fetch failed");
  return data;
}

if (barcodeInput) {
  barcodeInput.addEventListener("change", async function () {
    const barcode = barcodeInput.value.trim();
    if (!barcode) return;

    let data = null;
    try {
      data = await parseRemote(barcode);
    } catch (err) {
      data = localParseGS1(barcode);
      if (!data) {
        alert("Barcode parsing failed: " + err.message);
        console.error(err);
        return;
      }
    }

    // Populate form fields if they exist
    const nameEl = document.getElementById("id_product_name");
    if (nameEl) nameEl.value = data.name || "";
    const stockDisp = document.getElementById("stock-display");
    if (stockDisp) stockDisp.textContent = data.current_stock ?? "";
    const unitsDisp = document.getElementById("units-display");
    if (unitsDisp) unitsDisp.textContent = data.units_per_quantity ?? "";
    const unitsInput = document.getElementById("id_units_per_quantity");
    if (unitsInput) unitsInput.value = data.units_per_quantity ?? "";

    // Populate visible fields (if present)
    const lotInput = document.getElementById("id_lot_number");
    if (lotInput) lotInput.value = data.lot_number ?? "";
    const expInput = document.getElementById("id_expiry_date");
    if (expInput) expInput.value = data.expiry_date ?? "";

    // Also populate hidden fields for POST submission
    const codeHidden = document.getElementById("product_code_from_barcode");
    if (codeHidden) codeHidden.value = data.normalized_product_code || data.product_code || "";
    const lotHidden = document.getElementById("lot_number_field");
    if (lotHidden) lotHidden.value = data.lot_number || "";
    const expHidden = document.getElementById("expiry_date_field");
    if (expHidden) expHidden.value = data.expiry_date || "";

    // Volume-specific UI logic
    const volumeSection = document.getElementById("volume-withdrawal-section");
    if (volumeSection) {
      const pf = data.product_feature;
      volumeSection.style.display = (pf === "volume") ? "block" : "none";
    }
  });
}
