let trendChart;

async function loadTrendChart() {
  const res = await fetch("/transactions/recent");
  const data = await res.json();

  const sorted = data
    .filter((t) => t.created_at)
    .sort((a, b) => new Date(a.created_at) - new Date(b.created_at));

  const labels = sorted.map((t) => {
    const date = new Date(t.created_at);

    return date.toLocaleString([], {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  });

  const values = sorted.map((t) => t.probability ?? 0);

  const ctx = document.getElementById("trendChart");

  if (trendChart) trendChart.destroy();

  trendChart = new Chart(ctx, {
    type: "line",
    data: {
      labels,
      datasets: [
        {
          label: "Fraud Probability %",
          data: values,
          borderWidth: 2,
          tension: 0.3,
          pointRadius: 3,
          pointHoverRadius: 5,
          clip: false,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,

      layout: {
        padding: {
          top: 10,
          right: 10,
          left: 10,
          bottom: 5,
        },
      },

      scales: {
        x: {
          ticks: {
            maxRotation: 0,
            autoSkip: true,
            maxTicksLimit: 6,
          },
        },
        y: {
          min: 0,
          max: 100,
          ticks: {
            padding: 6,
          },
        },
      },
    },
  });
}

loadTrendChart();

setInterval(() => {
  loadTrendChart();
}, 60000);
