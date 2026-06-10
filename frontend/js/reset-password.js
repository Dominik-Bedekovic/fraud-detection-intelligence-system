const token = new URLSearchParams(window.location.search).get("token");

document.getElementById("resetForm").addEventListener("submit", async (e) => {
  e.preventDefault();

  const password = document.getElementById("password").value;
  const confirmPassword = document.getElementById("confirmPassword").value;

  if (password !== confirmPassword) {
    alert("Passwords do not match");
    return;
  }

  const res = await fetch("/auth/reset-password", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      token,
      new_password: password,
    }),
  });

  const data = await res.json();

  if (!res.ok) {
    alert(data.detail || "Reset failed");
    return;
  }

  alert("Password updated successfully");
  window.location.href = "/static/login.html";
});
