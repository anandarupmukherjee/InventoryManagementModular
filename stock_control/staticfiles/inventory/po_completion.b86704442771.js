document.addEventListener("DOMContentLoaded", () => {
  // Utility: fetch product name from product code
  async function fetchProductName(productCode) {
    if (!productCode) return;

    try {
      const res = await fetch(`/get-product-by-barcode/?barcode=${productCode}`);
      const data = await res.json();
      document.getElementById("id_product_name").value = data.name || "";
    } catch (err) {
      console.error("Failed to fetch product name:", err);
    }
  }

  // Fill form from table "Complete" button
  document.querySelectorAll(".fill-form-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      const code = btn.dataset.productCode;
      document.getElementById("id_product_code").value = code;
      document.getElementById("id_quantity_ordered").value = btn.dataset.quantity;
      document.getElementById("id_status").value = "Delivered";
      fetchProductName(code);
    });
  });

  // Barcode parsing from raw scan
  const barcodeInput = document.getElementById("po-barcode");
  barcodeInput?.addEventListener("change", async () => {
    const raw = barcodeInput.value.trim();
    if (!raw) return;

    try {
      const res = await fetch(`/parse-barcode/?raw=${encodeURIComponent(raw)}`);
      const data = await res.json();
      if (data.error) throw new Error(data.error);

      document.getElementById("id_barcode").value = raw;
      document.getElementById("id_lot_number").value = data.lot_number || "";

      if (data.expiry_date) {
        const [d, m, y] = data.expiry_date.split(".");
        document.getElementById("id_expiry_date").value = `${y}-${m}-${d}`;
      }

      document.getElementById("id_product_code").value = data.product_code || "";
      fetchProductName(data.product_code);
    } catch (err) {
      alert("Error: " + err.message);
      console.error("Barcode parsing failed:", err);
    }
  });

  // Live fetch when manually editing product code
  const productCodeInput = document.getElementById("id_product_code");
  productCodeInput?.addEventListener("change", () => {
    const code = productCodeInput.value.trim();
    fetchProductName(code);
  });

  // AJAX form submission to update table status dynamically
  const poForm = document.querySelector("form[method='post']");
  poForm?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const formData = new FormData(poForm);

    try {
      const res = await fetch(window.location.href, {
        method: "POST",
        body: formData,
        headers: {
          "X-Requested-With": "XMLHttpRequest"
        }
      });

      if (res.ok) {
        const code = document.getElementById("id_product_code").value;
        const row = document.querySelector(`tr[data-product-code="${code}"]`);
        if (row) {
          row.querySelector("td:nth-child(5)").innerHTML = '<span class="status-delivered">✅ Delivered</span>';
          row.querySelector("td:nth-child(6)").innerHTML = '<span class="text-muted">Complete</span>';
          row.classList.remove("delayed-row");

          // Optional: highlight updated row
          row.style.transition = "background-color 0.5s";
          row.style.backgroundColor = "#d4edda"; // light green
          setTimeout(() => row.style.backgroundColor = "", 1500);
        }
        poForm.reset();
      } else {
        alert("Form submission failed.");
      }
    } catch (err) {
      alert("Error submitting form: " + err.message);
      console.error(err);
    }
  });
});
