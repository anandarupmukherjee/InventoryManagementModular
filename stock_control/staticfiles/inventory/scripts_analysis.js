document.addEventListener("DOMContentLoaded", function () {

    function getChartData(canvasId) {
        const element = document.getElementById(canvasId);
        if (!element) {
            console.error(`Element with ID '${canvasId}' not found.`);
            return null;
        }
        try {
            return {
                labels: JSON.parse(element.getAttribute("data-labels") || "[]"),
                stock: JSON.parse(element.getAttribute("data-stock") || "[]"),
                thresholds: JSON.parse(element.getAttribute("data-thresholds") || "[]"),
                dates: JSON.parse(element.getAttribute("data-dates") || "[]"),
                withdrawals: JSON.parse(element.getAttribute("data-withdrawals") || "[]"),
                counts: JSON.parse(element.getAttribute("data-counts") || "[]"),
                sma7: JSON.parse(element.getAttribute("data-sma7") || "[]"),
                sma14: JSON.parse(element.getAttribute("data-sma14") || "[]"),
                forecastDates: JSON.parse(element.getAttribute("data-forecast-dates") || "[]"),
                forecastValues: JSON.parse(element.getAttribute("data-forecast-values") || "[]"),
                names: JSON.parse(element.getAttribute("data-names") || "[]"),
                fullNames: JSON.parse(element.getAttribute("data-fullnames") || "[]"),
                codes: JSON.parse(element.getAttribute("data-codes") || "[]"),
                leadTimes: JSON.parse(element.getAttribute("data-lead-times") || "[]"),
                runOutDays: JSON.parse(element.getAttribute("data-run-out-days") || "[]"),
                reorderDays: JSON.parse(element.getAttribute("data-reorder-days") || "[]"),
                topConsumedNames: JSON.parse(element.getAttribute("data-names") || "[]"),
                topConsumedQuantities: JSON.parse(element.getAttribute("data-quantities") || "[]")
            };
        } catch (error) {
            console.error(`Error parsing data for '${canvasId}':`, error);
            return null;
        }
    }

    function renderChart(canvasId, chartType, datasets, labels, tooltipTitles) {
        const ctx = document.getElementById(canvasId);
        if (ctx) {
            new Chart(ctx.getContext("2d"), {
                type: chartType,
                data: { labels: labels, datasets: datasets },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: (function(){
                            const base = { beginAtZero: true, ticks: { precision: 0 } };
                            // Add axis titles for clarity
                            if (canvasId === 'runOutForecastChart' || canvasId === 'leadTimesChart') {
                                base.title = { display: true, text: 'Days' };
                            } else if (canvasId === 'stockLevelsChart') {
                                base.title = { display: true, text: 'Units' };
                            } else if (canvasId === 'withdrawalsOverTimeChart' || canvasId === 'forecastChart' || canvasId === 'topConsumedItemsChart' || canvasId === 'locationWithdrawalsChart') {
                                base.title = { display: true, text: 'Quantity' };
                            } else if (canvasId === 'delayedDeliveriesChart') {
                                base.title = { display: true, text: 'Count' };
                            }
                            return base;
                        })()
                    },
                    plugins: {
                        legend: { display: true },
                        title: {
                            display: true,
                            text: canvasId.replace(/([A-Z])/g, ' $1').trim()
                        },
                        tooltip: {
                            callbacks: {
                                title: function(context) {
                                    if (tooltipTitles && tooltipTitles.length) {
                                        const idx = context[0].dataIndex;
                                        return tooltipTitles[idx] || context[0].label;
                                    }
                                    return context[0].label;
                                }
                            }
                        }
                    }
                }
            });
        }
    }

    // ✅ Render Stock Levels Chart
    const stockData = getChartData("stockLevelsChart");
    if (stockData) {
        const labels = (stockData.codes && stockData.codes.length) ? stockData.codes : stockData.labels;
        renderChart("stockLevelsChart", "bar", [
            { label: "Current Stock", data: stockData.stock, backgroundColor: "blue" },
            { label: "Threshold", data: stockData.thresholds, backgroundColor: "red" }
        ], labels, stockData.labels);
    }

    // ✅ Render Withdrawals Over Time Chart
    const withdrawalData = getChartData("withdrawalsOverTimeChart");
    if (withdrawalData) {
        renderChart("withdrawalsOverTimeChart", "line", [
            { label: "Total Withdrawals", data: withdrawalData.withdrawals, borderColor: "green", fill: false }
        ], withdrawalData.dates);
    }

    // ✅ Render Forecast Chart
    const forecastData = getChartData("forecastChart");
    if (forecastData) {
        renderChart("forecastChart", "line", [
            { label: "7-Day SMA", data: forecastData.sma7, borderColor: "orange", fill: false },
            { label: "14-Day SMA", data: forecastData.sma14, borderColor: "red", fill: false },
            { label: "Forecast (Next 7 Days)", data: forecastData.forecastValues, borderColor: "purple", borderDash: [5, 5], fill: false }
        ], [...forecastData.dates, ...forecastData.forecastDates]);
    }

    // ✅ Render Lead Times Chart
    const leadTimesData = getChartData("leadTimesChart");
    if (leadTimesData) {
        const labels = (leadTimesData.codes && leadTimesData.codes.length) ? leadTimesData.codes : leadTimesData.names;
        renderChart("leadTimesChart", "bar", [
            { label: "Lead Time (Days)", data: leadTimesData.leadTimes, backgroundColor: "blue" }
        ], labels, leadTimesData.names);
    }

    // ✅ Render Run-Out Forecast Chart
    const runOutData = getChartData("runOutForecastChart");
    if (runOutData) {
        const labels = (runOutData.codes && runOutData.codes.length) ? runOutData.codes : runOutData.names;
        renderChart("runOutForecastChart", "bar", [
            { label: "Days Until Run-Out", data: runOutData.runOutDays, backgroundColor: "red" },
            { label: "Days Until Reorder", data: runOutData.reorderDays, backgroundColor: "orange" }
        ], labels, runOutData.names);
    }

    // ✅ Render Top Consumed Items Chart
    const topConsumedData = getChartData("topConsumedItemsChart");
    if (topConsumedData) {
        const labels = (topConsumedData.codes && topConsumedData.codes.length) ? topConsumedData.codes : topConsumedData.topConsumedNames;
        renderChart("topConsumedItemsChart", "bar", [
            { label: "Top 5 Consumed Items", data: topConsumedData.topConsumedQuantities, backgroundColor: "purple" }
        ], labels, topConsumedData.topConsumedNames);
    }

    // ✅ Location-specific withdrawals chart
    const locData = getChartData("locationWithdrawalsChart");
    if (locData) {
        renderChart("locationWithdrawalsChart", "bar", [
            { label: "Withdrawn Qty", data: locData.topConsumedQuantities.length ? locData.topConsumedQuantities : locData['quantities'] || locData.counts || [], backgroundColor: "teal" }
        ], locData.topConsumedNames.length ? locData.topConsumedNames : locData.names);
    }

    // ✅ Delayed deliveries over time
    const delayedData = getChartData("delayedDeliveriesChart");
    if (delayedData) {
        renderChart("delayedDeliveriesChart", "line", [
            { label: "Delayed Deliveries", data: delayedData.counts, borderColor: "#c2410c", fill: false }
        ], delayedData.dates);
    }

    // ✅ Deleted lots top 10 (qty by product code)
    const deletedLotsData = getChartData("deletedLotsChart");
    if (deletedLotsData) {
        const dataSeries = deletedLotsData.topConsumedQuantities || deletedLotsData.quantities || deletedLotsData.counts || [];
        renderChart("deletedLotsChart", "bar", [
            { label: "Deleted Qty", data: dataSeries, backgroundColor: "#7c3aed" }
        ], deletedLotsData.names, deletedLotsData.fullNames && deletedLotsData.fullNames.length ? deletedLotsData.fullNames : deletedLotsData.names);
    }

    // ✅ Upcoming expiries (qty within 30 days) by product code
    const upcomingExpiryData = getChartData("upcomingExpiryChart");
    if (upcomingExpiryData) {
        const dataSeries = upcomingExpiryData.topConsumedQuantities || upcomingExpiryData.quantities || upcomingExpiryData.counts || [];
        const labels = upcomingExpiryData.names || upcomingExpiryData.codes;
        renderChart("upcomingExpiryChart", "bar", [
            { label: "Qty Expiring", data: dataSeries, backgroundColor: "#059669" }
        ], labels, upcomingExpiryData.fullNames && upcomingExpiryData.fullNames.length ? upcomingExpiryData.fullNames : labels);
    }

    // ===== Modal interactions =====
    let modalChartInstance = null;
    window.openModal = function (chartId) {
        const modal = document.getElementById('chartModal');
        const modalCanvas = document.getElementById('modalChart');
        if (!modal || !modalCanvas) return;

        // If a chart already exists, destroy it cleanly before creating a new one
        if (modalChartInstance && typeof modalChartInstance.destroy === 'function') {
            try { modalChartInstance.destroy(); } catch (_) {}
            modalChartInstance = null;
        }
        // Clear previous modal chart drawing
        const ctx = modalCanvas.getContext('2d');
        ctx && ctx.clearRect(0, 0, modalCanvas.width, modalCanvas.height);

        // Recreate data like the small chart, based on chartId
        let data = getChartData(chartId);
        if (!data) return;

        let type = 'bar';
        let datasets = [];
        let labels = [];
        let tooltipTitles = null;

        switch (chartId) {
            case 'stockLevelsChart':
                type = 'bar';
                datasets = [
                    { label: 'Current Stock', data: data.stock, backgroundColor: 'blue' },
                    { label: 'Threshold', data: data.thresholds, backgroundColor: 'red' },
                ];
                labels = (data.codes && data.codes.length) ? data.codes : data.labels;
                tooltipTitles = data.labels || null;
                break;
            case 'withdrawalsOverTimeChart':
                type = 'line';
                datasets = [
                    { label: 'Total Withdrawals', data: data.withdrawals, borderColor: 'green', fill: false },
                ];
                labels = data.dates;
                break;
            case 'forecastChart':
                type = 'line';
                datasets = [
                    { label: '7-Day SMA', data: data.sma7, borderColor: 'orange', fill: false },
                    { label: '14-Day SMA', data: data.sma14, borderColor: 'red', fill: false },
                    { label: 'Forecast (Next 7 Days)', data: data.forecastValues, borderColor: 'purple', borderDash: [5, 5], fill: false },
                ];
                labels = [...data.dates, ...data.forecastDates];
                break;
            case 'leadTimesChart':
                type = 'bar';
                datasets = [
                    { label: 'Lead Time (Days)', data: data.leadTimes, backgroundColor: 'blue' },
                ];
                labels = (data.codes && data.codes.length) ? data.codes : data.names;
                tooltipTitles = data.names || null;
                break;
            case 'runOutForecastChart':
                type = 'bar';
                datasets = [
                    { label: 'Days Until Run-Out', data: data.runOutDays, backgroundColor: 'red' },
                    { label: 'Days Until Reorder', data: data.reorderDays, backgroundColor: 'orange' },
                ];
                labels = (data.codes && data.codes.length) ? data.codes : data.names;
                // Use full names in tooltip even when codes are on the axis
                tooltipTitles = data.names || null;
                break;
            case 'topConsumedItemsChart':
                type = 'bar';
                datasets = [
                    { label: 'Top 5 Consumed Items', data: data.topConsumedQuantities, backgroundColor: 'purple' },
                ];
                labels = (data.codes && data.codes.length) ? data.codes : data.topConsumedNames;
                tooltipTitles = data.topConsumedNames || null;
                break;
            case 'locationWithdrawalsChart':
                type = 'bar';
                datasets = [
                    { label: 'Withdrawn Qty', data: (data.topConsumedQuantities && data.topConsumedQuantities.length) ? data.topConsumedQuantities : (data.quantities || data.counts || []), backgroundColor: 'teal' },
                ];
                labels = (data.topConsumedNames && data.topConsumedNames.length) ? data.topConsumedNames : data.names;
                break;
            case 'delayedDeliveriesChart':
                type = 'line';
                datasets = [
                    { label: 'Delayed Deliveries', data: data.counts, borderColor: '#c2410c', fill: false },
                ];
                labels = data.dates;
                break;
            case 'deletedLotsChart':
                type = 'bar';
                datasets = [
                    { label: 'Deleted Qty', data: data.topConsumedQuantities || data.quantities || data.counts || [], backgroundColor: '#7c3aed' },
                ];
                labels = data.names;
                tooltipTitles = (data.fullNames && data.fullNames.length) ? data.fullNames : (data.names || null);
                break;
            case 'upcomingExpiryChart':
                type = 'bar';
                datasets = [
                    { label: 'Qty Expiring', data: data.topConsumedQuantities || data.quantities || data.counts || [], backgroundColor: '#059669' },
                ];
                labels = data.names || data.codes;
                tooltipTitles = (data.fullNames && data.fullNames.length) ? data.fullNames : labels || null;
                break;
            default:
                return;
        }

        modalChartInstance = new Chart(modalCanvas.getContext('2d'), {
            type,
            data: { labels, datasets },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: { y: { beginAtZero: true, ticks: { precision: 0 } } },
                plugins: {
                    legend: { display: true },
                    title: { display: true, text: chartId.replace(/([A-Z])/g, ' $1').trim() },
                    tooltip: {
                        callbacks: {
                            title: function(context) {
                                if (tooltipTitles && tooltipTitles.length) {
                                    const idx = context[0].dataIndex;
                                    return tooltipTitles[idx] || context[0].label;
                                }
                                return context[0].label;
                            }
                        }
                    }
                }
            }
        });

        modal.style.display = 'block';
    };

    window.closeModal = function () {
        const modal = document.getElementById('chartModal');
        if (modalChartInstance && typeof modalChartInstance.destroy === 'function') {
            try { modalChartInstance.destroy(); } catch (_) {}
            modalChartInstance = null;
        }
        if (modal) modal.style.display = 'none';
    };

    // Close modal when clicking outside content
    const modal = document.getElementById('chartModal');
    modal?.addEventListener('click', (e) => {
        if (e.target === modal) closeModal();
    });
});
