const token = new URLSearchParams(window.location.search).get("token");

async function resetPassword() {
  const password = document.getElementById("password").value;

  await fetch("/auth/reset-password", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      token,
      new_password: password,
    }),
  });

  window.location.href = "/static/login.html";
}
