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




    // // --- 3) Table Search Functionality ---
    // Check if search input fields exist
    const searchProduct = document.getElementById("searchProduct");
    const searchWithdrawal = document.getElementById("searchWithdrawal");
    const productTable = document.getElementById("productTable");
    const withdrawalTable = document.getElementById("withdrawalTable");

    console.log("🔍 Checking elements:");
    console.log("🔍 searchProduct:", searchProduct ? "✅ Found" : "❌ Not Found");
    console.log("🔍 productTable:", productTable ? "✅ Found" : "❌ Not Found");
    console.log("🔍 searchWithdrawal:", searchWithdrawal ? "✅ Found" : "❌ Not Found");
    console.log("🔍 withdrawalTable:", withdrawalTable ? "✅ Found" : "❌ Not Found");

    /**
     * Function to enable search filtering on a table.
     * @param {string} searchInputId - The ID of the search input field.
     * @param {string} tableId - The ID of the table to filter.
     * @param {Array<number>} columnIndexes - The indexes of the columns to search.
     */
    function setupTableSearch(searchInputId, tableId, columnIndexes) {
        const searchInput = document.getElementById(searchInputId);
        const table = document.getElementById(tableId);
        
        if (!searchInput || !table) {
            console.error(`❌ Error: Missing elements for search in ${tableId}`);
            return;
        }

        console.log(`🔍 Setting up search for table: ${tableId}`);

        searchInput.addEventListener("keyup", function () {
            const filterValue = searchInput.value.toLowerCase();
            const tableBody = table.getElementsByTagName("tbody")[0];
            const rows = tableBody.getElementsByTagName("tr");

            for (let row of rows) {
                const cells = row.getElementsByTagName("td");
                let match = false;

                columnIndexes.forEach(index => {
                    if (cells[index] && cells[index].textContent.toLowerCase().includes(filterValue)) {
                        match = true;
                    }
                });

                row.style.display = match ? "" : "none";
            }
        });

        console.log(`✅ Search enabled for table: ${tableId}`);
    }

    // ✅ Enable search for Product List Table (Product Name, Product Code, Supplier)
    if (searchProduct && productTable) {
        setupTableSearch("searchProduct", "productTable", [0, 1, 7]);
    } else {
        console.error("❌ Product search input or table not found.");
    }

    // ✅ Enable search for Withdrawal Tracking Table (Product, Barcode, User)
    if (searchWithdrawal && withdrawalTable) {
        setupTableSearch("searchWithdrawal", "withdrawalTable", [1, 5, 6]);
    } else {
        console.error("❌ Withdrawal search input or table not found.");
    }











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

    // const barcodeInput = document.getElementById("id_barcode");
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

// --- 8) Manual Product Dropdown Auto-Fill ---
const productDropdown = document.getElementById("id_product_dropdown");
if (productDropdown) {
    productDropdown.addEventListener("change", async function () {
        const selectedId = this.value;
        console.log("🔍 Triggered product dropdown change with ID:", selectedId);
        if (!selectedId) return;

        try {
            const response = await fetch(`/get-product-by-id/?id=${selectedId}`);
            if (!response.ok) throw new Error("Product not found");

            const data = await response.json();
            console.log("📦 Product data fetched:", data);

            document.getElementById("id_barcode_manual").value = data.product_code || "";
            document.getElementById("manual-stock-display").textContent = data.current_stock ?? "N/A";
            document.getElementById("manual-units-display").textContent = data.units_per_quantity ?? "";
            document.getElementById("id_units_per_quantity").value = data.units_per_quantity ?? "";

            const volumeSection = document.getElementById("volume-withdrawal-section");
            if (data.product_feature === "volume" && volumeSection) {
                volumeSection.style.display = "block";
            } else {
                volumeSection.style.display = "none";
            }
        } catch (err) {
            console.error("❌ Error fetching product by ID:", err);
        }
    });
}






// ##################### ANALYSIS ##################

// console.log("✅ Analysis & Forecasting Charts Loaded");

