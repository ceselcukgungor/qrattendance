"use strict";

(function () {
    const panel = document.getElementById("session-panel");
    if (!panel) {
        return;
    }

    const refreshMs = Number(panel.dataset.refreshSeconds) * 1000;
    const qrImage = document.getElementById("qr-image");
    const qrPlaceholder = document.getElementById("qr-placeholder");
    const statusLabel = document.getElementById("session-status");
    const endButton = document.getElementById("end-session");
    const message = document.getElementById("session-message");
    const attendanceList = document.getElementById("attendance-list");
    let timerId = null;

    function showMessage(text, isError) {
        message.textContent = text;
        message.className = isError ? "message error" : "message success";
        message.hidden = false;
    }

    function setText(id, value) {
        document.getElementById(id).textContent = value;
    }

    function updateStats(data) {
        setText("present-count", data.present_count);
        setText("total-enrolled", data.total_enrolled);
        setText("attendance-rate", data.attendance_rate);
        setText("absenteeism-rate", data.absenteeism_rate);
        statusLabel.textContent = data.session_status;
    }

    function formatTime(epochSeconds) {
        return new Date(epochSeconds * 1000).toLocaleTimeString();
    }

    function renderAttendance(students) {
        const rows = students.map(function (student) {
            const row = document.createElement("tr");
            [student.student_id, student.full_name, formatTime(student.checked_in_at)].forEach(function (value) {
                const cell = document.createElement("td");
                cell.textContent = value;
                row.appendChild(cell);
            });
            return row;
        });
        attendanceList.replaceChildren.apply(attendanceList, rows);
    }

    function markClosed() {
        qrImage.hidden = true;
        qrPlaceholder.textContent = "This session is closed.";
        qrPlaceholder.hidden = false;
        endButton.hidden = true;
        if (timerId !== null) {
            clearInterval(timerId);
            timerId = null;
        }
    }

    async function fetchJson(url, options) {
        const response = await fetch(url, options);
        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.message || "Request failed.");
        }
        return data;
    }

    async function refresh() {
        try {
            const qr = await fetchJson(panel.dataset.qrUrl);
            updateStats(qr);
            if (qr.qr_image) {
                qrImage.src = qr.qr_image;
                qrImage.hidden = false;
                qrPlaceholder.hidden = true;
            } else {
                markClosed();
            }
            const attendance = await fetchJson(panel.dataset.attendanceUrl);
            renderAttendance(attendance.students);
        } catch (error) {
            showMessage(error.message, true);
        }
    }

    endButton.addEventListener("click", async function () {
        if (!window.confirm("End this attendance session? Students will no longer be able to check in.")) {
            return;
        }
        endButton.disabled = true;
        try {
            const data = await fetchJson(panel.dataset.endUrl, { method: "POST" });
            updateStats({
                present_count: data.stats.attended,
                total_enrolled: data.stats.enrolled,
                attendance_rate: data.stats.attendance_rate,
                absenteeism_rate: data.stats.absence_rate,
                session_status: data.status,
            });
            markClosed();
            showMessage("Session closed.", false);
        } catch (error) {
            showMessage(error.message, true);
            endButton.disabled = false;
        }
    });

    refresh();
    if (statusLabel.textContent === "active") {
        timerId = setInterval(refresh, refreshMs);
    }
})();
