document.addEventListener("DOMContentLoaded", function () {
    // --- Toggle Functionality (if applicable) ---
    const modeRadios = document.querySelectorAll('input[name="mode"]');
    const barcodeSection = document.getElementById("barcode-section");
    const dropdownSection = document.getElementById("dropdown-section");

    if (modeRadios.length) {
        modeRadios.forEach(radio => {
            radio.addEventListener("change", function () {
                if (this.value === "barcode") {
                    barcodeSection.style.display = "block";
                    dropdownSection.style.display = "none";
                } else {
                    barcodeSection.style.display = "none";
                    dropdownSection.style.display = "block";
                }
            });
        });
    }

    // --- Barcode Auto-Fill Functionality ---
    const barcodeInput = document.getElementById("id_barcode");
    const productNameInput = document.getElementById("id_product_name"); // read-only field for product name
    const quantityInput = document.getElementById("id_quantity");
    const withdrawalType = document.getElementById("id_withdrawal_type");
    const unitLabel = document.getElementById("unit_label");

    // Autofocus barcode field on page load (if in barcode mode)
    if (barcodeInput && (!document.querySelector('input[name="mode"]') || document.querySelector('input[name="mode"][value="barcode"]').checked)) {
        barcodeInput.focus();
    }

    if (barcodeInput && productNameInput) {
        barcodeInput.addEventListener("input", function () {
            const barcodeValue = barcodeInput.value.trim();
            if (barcodeValue.length > 5) {  // Trigger when barcode seems valid
                fetchProductDetails(barcodeValue);
            }
        });
    }

    // Function to fetch product details via AJAX
    async function fetchProductDetails(barcode) {
        try {
            const response = await fetch(`/get-product-by-barcode/?barcode=${barcode}`);
            if (!response.ok) {
                console.error("Server returned an error:", response.status);
                return;
            }
            const data = await response.json();
            console.log("Fetched Data:", data);
            if (data.name) {
                productNameInput.value = data.name;
                if (quantityInput) {
                    quantityInput.focus();
                }
            } else {
                productNameInput.value = "";
            }
        } catch (error) {
            console.error("Error fetching product details:", error);
        }
    }

    // --- Withdrawal Type Unit Change ---
    if (withdrawalType && unitLabel) {
        withdrawalType.addEventListener("change", function () {
            unitLabel.textContent = withdrawalType.value === "volume" ? "mL" : "units";
        });
    }

    // --- Table Search Feature for Track Withdrawals ---
    const searchInput = document.getElementById("searchInput");
    const tableBody = document.getElementById("productTable")?.getElementsByTagName("tbody")[0];

    if (searchInput && tableBody) {
        searchInput.addEventListener("keyup", function () {
            const filterValue = searchInput.value.toLowerCase();
            const rows = tableBody.getElementsByTagName("tr");

            for (let row of rows) {
                const timestampText = row.cells[0]?.textContent.toLowerCase() || "";
                const productNameText = row.cells[1]?.textContent.toLowerCase() || "";
                const usernameText = row.cells[5]?.textContent.toLowerCase() || "";

                if (timestampText.includes(filterValue) || productNameText.includes(filterValue) || usernameText.includes(filterValue)) {
                    row.style.display = "";
                } else {
                    row.style.display = "none";
                }
            }
        });
    }

    // --- Report Download (Prevent GET Requests After Download) ---
    const form = document.getElementById("reportForm");
    const modelSelector = document.getElementById("report_type");
    const fieldContainer = document.getElementById("field-container");
    const reportUrl = document.getElementById("downloadReportUrl").value;  // Get the correct Django URL

    // Define available fields for each model
    const modelFields = {
        "withdrawals": ["timestamp", "product", "product_code", "quantity", "withdrawal_type", "barcode", "user"],
        "stock": ["product_code", "name", "supplier", "threshold", "lead_time", "current_stock"],
        "purchase_orders": ["product", "quantity_ordered", "ordered_by", "order_date", "expected_delivery", "status"]
    };

    function updateFields() {
        const selectedModel = modelSelector.value;
        const fields = modelFields[selectedModel] || [];
        
        fieldContainer.innerHTML = ""; // Clear existing checkboxes

        fields.forEach(field => {
            const checkbox = document.createElement("input");
            checkbox.type = "checkbox";
            checkbox.name = "fields";
            checkbox.value = field;
            checkbox.id = `field_${field}`;
            checkbox.checked = true;  // Default: checked

            const label = document.createElement("label");
            label.htmlFor = `field_${field}`;
            label.textContent = field.replace("_", " ").charAt(0).toUpperCase() + field.slice(1);

            const div = document.createElement("div");
            div.appendChild(checkbox);
            div.appendChild(label);
            fieldContainer.appendChild(div);
        });
    }

    modelSelector.addEventListener("change", updateFields);
    updateFields(); // Initialize fields on page load

    // Handle form submission via AJAX
    form.addEventListener("submit", function(event) {
        event.preventDefault();  // ✅ Prevent default form submission
    
        const formData = new FormData(form);
    
        // ✅ Ensure at least one field is selected
        const selectedFields = [];
        document.querySelectorAll("#field-container input[type='checkbox']:checked").forEach((checkbox) => {
            formData.append("fields", checkbox.value);
            selectedFields.push(checkbox.value);
        });
    
        if (selectedFields.length === 0) {
            alert("Please select at least one field for the report.");
            return;
        }
    
        // ✅ Get the selected model name for filename
        const modelName = document.getElementById("report_type").value;
        const formattedModelName = modelName.replace("_", "").toLowerCase(); // Format model name
        const currentDate = new Date().toISOString().split("T")[0]; // Get YYYY-MM-DD
    
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
            a.download = `report_${formattedModelName}_${currentDate}.xlsx`;  // ✅ Updated filename
            document.body.appendChild(a);
            a.click();
            a.remove();
            window.URL.revokeObjectURL(downloadUrl);
        })
        .catch(error => console.error("Error downloading file:", error));
    });


    
});
