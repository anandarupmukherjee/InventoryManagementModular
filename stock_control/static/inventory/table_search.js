window.addEventListener("load", function () {
    const searchProduct = document.getElementById("searchProduct");
    const searchWithdrawal = document.getElementById("searchWithdrawal");
    const searchAdmin = document.getElementById("searchAdmin");  // ✅ new
    const searchRegistrations = document.getElementById("searchRegistrations");
    const searchLowStockLots = document.getElementById("searchLowStockLots");
    const searchExpiredLots = document.getElementById("searchExpiredLots");
    const productTable = document.getElementById("productTable");
    const withdrawalTable = document.getElementById("withdrawalTable");
    const registrationTable = document.getElementById("registrationTable");
    const lowStockLotsTable = document.getElementById("lowStockLotsTable");
    const expiredLotsTable = document.getElementById("expiredLotsTable");
    const adminTable = document.getElementById("adminTable");  // ✅ new
    const searchLowStock = document.getElementById("searchLowStock");
    const lowStockTable = document.getElementById("lowStockTable");

    console.log("🔍 Checking elements:");
    console.log("🔍 searchProduct:", searchProduct ? "✅ Found" : "❌ Not Found");
    console.log("🔍 productTable:", productTable ? "✅ Found" : "❌ Not Found");
    console.log("🔍 searchWithdrawal:", searchWithdrawal ? "✅ Found" : "❌ Not Found");
    console.log("🔍 withdrawalTable:", withdrawalTable ? "✅ Found" : "❌ Not Found");
    console.log("🔍 searchRegistrations:", searchRegistrations ? "✅ Found" : "❌ Not Found");
    console.log("🔍 registrationTable:", registrationTable ? "✅ Found" : "❌ Not Found");
    console.log("🔍 searchLowStockLots:", searchLowStockLots ? "✅ Found" : "❌ Not Found");
    console.log("🔍 lowStockLotsTable:", lowStockLotsTable ? "✅ Found" : "❌ Not Found");
    console.log("🔍 searchExpiredLots:", searchExpiredLots ? "✅ Found" : "❌ Not Found");
    console.log("🔍 expiredLotsTable:", expiredLotsTable ? "✅ Found" : "❌ Not Found");
    console.log("🔍 searchAdmin:", searchAdmin ? "✅ Found" : "❌ Not Found");
    console.log("🔍 adminTable:", adminTable ? "✅ Found" : "❌ Not Found");
    console.log("🔍 searchLowStock:", searchLowStock ? "✅ Found" : "❌ Not Found");
    console.log("🔍 lowStockTable:", lowStockTable ? "✅ Found" : "❌ Not Found");

    function setupTableSearch(searchInputId, tableId, columnIndexes) {
        const searchInput = document.getElementById(searchInputId);
        const table = document.getElementById(tableId);

        if (!searchInput || !table) {
            console.error(`❌ Error: Missing elements for search in ${tableId}`);
            return;
        }

        console.log(`🔍 Setting up search for table: ${tableId}`);

        searchInput.addEventListener("keyup", function () {
            const filterValue = searchInput.value.toLowerCase();
            const tableBody = table.getElementsByTagName("tbody")[0];
            const rows = tableBody.getElementsByTagName("tr");

            for (let row of rows) {
                const cells = row.getElementsByTagName("td");
                let match = false;

                columnIndexes.forEach(index => {
                    if (cells[index] && cells[index].textContent.toLowerCase().includes(filterValue)) {
                        match = true;
                    }
                });

                row.style.display = match ? "" : "none";
            }
        });

        console.log(`✅ Search enabled for table: ${tableId}`);
    }

    if (searchProduct && productTable) {
        setupTableSearch("searchProduct", "productTable", [0, 1, 7]); // Adjust to actual table
    }

    if (searchWithdrawal && withdrawalTable) {
        // Columns: 0 Timestamp, 1 Product, 2 Location, 3 Full, 4 Partial, 5 Type, 6 Code, 7 User
        setupTableSearch("searchWithdrawal", "withdrawalTable", [1, 6, 7]);
    }

    if (searchRegistrations && registrationTable) {
        // Columns: 0 Timestamp, 1 Delivery, 2 Location, 3 Barcode, 4 Product, 5 Lot, 6 Expiry, 7 Stock
        setupTableSearch("searchRegistrations", "registrationTable", [2, 3, 4, 5, 6]);
    }

    if (searchLowStockLots && lowStockLotsTable) {
        // Columns: 0 Product, 1 Lot, 2 Lot Stock, 3 Total Stock, 4 Threshold, 5 Expiry, 6 Location
        setupTableSearch("searchLowStockLots", "lowStockLotsTable", [0, 1, 5, 6]);
    }

    if (searchExpiredLots && expiredLotsTable) {
        // Columns: 0 Product, 1 Lot, 2 Expiry, 3 Stock, 4 Location
        setupTableSearch("searchExpiredLots", "expiredLotsTable", [0, 1, 4]);
    }

    if (searchAdmin && adminTable) {
        setupTableSearch("searchAdmin", "adminTable", [0, 1]); // e.g., Code, Name, Supplier
    }
    
    if (searchLowStock && lowStockTable) {
        setupTableSearch("searchLowStock", "lowStockTable", [0, 1]); // Code, Name
    }
    


});
