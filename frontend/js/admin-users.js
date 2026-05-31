async function loadUsers() {
  const token = localStorage.getItem("token");

  const res = await fetch("/admin/users", {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!res.ok) {
    alert("Admin access required");
    return;
  }

  const users = await res.json();

  const tbody = document.querySelector("#usersTable tbody");

  users.forEach((user) => {
    tbody.innerHTML += `
      <tr>
        <td>${user.id}</td>
        <td>${user.email}</td>
        <td>${user.full_name}</td>
        <td>${user.role_id}</td>
        <td>${user.is_active}</td>
        <td>
            <button class="btn view-btn" onclick="viewUser(${user.id})">
            View
            </button>
        </td>
      </tr>
    `;
  });
}

function viewUser(userId) {
  window.location.href = `/static/transactions.html?user_id=${userId}`;
}

loadUsers();
