document.addEventListener("DOMContentLoaded", () => {
    const modelSelector = document.getElementById("report_type");
    const fieldContainer = document.getElementById("field-container");

    const modelFields = {
        "withdrawals": ["timestamp", "product_name", "product_code", "quantity", "withdrawal_type", "barcode", "user"],
        "stock": ["product_code", "name", "supplier", "threshold", "lead_time"],
        "purchase_orders": ["product_name", "product_code", "lot_number", "expiry_date", "quantity_ordered", "ordered_by", "order_date", "expected_delivery", "status"]
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
            label.htmlFor = checkbox.id;
            label.textContent = field.replace(/_/g, " ").replace(/\b\w/g, c => c.toUpperCase());

            const div = document.createElement("div");
            div.appendChild(checkbox);
            div.appendChild(label);

            fieldContainer.appendChild(div);
        });
    }

    if (modelSelector && fieldContainer) {
        modelSelector.addEventListener("change", updateFields);
        updateFields(); // Load default on page load
    }
});
