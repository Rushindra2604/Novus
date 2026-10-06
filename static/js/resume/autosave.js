/* ==========================================
   NOVUS AUTO SAVE ENGINE
========================================== */

let saveTimer = null;


function autoSaveResume() {

    clearTimeout(saveTimer);

    /*
     * Do not attempt to save a completely empty
     * new resume.
     */
    if (
        typeof ResumeAPI.hasMeaningfulContent === "function" &&
        !ResumeAPI.hasMeaningfulContent(
            ResumeEngine.state
        )
    ) {

        updateSaveStatus("Not saved yet");

        return;
    }

    updateSaveStatus("Saving...");

    saveTimer = setTimeout(async () => {

        try {

            const result = await ResumeAPI.save();

            if (result.success) {

                ResumeEngine.isDirty = false;

                ResumeEngine.lastSaved =
                    new Date();

                updateSaveStatus("Saved");

                if (
                    typeof updateLastSaved === "function"
                ) {
                    updateLastSaved(
                        ResumeEngine.lastSaved
                    );
                }

            } else {

                updateSaveStatus("Save Failed");
            }

        } catch (error) {

            console.error(
                "Autosave failed:",
                error
            );

            updateSaveStatus("Save Failed");
        }

    }, 800);
}


function updateSaveStatus(text) {

    const status =
        document.getElementById("saveStatus");

    const container =
        document.getElementById("saveStatusContainer");

    const icon =
        container?.querySelector(".save-status-icon");

    if (!status || !container) {
        return;
    }


    status.textContent = text;


    container.classList.remove(
        "is-saving",
        "is-saved",
        "is-offline",
        "is-error"
    );


    if (text === "Saving...") {

        container.classList.add("is-saving");

        if (icon) {
            icon.setAttribute(
                "data-lucide",
                "loader-circle"
            );
        }

    }

    else if (text === "Saved") {

        container.classList.add("is-saved");

        if (icon) {
            icon.setAttribute(
                "data-lucide",
                "check"
            );
        }

    }

    else if (text === "Offline") {

        container.classList.add("is-offline");

        if (icon) {
            icon.setAttribute(
                "data-lucide",
                "wifi-off"
            );
        }

    }

    else if (text === "Save Failed") {

        container.classList.add("is-error");

        if (icon) {
            icon.setAttribute(
                "data-lucide",
                "triangle-alert"
            );
        }

    }


    if (window.lucide) {
        lucide.createIcons();
    }

}