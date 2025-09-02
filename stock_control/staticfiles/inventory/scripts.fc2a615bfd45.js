document.addEventListener("DOMContentLoaded", function () {
    // --- 1) Mode Toggle: Barcode vs. Manual ---
    const modeRadios = document.querySelectorAll('input[name="mode"]');
    const barcodeSection = document.getElementById("barcode-section");
    const manualSection = document.getElementById("manual-section");
    const barcodeInput = document.getElementById("id_barcode");

    modeRadios.forEach(radio => {
        radio.addEventListener("change", function () {
            if (this.value === "barcode") {
                barcodeSection.style.display = "block";
                manualSection.style.display = "none";
                if (barcodeInput) barcodeInput.focus();
            } else {
                barcodeSection.style.display = "none";
                manualSection.style.display = "block";
            }
        });
    });

    if (barcodeInput) {
        const defaultMode = document.querySelector('input[name="mode"]:checked');
        if (defaultMode && defaultMode.value === "barcode") {
            barcodeInput.focus();
        }
    }

    // --- 2) Withdrawal Mode Toggle: Full vs. Part ---
    const withdrawalModeRadios = document.querySelectorAll('input[name="withdrawal_mode"]');
    const fullItemSection = document.getElementById("full_item_section");
    const partItemSection = document.getElementById("part_item_section");

    withdrawalModeRadios.forEach(radio => {
        radio.addEventListener("change", function () {
            fullItemSection.style.display = this.value === "full" ? "block" : "none";
            partItemSection.style.display = this.value === "part" ? "block" : "none";
        });
    });

    // --- 3) Table Search Functionality ---
    function setupTableSearch(searchInputId, tableId, searchColumns) {
        const searchInput = document.getElementById(searchInputId);
        const table = document.getElementById(tableId);
        const tableBody = table?.getElementsByTagName("tbody")[0];

        if (searchInput && tableBody) {
            searchInput.addEventListener("keyup", function () {
                const filterValue = searchInput.value.toLowerCase();
                const rows = tableBody.getElementsByTagName("tr");

                for (let row of rows) {
                    const cells = row.getElementsByTagName("td");
                    let match = false;

                    searchColumns.forEach(index => {
                        if (cells[index] && cells[index].textContent.toLowerCase().includes(filterValue)) {
                            match = true;
                        }
                    });

                    row.style.display = match ? "" : "none";
                }
            });
        }
    }

    // ✅ Enable search for Product List Table
    setupTableSearch("searchInput", "productTable", [0, 1, 7]); // Search by Product Name (0), Product Code (1), Supplier (7)

    // ✅ Enable search for Withdrawal Tracking Table
    setupTableSearch("searchInput", "withdrawalTable", [1, 5, 6]); // Search by Product (1), Barcode (5), User (6)

    // --- 4) Barcode Auto-Fill Functionality ---
    async function fetchProductDetailsByBarcode(barcode) {
        try {
            const response = await fetch(`/get-product-by-barcode/?barcode=${barcode}`);
            if (!response.ok) throw new Error("Product not found");

            const data = await response.json();
            document.getElementById("id_product_name").value = data.name || "";
            document.getElementById("stock-display").textContent = data.stock ?? "";
            document.getElementById("units-display").textContent = data.units_per_quantity ?? "";
            document.getElementById("id_units_per_quantity").value = data.units_per_quantity ?? "";

            const volumeSection = document.getElementById("volume-withdrawal-section");
            if (data.product_feature === "volume" && volumeSection) {
                volumeSection.style.display = "block";
            } else {
                volumeSection.style.display = "none";
            }
        } catch (err) {
            console.error("Error fetching product by barcode:", err);
        }
    }

    const barcodeInput = document.getElementById("id_barcode");
    if (barcodeInput) {
        barcodeInput.addEventListener("input", function () {
            const barcodeValue = barcodeInput.value.trim();
            if (barcodeValue.length > 3) fetchProductDetailsByBarcode(barcodeValue);
        });
    }

    // --- 5) Change label if withdrawal_type = volume or unit ---
    const withdrawalType = document.getElementById("id_withdrawal_type");
    const unitLabel = document.getElementById("unit_label");
    if (withdrawalType && unitLabel) {
        withdrawalType.addEventListener("change", function () {
            unitLabel.textContent = withdrawalType.value === "volume" ? "mL" : "units";
        });
    }

    // --- 6) Part-Withdrawal: Recompute partial logic on input ---
    const partsInput = document.getElementById("id_parts_withdrawn");
    const fullItemsInput = document.getElementById("id_full_items");
    const partsRemainingInput = document.getElementById("id_parts_remaining");

    function updatePartCalculations() {
        if (!partsInput || !fullItemsInput || !partsRemainingInput) return;

        const parts = parseInt(partsInput.value, 10) || 0;
        const threshold = parseInt(document.getElementById("id_units_per_quantity").value, 10) || 1;
        const fullItems = Math.floor(parts / threshold);
        const remainder = parts % threshold;

        fullItemsInput.value = fullItems;
        partsRemainingInput.value = remainder === 0 && parts > 0 ? 0 : threshold - remainder;
    }

    if (partsInput) {
        partsInput.addEventListener("input", updatePartCalculations);
        updatePartCalculations();
    }

    // --- 7) Report Download Functionality ---
    const reportForm = document.getElementById("reportForm");
    if (reportForm) {
        const modelSelector = document.getElementById("report_type");
        const fieldContainer = document.getElementById("field-container");
        const reportUrl = document.getElementById("downloadReportUrl").value;

        const modelFields = {
            "withdrawals": ["timestamp", "product", "quantity", "withdrawal_type", "barcode", "user"],
            "stock": ["product_code", "name", "supplier", "threshold", "lead_time", "current_stock"],
            "purchase_orders": ["product", "quantity_ordered", "ordered_by", "order_date", "expected_delivery", "status"]
        };

        function updateFields() {
            const selectedModel = modelSelector.value;
            fieldContainer.innerHTML = "";
            (modelFields[selectedModel] || []).forEach(field => {
                const checkbox = document.createElement("input");
                checkbox.type = "checkbox";
                checkbox.name = "fields";
                checkbox.value = field;
                checkbox.id = `field_${field}`;
                checkbox.checked = true;

                const label = document.createElement("label");
                label.htmlFor = `field_${field}`;
                label.textContent = field.replace("_", " ");

                const div = document.createElement("div");
                div.appendChild(checkbox);
                div.appendChild(label);
                fieldContainer.appendChild(div);
            });
        }

        modelSelector.addEventListener("change", updateFields);
        updateFields();

        reportForm.addEventListener("submit", function (event) {
            event.preventDefault();
            const formData = new FormData(reportForm);
            const selectedFields = [...document.querySelectorAll("#field-container input[type='checkbox']:checked")].map(c => c.value);

            if (selectedFields.length === 0) {
                alert("Please select at least one field for the report.");
                return;
            }

            fetch(reportUrl, { method: "POST", body: formData })
                .then(response => response.blob())
                .then(blob => {
                    const downloadUrl = URL.createObjectURL(blob);
                    const a = document.createElement("a");
                    a.href = downloadUrl;
                    a.download = `report_${modelSelector.value}_${new Date().toISOString().split("T")[0]}.xlsx`;
                    document.body.appendChild(a);
                    a.click();
                    a.remove();
                    URL.revokeObjectURL(downloadUrl);
                })
                .catch(error => console.error("Error downloading file:", error));
        });
    }
});
