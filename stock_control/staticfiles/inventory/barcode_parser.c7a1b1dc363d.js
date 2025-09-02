document.addEventListener("DOMContentLoaded", function () {
    const barcodeInput = document.getElementById("id_barcode");

    if (!barcodeInput) return;

    barcodeInput.addEventListener("input", function () {
        const raw = barcodeInput.value.trim();
        if (!raw) return;

        // --- Detect 3PR Format ---
        if (raw.includes("3PR")) {
            const parts = raw.split("3PR");
            const before = parts[0];  // Useless leading zeroes
            const after = parts[1];   // 00063**0011765983**31.08.2026**

            const [productCodeRest, lot, expiry] = after.split("**");
            const product_code = "3PR" + productCodeRest;

            populateFields({ product_code, lot, expiry });
        }

        // --- GS1 Format Support (Optional) ---
        else if (raw.startsWith("01")) {
            const aiMap = { "01": "product_code", "10": "lot", "17": "expiry" };
            let index = 0;
            const parsed = {};

            while (index < raw.length) {
                const ai = raw.substring(index, index + 2);
                let length = 0;
                if (ai === "01") length = 14;
                else if (ai === "10") {
                    index += 2;
                    const lotStart = index;
                    while (index < raw.length && !["17", "21", "00"].includes(raw.substring(index, index + 2))) {
                        index++;
                    }
                    parsed.lot = raw.substring(lotStart, index);
                    continue;
                }
                else if (ai === "17") length = 6;
                else break;

                parsed[aiMap[ai]] = raw.substring(index + 2, index + 2 + length);
                index += 2 + length;
            }

            // Format expiry
            if (parsed.expiry?.length === 6) {
                const y = "20" + parsed.expiry.substring(0, 2);
                const m = parsed.expiry.substring(2, 4);
                const d = parsed.expiry.substring(4, 6);
                parsed.expiry = `${y}-${m}-${d}`;
            }

            populateFields(parsed);
        }
    });

    function populateFields({ product_code, lot, expiry }) {
        if (product_code) document.getElementById("id_barcode").value = product_code;
        if (lot) document.getElementById("id_lot_number")?.value = lot;
        if (expiry) document.getElementById("id_expiry_date")?.value = expiry;
    }
});
