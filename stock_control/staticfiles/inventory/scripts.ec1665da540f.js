document.addEventListener("DOMContentLoaded", function () {
    const barcodeInput = document.getElementById("id_barcode");
    const productSelect = document.getElementById("id_product");
    const quantityInput = document.getElementById("id_quantity");
    const withdrawalType = document.getElementById("id_withdrawal_type");
    const unitLabel = document.getElementById("unit_label");

    // Ensure elements exist before applying event listeners
    if (barcodeInput && productSelect) {
        barcodeInput.focus();

        barcodeInput.addEventListener("input", async function () {
            const barcodeValue = barcodeInput.value.trim();

            if (barcodeValue.length > 5) {  // Avoid empty/invalid requests
                try {
                    const response = await fetch(`/get-product-by-barcode/?barcode=${barcodeValue}`);

                    if (!response.ok) {
                        console.error("Server returned an error:", response.status);
                        return;
                    }

                    const data = await response.json();
                    if (data.id) {
                        productSelect.value = data.id;
                        quantityInput.focus();  // Move focus to quantity after product is auto-selected
                    } else {
                        productSelect.value = "";
                        console.warn("Product not found.");
                    }
                } catch (error) {
                    console.error("Error fetching product:", error);
                }
            }
        });
    }

    // Change unit display based on withdrawal type
    if (withdrawalType && unitLabel) {
        withdrawalType.addEventListener("change", function () {
            unitLabel.textContent = withdrawalType.value === "volume" ? "mL" : "units";
        });
    }
});




document.addEventListener("DOMContentLoaded", function () {
    const searchInput = document.getElementById("searchInput");
    const productTable = document.getElementById("productTable").getElementsByTagName("tbody")[0];

    searchInput.addEventListener("keyup", function () {
        const filterValue = searchInput.value.toLowerCase();
        const rows = productTable.getElementsByTagName("tr");

        for (let row of rows) {
            const productName = row.cells[0]?.textContent.toLowerCase() || "";
            const productCode = row.cells[1]?.textContent.toLowerCase() || "";
            const supplier = row.cells[5]?.textContent.toLowerCase() || "";

            // Show or hide rows based on search query
            if (productName.includes(filterValue) || productCode.includes(filterValue) || supplier.includes(filterValue)) {
                row.style.display = "";
            } else {
                row.style.display = "none";
            }
        }
    });
});