//     function getChartData(canvasId) {
//         const element = document.getElementById(canvasId);
//         if (!element) {
//             console.error(`❌ Element with ID '${canvasId}' not found.`);
//             return null;
//         }
//         try {
//             return {
//                 labels: JSON.parse(element.getAttribute("data-labels") || "[]"),
//                 stock: JSON.parse(element.getAttribute("data-stock") || "[]"),
//                 thresholds: JSON.parse(element.getAttribute("data-thresholds") || "[]"),
//                 dates: JSON.parse(element.getAttribute("data-dates") || "[]"),
//                 withdrawals: JSON.parse(element.getAttribute("data-withdrawals") || "[]"),
//                 sma7: JSON.parse(element.getAttribute("data-sma7") || "[]"),
//                 sma14: JSON.parse(element.getAttribute("data-sma14") || "[]"),
//                 forecastDates: JSON.parse(element.getAttribute("data-forecast-dates") || "[]"),
//                 forecastValues: JSON.parse(element.getAttribute("data-forecast-values") || "[]")
//             };
//         } catch (error) {
//             console.error(`❌ Error parsing data for '${canvasId}':`, error);
//             return null;
//         }
//     }

//     function renderChart(canvasId, chartType, datasets, labels) {
//         const ctx = document.getElementById(canvasId);
//         if (ctx) {
//             new Chart(ctx.getContext("2d"), {
//                 type: chartType,
//                 data: { labels: labels, datasets: datasets },
//                 options: { responsive: true, maintainAspectRatio: false, scales: { y: { beginAtZero: true } } }
//             });
//         } else {
//             console.warn(`⚠ Chart '${canvasId}' not found.`);
//         }
//     }

//     // ✅ Stock Levels Chart
//     const stockData = getChartData("stockLevelsChart");
//     if (stockData && stockData.labels.length > 0) {
//         renderChart("stockLevelsChart", "bar", [
//             { label: "Current Stock", data: stockData.stock, backgroundColor: "blue" },
//             { label: "Threshold", data: stockData.thresholds, backgroundColor: "red" }
//         ], stockData.labels);
//     }

//     // ✅ Withdrawals Over Time Chart
//     const withdrawalData = getChartData("withdrawalsOverTimeChart");
//     if (withdrawalData && withdrawalData.dates.length > 0) {
//         renderChart("withdrawalsOverTimeChart", "line", [
//             { label: "Total Withdrawals", data: withdrawalData.withdrawals, borderColor: "green", fill: false }
//         ], withdrawalData.dates);
//     }

//     // ✅ Forecast Chart
//     const forecastData = getChartData("forecastChart");
//     if (forecastData && forecastData.forecastValues.length > 0) {
//         renderChart("forecastChart", "line", [
//             { label: "7-Day SMA", data: forecastData.sma7, borderColor: "orange", fill: false },
//             { label: "14-Day SMA", data: forecastData.sma14, borderColor: "red", fill: false },
//             { label: "Forecast (Next 7 Days)", data: [...Array(forecastData.withdrawals.length).fill(null), ...forecastData.forecastValues], borderColor: "purple", borderDash: [5, 5], fill: false }
//         ], [...forecastData.dates, ...forecastData.forecastDates]);
//     }

//     // ✅ Open Charts in Modal View
//     function openModal(chartId) {
//         const modal = document.getElementById("chartModal");
//         const modalChartCanvas = document.getElementById("modalChart");
//         const chartData = getChartData(chartId);

//         if (!chartData) return;

//         modal.style.display = "block";

//         // Destroy existing chart before creating a new one
//         if (window.modalChartInstance) {
//             window.modalChartInstance.destroy();
//         }

//         window.modalChartInstance = new Chart(modalChartCanvas.getContext("2d"), {
//             type: "line",
//             data: {
//                 labels: chartData.dates,
//                 datasets: [
//                     { label: "Actual Withdrawals", data: chartData.withdrawals, borderColor: "blue", fill: false },
//                     { label: "7-Day SMA", data: chartData.sma7, borderColor: "orange", fill: false },
//                     { label: "14-Day SMA", data: chartData.sma14, borderColor: "red", fill: false },
//                     { label: "Forecast", data: chartData.forecastValues, borderColor: "purple", fill: false }
//                 ]
//             },
//             options: { responsive: true, maintainAspectRatio: false }
//         });
//     }

//     function closeModal() {
//         document.getElementById("chartModal").style.display = "none";
//     }

//     document.querySelectorAll(".chart-tile").forEach(tile => {
//         tile.addEventListener("click", function () {
//             openModal(this.querySelector("canvas").id);
//         });
//     });

//     document.querySelector(".close-modal").addEventListener("click", closeModal);



});



