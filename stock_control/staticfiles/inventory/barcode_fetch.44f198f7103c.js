document.addEventListener("DOMContentLoaded", function () {
    const barcodeInput = document.getElementById("id_barcode");

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
            volumeSection.style.display = data.product_feature === "volume" ? "block" : "none";
        } catch (err) {
            console.error("Error fetching product by barcode:", err);
        }
    }

    if (barcodeInput) {
        barcodeInput.addEventListener("input", function () {
            const barcodeValue = barcodeInput.value.trim();
            if (barcodeValue.length > 3) fetchProductDetailsByBarcode(barcodeValue);
        });
    }
});
