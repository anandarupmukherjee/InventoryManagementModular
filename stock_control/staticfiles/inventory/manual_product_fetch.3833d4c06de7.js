document.addEventListener("DOMContentLoaded", function () {
    const fetchButton = document.getElementById("fetch-manual-details");
    const productDropdown = document.getElementById("id_product_dropdown");

    if (fetchButton && productDropdown) {
        fetchButton.addEventListener("click", async function () {
            const selectedId = productDropdown.value;
            if (!selectedId) return alert("Please select a product first.");

            try {
                const response = await fetch(`/get-product-by-id/?id=${selectedId}`);
                if (!response.ok) throw new Error("Product not found");

                const data = await response.json();
                document.getElementById("id_product_name").value = data.name || "";
                document.getElementById("stock-display").textContent = data.current_stock ?? "";
                document.getElementById("units-display").textContent = data.units_per_quantity ?? "";
                document.getElementById("id_units_per_quantity").value = data.units_per_quantity ?? "";
                document.getElementById("id_barcode_manual").value = data.product_code || "";
                document.getElementById("manual-stock-display").textContent = data.current_stock ?? "";
                document.getElementById("manual-units-display").textContent = data.units_per_quantity ?? "";

                const volumeSection = document.getElementById("volume-withdrawal-section");
                volumeSection.style.display = data.product_feature === "volume" ? "block" : "none";
            } catch (err) {
                console.error("❌ Error fetching product by ID:", err);
                alert("Error fetching product info.");
            }
        });
    }
});
