document.addEventListener("DOMContentLoaded", function () {
    const modelSelector = document.getElementById("report_type");
    const fieldContainer = document.getElementById("field-container");

    const modelFields = {
        "withdrawals": ["timestamp", "product", "product_code", "quantity", "withdrawal_type", "barcode", "user"],
        "stock": ["product_code", "name", "supplier", "threshold", "lead_time", "current_stock"],
        "purchase_orders": ["product", "quantity_ordered", "ordered_by", "order_date", "expected_delivery", "status"]
    };

    function updateFields() {
        const selectedModel = modelSelector.value;
        const fields = modelFields[selectedModel] || [];
        fieldContainer.innerHTML = ""; // Clear current fields

        fields.forEach(field => {
            const checkbox = document.createElement("input");
            checkbox.type = "checkbox";
            checkbox.name = "fields";
            checkbox.value = field;
            checkbox.id = `field_${field}`;
            checkbox.checked = true;

            const label = document.createElement("label");
            label.htmlFor = checkbox.id;
            label.textContent = field.replace(/_/g, " ").replace(/\b\w/g, char => char.toUpperCase());

            const wrapper = document.createElement("div");
            wrapper.appendChild(checkbox);
            wrapper.appendChild(label);

            fieldContainer.appendChild(wrapper);
        });
    }

    if (modelSelector && fieldContainer) {
        modelSelector.addEventListener("change", updateFields);
        updateFields(); // Initialize on page load
    } else {
        console.warn("📊 report_type or field-container missing.");
    }
});
