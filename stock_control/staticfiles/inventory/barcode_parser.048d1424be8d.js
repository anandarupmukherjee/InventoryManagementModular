const barcodeInput = document.getElementById("id_barcode");
if (barcodeInput) {
    barcodeInput.addEventListener("change", async function () {
        const barcode = barcodeInput.value.trim();
        if (!barcode) return;

        try {
            const response = await fetch(`/parse-barcode/?barcode=${encodeURIComponent(barcode)}`);
            const data = await response.json();
            if (!response.ok) throw new Error(data.error || "Fetch failed");

            // Populate fields
            document.getElementById("id_product_name").value = data.name || "";
            document.getElementById("stock-display").textContent = data.current_stock ?? "";
            document.getElementById("units-display").textContent = data.units_per_quantity ?? "";
            document.getElementById("id_units_per_quantity").value = data.units_per_quantity ?? "";
            document.getElementById("parsed_product_code_hidden").value = data.product_code || "";

            document.getElementById("id_lot_number").value = data.lot_number ?? "";
            document.getElementById("id_expiry_date").value = data.expiry_date ?? "";

            // Volume toggle
            const volumeSection = document.getElementById("volume-withdrawal-section");
            if (data.product_feature === "volume" && volumeSection) {
                volumeSection.style.display = "block";
            } else {
                volumeSection.style.display = "none";
            }

        } catch (err) {
            alert("Barcode parsing failed: " + err.message);
            console.error(err);
        }
    });
}
