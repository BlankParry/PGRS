// Handling the dynamic behavior on citizen login page
document.getElementById("loginForm").onsubmit = function (event) {
    let email = document.getElementById("email").value;

    // Basic validation for email
    if (!email) {
        alert("Please enter your email.");
        event.preventDefault(); // Prevent form submission
    }
};

// If you need to display citizen details dynamically on the dashboard
document.addEventListener("DOMContentLoaded", function () {
    const citizenId = document.getElementById("citizenId");
    // Dynamically display citizen ID or other details
    if (citizenId) {
        citizenId.textContent = `Your Citizen ID: ${citizenId.getAttribute("data-citizen-id")}`;
    }
});
