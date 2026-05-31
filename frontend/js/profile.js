async function loadProfile() {
  const token = localStorage.getItem("token");

  const res = await fetch("/auth/me", {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!res.ok) {
    window.location.href = "/static/login.html";
    return;
  }

  const user = await res.json();

  document.getElementById("profile").innerHTML = `
    <div class="card">
      <p><b>Name:</b> ${user.full_name}</p>
    </div>

    <div class="card">
      <p><b>Email:</b> ${user.email}</p>
    </div>

    <div class="card">
      <p><b>Role:</b> ${user.role_name}</p>
    </div>
  `;
}

loadProfile();
