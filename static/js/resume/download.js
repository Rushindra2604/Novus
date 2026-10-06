/* ==========================================================
   NOVUS RESUME STUDIO
   PDF DOWNLOAD
   Backend / WeasyPrint
========================================================== */

document.addEventListener("DOMContentLoaded", () => {

    const downloadButton =
        document.getElementById("downloadResumeBtn");

    if (!downloadButton) {
        return;
    }

    downloadButton.addEventListener(
        "click",
        downloadResumePDF
    );

});


async function downloadResumePDF() {

    const button =
        document.getElementById("downloadResumeBtn");

    const studio =
        document.querySelector(".resume-studio");


    if (!button || !studio) {
        console.error(
            "Resume Studio or download button not found."
        );
        return;
    }


    const resumeId =
        studio.dataset.resumeId;


    if (!resumeId) {
        console.error(
            "Resume ID not found."
        );
        return;
    }


    const originalHTML =
        button.innerHTML;


    try {

        /* ==================================================
           DISABLE BUTTON
        ================================================== */

        button.disabled = true;

        button.innerHTML = `
            <i data-lucide="loader-circle"></i>
            PDF
        `;


        if (window.lucide) {
            lucide.createIcons();
        }


        /* ==================================================
           MAKE SURE LATEST STATE IS SAVED
        ================================================== */

        if (
            typeof saveTimer !== "undefined"
        ) {

            clearTimeout(saveTimer);

        }


        if (
            typeof ResumeEngine !== "undefined" &&
            typeof ResumeAPI !== "undefined"
        ) {

            try {

                ResumeEngine.storage.saveDraft();

                await ResumeAPI.save();

            }

            catch (error) {

                console.warn(
                    "Could not perform final save before PDF:",
                    error
                );

            }

        }


        /* ==================================================
           REQUEST PDF FROM FLASK
        ================================================== */

        const response = await fetch(
            `/api/resume/${resumeId}/pdf`,
            {
                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify({
                    resume: ResumeEngine.state
                })
            }
        );


        if (!response.ok) {

            let message =
                `PDF generation failed (${response.status})`;

            try {

                const errorData =
                    await response.json();

                if (errorData.message) {
                    message = errorData.message;
                }

            }

            catch {
                // Response wasn't JSON.
            }

            throw new Error(message);
        }


        /* ==================================================
           CONVERT RESPONSE TO FILE
        ================================================== */

        const blob =
            await response.blob();


        if (!blob || blob.size === 0) {

            throw new Error(
                "The generated PDF is empty."
            );

        }


        /* ==================================================
           GET FILENAME
        ================================================== */

        let title =
            ResumeEngine?.state?.title ||
            "Novus Resume";


        title = title
            .trim()
            .replace(/[<>:"/\\|?*]+/g, "")
            .replace(/\s+/g, " ");


        if (!title) {
            title = "Novus Resume";
        }


        const filename =
            `${title}.pdf`;


        /* ==================================================
           DOWNLOAD
        ================================================== */

        const url =
            window.URL.createObjectURL(blob);


        const link =
            document.createElement("a");


        link.href = url;
        link.download = filename;

        document.body.appendChild(link);

        link.click();

        link.remove();


        window.URL.revokeObjectURL(url);


    }

    catch (error) {

        console.error(
            "PDF download failed:",
            error
        );


        alert(
            "Unable to generate the PDF. Please try again."
        );

    }

    finally {

        /* ==================================================
           RESTORE BUTTON
        ================================================== */

        button.disabled = false;

        button.innerHTML =
            originalHTML;


        if (window.lucide) {
            lucide.createIcons();
        }

    }

}