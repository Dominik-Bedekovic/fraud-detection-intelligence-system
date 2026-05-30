async function loadRecentTransactions() {
  const token = localStorage.getItem("token");

  const res = await fetch("/transactions/recent", {
    headers: {
    "Authorization": `Bearer ${token}`,
    },
  }
  );
  const data = await res.json();

  const table = document.querySelector(".data-table");

  table.innerHTML = `
    <thead>
      <tr>
        <th>ID</th>
        <th>Type</th>
        <th>Amount</th>
        <th>Prediction</th>
        <th>Probability</th>
      </tr>
    </thead>
    <tbody>
      ${data
        .map(
          (t) => `
        <tr>
          <td>${t.id}</td>
          <td>${t.type}</td>
          <td>${t.amount}</td>
          <td>${t.prediction ?? "—"}</td>
          <td>${t.probability ?? "—"}</td>
        </tr>
      `,
        )
        .join("")}
    </tbody>
  `;
}

loadRecentTransactions();
