document.addEventListener('DOMContentLoaded', (_) => {
    const generateCertModal = document.getElementById("generateCertModal");
    const generateCertBtn = document.getElementById("generateCertBtn");
    const modalClose = document.getElementsByClassName("modal-close")[0];
    const generateCertForm = document.getElementById("generateCertForm");
    const reloadPreviewBtn = document.getElementById("reloadPreview");
    const commandPreview = document.getElementById("commandPreview");
    const logContent = document.getElementById("logContent");

    generateCertBtn.onclick = function() {
        generateCertModal.style.display = "block";
    }

    modalClose.onclick = function() {
        generateCertModal.style.display = "none";
    }

    window.onclick = function(event) {
        if (event.target === generateCertModal) {
            generateCertModal.style.display = "none";
        }
    }

    function updateCommandPreview() {
        const keyName = document.getElementById("keyName").value;
        const keyType = document.getElementById("keyType").value;
        const duration = document.getElementById("duration").value;
        const durationUnit = document.getElementById("durationUnit").value;

        commandPreview.textContent = `step-ca command --key-name "${keyName}" --key-type ${keyType} --duration ${duration}${durationUnit}`;
    }

    reloadPreviewBtn.onclick = updateCommandPreview;

    generateCertForm.onsubmit = function(e) {
        e.preventDefault();
        updateCommandPreview();
        
        logContent.innerHTML = "Executing command...";
        setTimeout(() => {
            logContent.innerHTML += "<br>Certificate generated successfully!";
        }, 2000);
    }
});