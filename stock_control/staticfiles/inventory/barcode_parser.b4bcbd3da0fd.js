document.addEventListener("DOMContentLoaded", function () {
    const barcodeInput = document.getElementById("id_barcode");

    if (barcodeInput) {
        barcodeInput.addEventListener("change", function () {
            const raw = barcodeInput.value.trim();
            if (!raw) return;

            // Type 1: 3PR Format
            if (raw.includes("3PR")) {
                const match = raw.match(/3PR\d{5}/);
                const product_code = match ? match[0] : "";
                const parts = raw.replace(/\*/g, "").split(product_code);
                const lot = parts[1]?.substring(0, 10) ?? "";
                const expiry = parts[1]?.substring(10) ?? "";

                populateBarcodeFields({ product_code, lot, expiry });
            }

            // Type 2: GS1 Format (AI-based)
            else if (raw.startsWith("01")) {
                const aiMap = {
                    "01": "product_code", // GTIN
                    "10": "lot",
                    "17": "expiry"
                };

                let currentIndex = 0;
                const parsed = {};
                while (currentIndex < raw.length) {
                    const ai = raw.substring(currentIndex, currentIndex + 2);
                    const aiLength = ai === "01" ? 14 : ai === "17" ? 6 : 10; // Fallback

                    const value = raw.substring(currentIndex + 2, currentIndex + 2 + aiLength);
                    const key = aiMap[ai];

                    if (key) parsed[key] = value;
                    currentIndex += 2 + aiLength;
                }

                // Expiry reformat: YYMMDD to YYYY-MM-DD
                if (parsed.expiry?.length === 6) {
                    const y = "20" + parsed.expiry.substring(0, 2);
                    const m = parsed.expiry.substring(2, 4);
                    const d = parsed.expiry.substring(4, 6);
                    parsed.expiry = `${y}-${m}-${d}`;
                }

                populateBarcodeFields(parsed);
            }
        });
    }

    function populateBarcodeFields({ product_code, lot, expiry }) {
        if (product_code) document.getElementById("id_barcode").value = product_code;
        if (lot) document.getElementById("id_lot_number")?.value = lot;
        if (expiry) document.getElementById("id_expiry_date")?.value = expiry;
    }
});
