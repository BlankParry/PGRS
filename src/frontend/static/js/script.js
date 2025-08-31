// Simple form validation for registration
document.getElementById("registerForm").onsubmit = function (event) {
    let name = document.getElementById("name").value;
    let contactNumber = document.getElementById("contact_number").value;
    let email = document.getElementById("email").value;
    let address = document.getElementById("address").value;

    // Basic validation checks
    if (!name || !contactNumber || !email || !address) {
        alert("Please fill in all required fields.");
        event.preventDefault(); // Prevent form submission
    }
};
