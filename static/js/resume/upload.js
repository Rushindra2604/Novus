document.addEventListener("DOMContentLoaded", () => {

    const uploadTrigger = document.getElementById("dashboardUploadTrigger");
    const fileInput = document.getElementById("dashboardResumeFile");
    const uploadForm = document.getElementById("dashboardResumeUploadForm");

    if (!uploadTrigger || !fileInput || !uploadForm) {
        return;
    }

    // Open file picker
    uploadTrigger.addEventListener("click", (event) => {

        event.preventDefault();

        fileInput.click();

    });

    // Submit selected file
    fileInput.addEventListener("change", () => {

        const file = fileInput.files[0];

        if (!file) {
            return;
        }

        const allowedExtensions = [".pdf", ".docx"];
        const filename = file.name.toLowerCase();

        const isAllowed = allowedExtensions.some(
            extension => filename.endsWith(extension)
        );

        if (!isAllowed) {

            alert("Please upload a PDF or DOCX resume.");

            fileInput.value = "";

            return;
        }

        // 10 MB maximum
        const maxSize = 10 * 1024 * 1024;

        if (file.size > maxSize) {

            alert("Resume file must be smaller than 10 MB.");

            fileInput.value = "";

            return;
        }

        // Submit to Flask
        uploadForm.submit();

    });

});