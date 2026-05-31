async function loadNavbar(mode = "full") {
  const container = document.getElementById("navbar");
  if (!container) return;

  const res = await fetch("/static/components/navbar.html");
  const html = await res.text();
  container.innerHTML = html;

  const navLinks = container.querySelector("#navLinks");

  if (mode === "auth") {
    if (navLinks) navLinks.style.display = "none";
    return;
  }

  const token = localStorage.getItem("token");
  if (!token) return;

  const meRes = await fetch("/auth/me", {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!meRes.ok) return;

  const user = await meRes.json();

  const userNav = container.querySelector("#userNav");
  if (!userNav) return;

  let adminLink = "";

  if (user.role_id === 2) {
    adminLink = `<a href="/static/admin-users.html" id="adminBtn">Users</a>`;
  }

  const showNavLinks = mode !== "admin";

  if (navLinks) {
    navLinks.style.display = showNavLinks ? "flex" : "none";
  }

  userNav.innerHTML = `
    <div class="user-menu">
      <button id="userBtn">${user.full_name}</button>
      <div id="dropdownMenu" class="dropdown-menu">
        ${adminLink}
        <a href="#" id="logoutBtn">Logout</a>
      </div>
    </div>
  `;

  const userBtn = userNav.querySelector("#userBtn");
  const dropdown = userNav.querySelector("#dropdownMenu");
  const logoutBtn = userNav.querySelector("#logoutBtn");
  const adminBtn = userNav.querySelector("#adminBtn");

  userBtn?.addEventListener("click", (e) => {
    e.stopPropagation();
    dropdown.classList.toggle("show");
  });

  logoutBtn?.addEventListener("click", (e) => {
    e.preventDefault();
    localStorage.removeItem("token");
    window.location.href = "/static/login.html";
  });

  adminBtn?.addEventListener("click", (e) => {
    e.preventDefault();
    window.location.href = "/static/admin-users.html";
  });

  document.addEventListener("click", () => {
    dropdown?.classList.remove("show");
  });
}
