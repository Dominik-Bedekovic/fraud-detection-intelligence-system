document.getElementById("loginForm").onsubmit = async (e) => {
  e.preventDefault();

  const payload = {
    email: document.getElementById("email").value,
    password: document.getElementById("password").value,
  };

  const res = await fetch("/auth/token", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  const data = await res.json();

  if (!res.ok) {
    alert(data.detail || "Login failed");
    return;
  }

  if (!data.access_token) {
    alert("No token received");
    return;
  }

  localStorage.setItem("token", data.access_token);

  window.location.href = "/";
};
