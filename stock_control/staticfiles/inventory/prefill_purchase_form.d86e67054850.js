document.addEventListener("DOMContentLoaded", function () {
    const params = new URLSearchParams(window.location.search);
    const productCode = params.get("product_code");
    const productName = params.get("product_name");

    if (productCode) {
        const codeField = document.getElementById("id_product_code");
        if (codeField) codeField.value = productCode;
    }

    if (productName) {
        const nameField = document.getElementById("id_product_name");
        if (nameField) nameField.value = productName;
    }
});
