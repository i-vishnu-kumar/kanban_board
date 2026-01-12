document.addEventListener("DOMContentLoaded", function () {
  const createButton = document.getElementById("createButton");

  if (createButton) {
    createButton.addEventListener("click", function () {
      const sprintValue = document.getElementById("sprint_num").value;
      sessionStorage.setItem("selectedSprint", sprintValue);
      window.location.href = "home";
    });
  } else {
    console.error("Button not found!");
  }
});
