document.addEventListener("DOMContentLoaded", function () {

// ##################### ANALYSIS ##################

console.log("✅ Analysis & Forecasting Charts Loaded");

    function getChartData(canvasId) {
        const element = document.getElementById(canvasId);
        if (!element) {
            console.error(`❌ Element with ID '${canvasId}' not found.`);
            return null;
        }
        try {
            return {
                labels: JSON.parse(element.getAttribute("data-labels") || "[]"),
                stock: JSON.parse(element.getAttribute("data-stock") || "[]"),
                thresholds: JSON.parse(element.getAttribute("data-thresholds") || "[]"),
                dates: JSON.parse(element.getAttribute("data-dates") || "[]"),
                withdrawals: JSON.parse(element.getAttribute("data-withdrawals") || "[]"),
                sma7: JSON.parse(element.getAttribute("data-sma7") || "[]"),
                sma14: JSON.parse(element.getAttribute("data-sma14") || "[]"),
                forecastDates: JSON.parse(element.getAttribute("data-forecast-dates") || "[]"),
                forecastValues: JSON.parse(element.getAttribute("data-forecast-values") || "[]")
            };
        } catch (error) {
            console.error(`❌ Error parsing data for '${canvasId}':`, error);
            return null;
        }
    }

    function renderChart(canvasId, chartType, datasets, labels) {
        const ctx = document.getElementById(canvasId);
        if (ctx) {
            new Chart(ctx.getContext("2d"), {
                type: chartType,
                data: { labels: labels, datasets: datasets },
                options: { responsive: true, maintainAspectRatio: false, scales: { y: { beginAtZero: true } } }
            });
        } else {
            console.warn(`⚠ Chart '${canvasId}' not found.`);
        }
    }

    // ✅ Stock Levels Chart
    const stockData = getChartData("stockLevelsChart");
    if (stockData && stockData.labels.length > 0) {
        renderChart("stockLevelsChart", "bar", [
            { label: "Current Stock", data: stockData.stock, backgroundColor: "blue" },
            { label: "Threshold", data: stockData.thresholds, backgroundColor: "red" }
        ], stockData.labels);
    }

    // ✅ Withdrawals Over Time Chart
    const withdrawalData = getChartData("withdrawalsOverTimeChart");
    if (withdrawalData && withdrawalData.dates.length > 0) {
        renderChart("withdrawalsOverTimeChart", "line", [
            { label: "Total Withdrawals", data: withdrawalData.withdrawals, borderColor: "green", fill: false }
        ], withdrawalData.dates);
    }

    // ✅ Forecast Chart
    const forecastData = getChartData("forecastChart");
    if (forecastData && forecastData.forecastValues.length > 0) {
        renderChart("forecastChart", "line", [
            { label: "7-Day SMA", data: forecastData.sma7, borderColor: "orange", fill: false },
            { label: "14-Day SMA", data: forecastData.sma14, borderColor: "red", fill: false },
            { label: "Forecast (Next 7 Days)", data: [...Array(forecastData.withdrawals.length).fill(null), ...forecastData.forecastValues], borderColor: "purple", borderDash: [5, 5], fill: false }
        ], [...forecastData.dates, ...forecastData.forecastDates]);
    }

    // ✅ Open Charts in Modal View
    function openModal(chartId) {
        const modal = document.getElementById("chartModal");
        const modalChartCanvas = document.getElementById("modalChart");
        const chartData = getChartData(chartId);

        if (!chartData) return;

        modal.style.display = "block";

        // Destroy existing chart before creating a new one
        if (window.modalChartInstance) {
            window.modalChartInstance.destroy();
        }

        window.modalChartInstance = new Chart(modalChartCanvas.getContext("2d"), {
            type: "line",
            data: {
                labels: chartData.dates,
                datasets: [
                    { label: "Actual Withdrawals", data: chartData.withdrawals, borderColor: "blue", fill: false },
                    { label: "7-Day SMA", data: chartData.sma7, borderColor: "orange", fill: false },
                    { label: "14-Day SMA", data: chartData.sma14, borderColor: "red", fill: false },
                    { label: "Forecast", data: chartData.forecastValues, borderColor: "purple", fill: false }
                ]
            },
            options: { responsive: true, maintainAspectRatio: false }
        });
    }

    function closeModal() {
        document.getElementById("chartModal").style.display = "none";
    }

    document.querySelectorAll(".chart-tile").forEach(tile => {
        tile.addEventListener("click", function () {
            openModal(this.querySelector("canvas").id);
        });
    });

    document.querySelector(".close-modal").addEventListener("click", closeModal);

});

