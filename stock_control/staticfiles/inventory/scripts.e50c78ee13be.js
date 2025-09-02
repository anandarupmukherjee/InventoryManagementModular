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

    // --- 3) Barcode Auto-Fill Functionality ---
    const productNameInput = document.getElementById("id_product_name");
    const stockDisplay = document.getElementById("stock-display");
    const unitsDisplay = document.getElementById("units-display");
    const unitsPerQuantityInput = document.getElementById("id_units_per_quantity");
    const volumeSection = document.getElementById("volume-withdrawal-section");
    const volumeSelect = document.getElementById("id_volume_select");

    if (barcodeInput) {
        barcodeInput.addEventListener("input", function () {
            const barcodeValue = barcodeInput.value.trim();
            if (barcodeValue.length > 3) {
                fetchProductDetailsByBarcode(barcodeValue);
            }
        });
    }

    async function fetchProductDetailsByBarcode(barcode) {
        try {
            const response = await fetch(`/get-product-by-barcode/?barcode=${barcode}`);
            if (!response.ok) {
                productNameInput.value = "";
                stockDisplay.textContent = "";
                unitsDisplay.textContent = "";
                unitsPerQuantityInput.value = "";
                if (volumeSection) volumeSection.style.display = "none";
                return;
            }
            const data = await response.json();
            productNameInput.value = data.name || "";
            stockDisplay.textContent = data.stock ?? "";
            unitsDisplay.textContent = data.units_per_quantity ?? "";
            unitsPerQuantityInput.value = data.units_per_quantity ?? "";

            if (data.product_feature === "volume") {
                if (volumeSection) {
                    volumeSection.style.display = "block";
                    if (volumeSelect) {
                        volumeSelect.innerHTML = "";
                        let totalVol = parseFloat(data.stock) || 0;
                        let step = 50;
                        let current = 0;
                        while (current < totalVol) {
                            current += step;
                            if (current > totalVol) current = totalVol;
                            let opt = document.createElement("option");
                            opt.value = current.toFixed(2);
                            opt.textContent = `${current.toFixed(2)} mL`;
                            volumeSelect.appendChild(opt);
                            if (current === totalVol) break;
                        }
                    }
                }
            } else {
                if (volumeSection) volumeSection.style.display = "none";
            }
        } catch (err) {
            console.error("Error fetching product by barcode:", err);
        }
    }

    // --- 4) Table Search Feature for Product List ---
    function setupTableSearch(searchInputId, tableId) {
        const searchInput = document.getElementById(searchInputId);
        const tableBody = document.getElementById(tableId)?.getElementsByTagName("tbody")[0];

        if (searchInput && tableBody) {
            searchInput.addEventListener("keyup", function () {
                const filterValue = searchInput.value.toLowerCase();
                const rows = tableBody.getElementsByTagName("tr");
                for (let row of rows) {
                    const cells = row.getElementsByTagName("td");
                    let match = false;
                    for (let cell of cells) {
                        if (cell.textContent.toLowerCase().includes(filterValue)) {
                            match = true;
                            break;
                        }
                    }
                    row.style.display = match ? "" : "none";
                }
            });
        }
    }

    // Enable search for product list and withdrawal track tables
    setupTableSearch("searchInput", "productTable");  // Product List
    setupTableSearch("searchInput", "withdrawalTable");  // Withdrawal Tracking

    // --- 5) Report Download Functionality ---
    const reportForm = document.getElementById("reportForm");
    if (reportForm) {
        const modelSelector = document.getElementById("report_type");
        const fieldContainer = document.getElementById("field-container");
        const reportUrl = document.getElementById("downloadReportUrl").value;

        const modelFields = {
            "withdrawals": [
                "timestamp", "product", "product_code", "quantity",
                "withdrawal_type", "barcode", "user"
            ],
            "stock": [
                "product_code", "name", "supplier", "threshold", 
                "lead_time", "current_stock"
            ],
            "purchase_orders": [
                "product", "quantity_ordered", "ordered_by", 
                "order_date", "expected_delivery", "status"
            ]
        };

        function updateFields() {
            const selectedModel = modelSelector.value;
            const fields = modelFields[selectedModel] || [];
            fieldContainer.innerHTML = "";
            fields.forEach(field => {
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
            const selectedFields = [];
            document
                .querySelectorAll("#field-container input[type='checkbox']:checked")
                .forEach(checkbox => {
                    formData.append("fields", checkbox.value);
                    selectedFields.push(checkbox.value);
                });

            if (selectedFields.length === 0) {
                alert("Please select at least one field for the report.");
                return;
            }

            fetch(reportUrl, {
                method: "POST",
                body: formData
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error(`Server returned ${response.status}`);
                }
                return response.blob();
            })
            .then(blob => {
                const downloadUrl = window.URL.createObjectURL(blob);
                const a = document.createElement("a");
                a.href = downloadUrl;
                const modelName = modelSelector.value.replace("_", "");
                const currentDate = new Date().toISOString().split("T")[0];
                a.download = `report_${modelName}_${currentDate}.xlsx`;
                document.body.appendChild(a);
                a.click();
                a.remove();
                window.URL.revokeObjectURL(downloadUrl);
            })
            .catch(error => console.error("Error downloading file:", error));
        });
    }
});
