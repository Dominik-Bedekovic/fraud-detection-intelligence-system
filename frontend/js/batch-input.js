document.getElementById("batchForm").onsubmit = async (e) => {
  e.preventDefault();

  const fileInput = document.getElementById("csvFile");
  const token = localStorage.getItem("token");

  if (!fileInput.files.length) {
    alert("Please select a CSV file");
    return;
  }

  const formData = new FormData();
  formData.append("file", fileInput.files[0]);

  document.getElementById("batchRes").innerText = "Processing...";

  try {
    const res = await fetch("/predict/batch", {
      method: "POST",
      headers: {"Authorization": `Bearer ${token}`},
      body: formData,
    });

    const data = await res.json();

    const box = document.getElementById("batchRes");

    box.classList.add("show");

    box.innerHTML = `
              <h3>Batch Results:</h3>
              ${data.results
                .map(
                  (r, i) => `
                <div style="padding:8px; border-bottom:1px solid #eee;">
                <h3>Result #${i + 1}</h3>
                <p><strong>Label:</strong> ${r.label}</p>
                <p><strong>Fraud probability:</strong> ${r.probability}%</p>
                </div>
  `,
                )
                .join("")}
`;
  } catch (err) {
    document.getElementById("batchRes").innerText = "Error: " + err.message;
  }
};
