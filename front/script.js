// script.js
document.addEventListener('DOMContentLoaded', (event) => {
    const modal = document.getElementById("generateCertModal");
    const btn = document.getElementById("generateCertBtn");
    const span = document.getElementsByClassName("close")[0];
    const form = document.getElementById("generateCertForm");
    const reloadPreviewBtn = document.getElementById("reloadPreview");
    const commandPreview = document.getElementById("commandPreview");
    const logContent = document.getElementById("logContent");

    btn.onclick = function() {
        modal.style.display = "block";
    }

    span.onclick = function() {
        modal.style.display = "none";
    }

    window.onclick = function(event) {
        if (event.target == modal) {
            modal.style.display = "none";
        }
    }

    function updateCommandPreview() {
        const keyName = document.getElementById("keyName").value;
        const keyType = document.getElementById("keyType").value;
        const duration = document.getElementById("duration").value;
        const durationUnit = document.getElementById("durationUnit").value;

        const command = `step-ca command --key-name "${keyName}" --key-type ${keyType} --duration ${duration}${durationUnit}`;
        commandPreview.textContent = command;
    }

    reloadPreviewBtn.onclick = updateCommandPreview;

    form.onsubmit = function(e) {
        e.preventDefault();
        updateCommandPreview();
        
        // Here you would typically send an AJAX request to your Flask backend
        // For now, we'll just simulate it with a timeout
        logContent.innerHTML = "Executing command...";
        setTimeout(() => {
            logContent.innerHTML += "<br>Certificate generated successfully!";
        }, 2000);
    }
});