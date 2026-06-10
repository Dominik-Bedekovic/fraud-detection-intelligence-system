document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("forgotForm");

  form.addEventListener("submit", async (e) => {
    e.preventDefault();

    const email = document.getElementById("email").value;

    const res = await fetch("/auth/forgot-password", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ email }),
    });

    const data = await res.json();

    console.log(data);

    if (!res.ok) {
      alert(data.detail || "Error");
      return;
    }

    alert("Password reset request submitted.");

    if (data.reset_link) {
      window.location.href = data.reset_link;
    }
  });
});
