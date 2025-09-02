document.addEventListener("DOMContentLoaded", function () {
    const searchInput = document.getElementById("searchInput");
    const tableBody = document.getElementById("productTable")?.getElementsByTagName("tbody")[0];

    if (searchInput && tableBody) {
        searchInput.addEventListener("keyup", function () {
            const filterValue = searchInput.value.toLowerCase();
            const rows = tableBody.getElementsByTagName("tr");

            for (let row of rows) {
                const timestampText = row.cells[0]?.textContent.toLowerCase() || "";
                const productNameText = row.cells[1]?.textContent.toLowerCase() || "";
                const usernameText = row.cells[5]?.textContent.toLowerCase() || "";

                const isVisible = (
                    timestampText.includes(filterValue) ||
                    productNameText.includes(filterValue) ||
                    usernameText.includes(filterValue)
                );

                row.style.display = isVisible ? "" : "none";
            }
        });
    } else {
        console.warn("🔍 Search input or table body not found for table search.");
    }
});
