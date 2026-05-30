document.getElementById("registerForm").onsubmit = async (e) => {
  e.preventDefault();

  const payload = {
    full_name: document.getElementById("full_name").value,
    email: document.getElementById("email").value,
    password: document.getElementById("password").value,
  };

  const res = await fetch("/auth/", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  const data = await res.json();

  console.log(data);

  if (res.ok) {
    window.location.href = "/static/login.html";
  } else {
    console.error("Error creating user", data);
  }
};
