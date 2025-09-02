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
    // This code filters rows in the table by matching against Timestamp (column 0),
    // Product Name (column 1), and Username (column 5).
    const searchInput = document.getElementById("searchInput");
    const tableBody = document.getElementById("productTable")?.getElementsByTagName("tbody")[0];

    if (searchInput && tableBody) {
        searchInput.addEventListener("keyup", function () {
            const filterValue = searchInput.value.toLowerCase();
            const rows = tableBody.getElementsByTagName("tr");

            for (let row of rows) {
                // Get text from columns: timestamp (0), product name (1), and username (5)
                const timestampText = row.cells[0]?.textContent.toLowerCase() || "";
                const productNameText = row.cells[1]?.textContent.toLowerCase() || "";
                const usernameText = row.cells[5]?.textContent.toLowerCase() || "";

                // Show row if any of these columns contain the filter value
                if (timestampText.includes(filterValue) || productNameText.includes(filterValue) || usernameText.includes(filterValue)) {
                    row.style.display = "";
                } else {
                    row.style.display = "none";
                }
            }
        });
    }


    //Report download auto update features based on models and forms
    const form = document.getElementById("reportForm");
    const modelSelector = document.getElementById("report_type");
    const fieldContainer = document.getElementById("field-container");

    // Define available fields for each model
    const modelFields = {
        "withdrawals": ["timestamp", "product", "product_code", "quantity", "withdrawal_type", "barcode", "user"],
        "stock": ["product_code", "name", "supplier", "threshold", "lead_time", "current_stock"],
        "purchase_orders": ["product", "quantity_ordered", "ordered_by", "order_date", "expected_delivery", "status"]
    };

    function updateFields() {
        const selectedModel = modelSelector.value;
        const fields = modelFields[selectedModel] || [];
        
        // Clear existing checkboxes
        fieldContainer.innerHTML = "";

        fields.forEach(field => {
            // Create checkbox input
            const checkbox = document.createElement("input");
            checkbox.type = "checkbox";
            checkbox.name = "fields";
            checkbox.value = field;
            checkbox.id = `field_${field}`;
            checkbox.checked = true; // Default checked

            // Create label
            const label = document.createElement("label");
            label.htmlFor = `field_${field}`;
            label.textContent = field.replace("_", " ").charAt(0).toUpperCase() + field.slice(1); // Format label

            // Wrap in div and append
            const div = document.createElement("div");
            div.appendChild(checkbox);
            div.appendChild(label);
            fieldContainer.appendChild(div);
        });
    }

    // Attach event listener to update fields on model change
    modelSelector.addEventListener("change", updateFields);
    updateFields(); // Initialize fields on page load

    // Handle form submission via AJAX
    form.addEventListener("submit", function(event) {
        event.preventDefault(); // Prevent default form submission

        const formData = new FormData(form);
        const url = form.action || window.location.href;

        fetch(url, {
            method: "POST",
            body: formData
        })
        .then(response => response.blob())
        .then(blob => {
            const downloadUrl = window.URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = downloadUrl;
            a.download = "report.xlsx";  // Default filename
            document.body.appendChild(a);
            a.click();
            a.remove();
            window.URL.revokeObjectURL(downloadUrl);
        })
        .catch(error => console.error("Error downloading file:", error));
    });
});

