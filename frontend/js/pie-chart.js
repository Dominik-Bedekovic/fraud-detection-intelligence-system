let pieChart;

async function loadDashboardStats() {
  const token = localStorage.getItem("token");
  const res = await fetch("/dashboard/stats", {
    headers: {
    "Authorization": `Bearer ${token}`,
    },
  }
  );
  const data = await res.json();

  document.getElementById("totalTransactions").innerText =
    data.total_transactions;

  document.getElementById("fraudsDetected").innerText = data.fraud_transactions;

  document.getElementById("fraudRate").innerText = data.fraud_rate + "%";

  const ctx = document.getElementById("pieChart");

  if (pieChart) pieChart.destroy();

  pieChart = new Chart(ctx, {
    type: "pie",
    data: {
      labels: ["Fraud", "Not Fraud"],
      datasets: [
        {
          data: [
            data.fraud_transactions,
            data.total_transactions - data.fraud_transactions,
          ],
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
    },
  });
}
loadDashboardStats();

setInterval(() => {
  loadDashboardStats();
}, 60000);
