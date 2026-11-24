"use strict";

(function () {
    const message = document.getElementById("dashboard-message");

    function showError(text) {
        message.textContent = text;
        message.className = "message error";
        message.hidden = false;
    }

    document.querySelectorAll(".start-session").forEach(function (button) {
        button.addEventListener("click", async function () {
            button.disabled = true;
            try {
                const response = await fetch("/api/sessions/start", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ course_id: Number(button.dataset.courseId) }),
                });
                const data = await response.json();
                if (!response.ok) {
                    throw new Error(data.message || "Could not start the session.");
                }
                window.location.href = "/instructor/sessions/" + data.session_id;
            } catch (error) {
                showError(error.message);
                button.disabled = false;
            }
        });
    });
})();
