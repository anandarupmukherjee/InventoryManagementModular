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
});
