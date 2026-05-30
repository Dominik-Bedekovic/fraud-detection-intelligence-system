let filters = {
  type: "",
  fraud: "",
};

document.addEventListener("click", (e) => {
  if (!e.target.classList.contains("chip")) return;

  const parent = e.target.closest(".filter-buttons");
  if (!parent) return;

  const key = parent.dataset.filter;
  const value = e.target.dataset.value;

  filters[key] = value;

  parent.querySelectorAll(".chip").forEach((b) => b.classList.remove("active"));

  e.target.classList.add("active");

  loadTransactions();
});

async function loadTransactions() {
  let url = "/transactions";
  const params = [];

  if (filters.type) params.push(`type=${filters.type}`);
  if (filters.fraud !== "") params.push(`is_fraud=${filters.fraud === "true"}`);

  if (params.length) url += "?" + params.join("&");

  const res = await fetch(url);
  const data = await res.json();

  const tbody = document.getElementById("transactionsBody");

  if (!data || data.length === 0) {
    tbody.innerHTML = `
            <tr class="empty-row">
              <td colspan="5">No transactions found</td>
            </tr>
          `;
    return;
  }

  tbody.innerHTML = data
    .map(
      (t) => `
          <tr class="${t.prediction === 1 ? "fraud-row" : ""}">
            <td>${t.id}</td>
            <td>${t.type}</td>
            <td>${t.amount}</td>
            <td>${t.prediction ?? "—"}</td>
            <td>${t.probability ?? "—"}</td>
          </tr>
        `,
    )
    .join("");
}

function resetFilters() {
  filters = { type: "", fraud: "" };

  document.querySelectorAll(".filter-buttons").forEach((group) => {
    group.querySelectorAll(".chip").forEach((b) => {
      b.classList.toggle("active", b.dataset.value === "");
    });
  });

  loadTransactions();
}

loadTransactions();
