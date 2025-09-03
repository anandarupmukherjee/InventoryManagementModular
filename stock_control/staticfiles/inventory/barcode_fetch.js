document.addEventListener("DOMContentLoaded", function () {
  const barcodeInput = document.getElementById("id_barcode");
  if (!barcodeInput) return;

  function localParseGS1(raw) {
    if (!raw) return null;
    const gs = /\x1D/g; // FNC1/GS
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
    const json = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(json.error || "Barcode parsing failed");
    return json;
  }

  async function hydrateProductDetails(code) {
    try {
      const productResponse = await fetch(`/data/get-product-by-barcode/?barcode=${encodeURIComponent(code)}`);
      if (!productResponse.ok) return;
      const product = await productResponse.json();
      const nameEl = document.getElementById("id_product_name");
      if (nameEl) nameEl.value = product.name || "";
      const stockEl = document.getElementById("stock-display");
      if (stockEl) stockEl.textContent = product.stock ?? "";
      const unitsDisp = document.getElementById("units-display");
      if (unitsDisp) unitsDisp.textContent = product.units_per_quantity ?? "";
      const unitsInput = document.getElementById("id_units_per_quantity");
      if (unitsInput) unitsInput.value = product.units_per_quantity ?? "";
      const codeHidden = document.getElementById("parsed_product_code_hidden");
      if (codeHidden) codeHidden.value = code || "";
      const volumeSection = document.getElementById("volume-withdrawal-section");
      if (volumeSection) volumeSection.style.display = (product.product_feature === "volume") ? "block" : "none";
    } catch (e) {
      console.warn("Failed to hydrate product details", e);
    }
  }

  barcodeInput.addEventListener("keydown", async function (event) {
    if (event.key !== "Enter") return;
    event.preventDefault();
    const rawBarcode = barcodeInput.value.trim();
    if (rawBarcode.length < 6) return;

    let data = null;
    try {
      data = await parseRemote(rawBarcode);
    } catch (remoteErr) {
      // Fallback to lightweight client-side GS1 parse
      data = localParseGS1(rawBarcode);
      if (!data) {
        console.error("❌ Error processing barcode:", remoteErr);
        alert("❌ Failed to process barcode. Ensure format is correct.");
        return;
      }
    }

    // Fill parsed barcode details when fields exist
    const codeField = document.getElementById("parsed_product_code");
    if (codeField) codeField.value = data.normalized_product_code || data.product_code || "";
    const lotField = document.getElementById("parsed_lot_number");
    if (lotField) lotField.value = data.lot_number || "";
    const expField = document.getElementById("parsed_expiry_date");
    if (expField) expField.value = data.expiry_date || "";

    // Try to also set commonly used hidden fields
    const lotHidden = document.getElementById("lot_number_field");
    if (lotHidden) lotHidden.value = data.lot_number || "";
    const expHidden = document.getElementById("expiry_date_field");
    if (expHidden) expHidden.value = data.expiry_date || "";

    // Normalize product code for DB lookup (strip leading zeros when purely numeric)
    let lookupCode = data.normalized_product_code || data.product_code || "";
    if (/^\d+$/.test(lookupCode)) lookupCode = lookupCode.replace(/^0+/, "") || "0";

    if (lookupCode) await hydrateProductDetails(lookupCode);
  });
});
