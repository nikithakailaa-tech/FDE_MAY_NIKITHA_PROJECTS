// Load dashboard on page load
window.onload = async function () {
    requireAuth();
    await loadStats();
}

async function loadStats() {
    try {
        const stats = await getDashboardStats();

        document.getElementById("total").innerText = stats.total_complaints || 0;
        document.getElementById("open").innerText = stats.open || 0;
        document.getElementById("in_progress").innerText = stats.in_progress || 0;
        document.getElementById("resolved").innerText = stats.resolved || 0;
        document.getElementById("closed").innerText = stats.closed || 0;
        document.getElementById("escalated").innerText = stats.escalated || 0;
        document.getElementById("sla_breached").innerText = stats.sla_breached || 0;
        document.getElementById("avg_rating").innerText = stats.average_rating || 0;

    } catch (err) {
        console.error("Failed to load stats", err);
    }
}