// Wait for the window to load
window.onload = function() {
    // Set timeout to simulate loading time
    setTimeout(function() {
        // Redirect to the index page
        window.location.href = "{% url 'index' %}";
    }, 3000); // 3000 milliseconds = 3 seconds
};
