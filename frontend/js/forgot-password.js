document.addEventListener("DOMContentLoaded", () => {
  const btn = document.getElementById("forgotPassword");

  if (!btn) return;

  btn.addEventListener("click", async (e) => {
    e.preventDefault();

    const email = prompt("Enter your email:");

    if (!email) return;

    const res = await fetch("/auth/forgot-password", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ email }),
    });

    const data = await res.json();

    if (!res.ok) {
      alert(data.detail || "Error");
      return;
    }

    window.location.href = `/static/reset-password.html?email=${encodeURIComponent(email)}`;
  });
});
