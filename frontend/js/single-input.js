document.getElementById("singleForm").onsubmit = async (e) => {
  e.preventDefault();

  const payload = {
    type: document.getElementById("type").value,
    amount: Number(document.getElementById("amount").value),
    oldbalanceOrg: Number(document.getElementById("oldbalanceOrg").value),
    newbalanceOrig: Number(document.getElementById("newbalanceOrig").value),
    oldbalanceDest: Number(document.getElementById("oldbalanceDest").value),
    newbalanceDest: Number(document.getElementById("newbalanceDest").value),
  };

  const res = await fetch("/predict", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  const data = await res.json();

  const box = document.getElementById("singleRes");

  box.classList.add("show");

  box.innerHTML = `
            <div>
              <h3>Result</h3>
              <p><strong>Label:</strong> ${data.label}</p>
              <p><strong>Fraud probability:</strong> ${data.probability}%</p>
            </div>
          `;
};
