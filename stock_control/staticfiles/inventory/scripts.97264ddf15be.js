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

        if (barcodeValue.length > 2) {  // Only trigger request if input is valid
            fetch(`/inventory/get-product-by-barcode/?barcode=${barcodeValue}`)
                .then(response => response.json())
                .then(data => {
                    if (data.id) {
                        productSelect.value = data.id;
                    } else {
                        productSelect.value = ""; // Reset selection if no match
                    }
                })
                .catch(error => console.error("Error fetching product:", error));
        }
    });

    // Change unit display based on withdrawal type
    withdrawalType.addEventListener("change", function () {
        unitLabel.textContent = withdrawalType.value === "volume" ? "mL" : "units";
    });
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
