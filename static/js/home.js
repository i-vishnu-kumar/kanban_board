document.addEventListener("DOMContentLoaded", function () {
  var now = new Date();
  var datetime = now.toLocaleString();

  document.getElementById("datetime").innerHTML = datetime;

  setInterval(function () {
    let now = new Date();
    let datetime = now.toLocaleString();
    document.getElementById("datetime").innerHTML = datetime;
  }, 1000);

  rem_btn = document.getElementById("removebtn");

  rem_btn.addEventListener("click", () => {
    console.log("Clicked!!");

    // Get the current URL parameters
    const pathParts = window.location.pathname.split("/");
    const dev_name = pathParts[2]; // /home/<dev_name>/<temp_name>
    const temp_name = pathParts[3];

    // Make AJAX request to remove last sprint
    fetch(`/remove_sprint/${dev_name}/${temp_name}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
    })
      .then((response) => {
        if (response.ok) {
          // Reload the page to show updated data
          window.location.reload();
        } else {
          console.error("Failed to remove sprint");
          alert("Failed to remove sprint: " + error);
        }
      })
      .catch((error) => {
        console.error("Error:", error);
        alert("Error removing sprint");
      });
  });

  add_btn = document.getElementById("addbtn");
  add_btn.addEventListener("click", () => {
    console.log("Add Clicked!!");

    // Get the current URL parameters
    const pathParts = window.location.pathname.split("/");
    const dev_name = pathParts[2]; // /home/<dev_name>/<temp_name>
    const temp_name = pathParts[3];

    // Make AJAX request to add new sprint
    fetch(`/add_sprint/${dev_name}/${temp_name}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
    })
      .then((response) => {
        if (response.ok) {
          // Reload the page to show updated data
          window.location.reload();
        } else {
          console.error("Failed to add sprint");
          alert("Failed to add sprint: " + error);
        }
      })
      .catch((error) => {
        console.error("Error:", error);
        alert("Error adding sprint");
      });
  });
});
