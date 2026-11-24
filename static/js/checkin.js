"use strict";

(function () {
    const form = document.getElementById("checkin-form");
    if (!form) {
        return;
    }

    const message = document.getElementById("checkin-message");
    const button = form.querySelector("button[type=submit]");

    function showMessage(text, isError) {
        message.textContent = text;
        message.className = isError ? "message error" : "message success";
        message.hidden = false;
    }

    form.addEventListener("submit", async function (event) {
        event.preventDefault();
        button.disabled = true;
        try {
            const response = await fetch(form.dataset.checkinUrl, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    token: document.getElementById("token").value,
                    student_id: document.getElementById("student_id").value.trim(),
                }),
            });
            const data = await response.json();
            showMessage(data.message, !response.ok);
            if (response.ok) {
                form.hidden = true;
                return;
            }
        } catch (error) {
            showMessage("Network error. Please try again.", true);
        }
        button.disabled = false;
    });
})();
