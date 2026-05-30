document.getElementById("forgotPassword").addEventListener("click", (e) => {
  e.preventDefault();

  alert("You thought I was gonna help you?! 😈");

  const audio = new Audio("/static/sounds/krusty-krabs.m4a");
  audio.play();

  document.body.style.transform = "scale(1.01)";
  document.body.style.filter = "hue-rotate(180deg)";

  setTimeout(() => {
    document.body.style.transform = "none";
    document.body.style.filter = "none";
  }, 1500);
});
