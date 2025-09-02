document.addEventListener("DOMContentLoaded", function () {
    const barcodeInput = document.getElementById("id_barcode");
    const productSelect = document.getElementById("id_product");
    const withdrawalType = document.getElementById("id_withdrawal_type");
    const unitLabel = document.getElementById("unit_label");

    // Focus on the barcode field when the page loads
    barcodeInput.focus();

    // Auto-select the product when a barcode is scanned
    barcodeInput.addEventListener("input", function () {
        const barcodeValue = barcodeInput.value.trim();
        let found = false;

        for (let option of productSelect.options) {
            if (option.dataset.barcode === barcodeValue) {
                productSelect.value = option.value;
                found = true;
                break;
            }
        }

        if (!found) {
            productSelect.value = ""; // Reset selection if no product matches
        }
    });

    // Change unit display based on withdrawal type
    withdrawalType.addEventListener("change", function () {
        unitLabel.textContent = withdrawalType.value === "volume" ? "mL" : "units";
    });
});
