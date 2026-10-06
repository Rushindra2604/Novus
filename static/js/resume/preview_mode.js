/* ==========================================================
   NOVUS - PHASE 9A
   FULL RESUME PREVIEW
========================================================== */

(function () {

    "use strict";


    function removeDuplicateIds(root) {

        if (!root) return;

        if (root.id) {
            root.removeAttribute("id");
        }

        root.querySelectorAll("[id]").forEach(element => {
            element.removeAttribute("id");
        });

    }


    function createPreviewOverlay() {

        let overlay = document.getElementById("resumePreviewOverlay");

        if (overlay) {
            return overlay;
        }

        overlay = document.createElement("div");

        overlay.id = "resumePreviewOverlay";
        overlay.className = "resume-preview-overlay";
        overlay.setAttribute("aria-hidden", "true");

        overlay.innerHTML = `

            <div
                class="resume-preview-backdrop"
                data-preview-close
            ></div>

            <div
                class="resume-preview-window"
                role="dialog"
                aria-modal="true"
                aria-labelledby="resumePreviewTitle"
            >

                <header class="resume-preview-toolbar">

                    <div class="resume-preview-brand">

                        <span class="resume-preview-brand-icon">
                            <i data-lucide="sparkles"></i>
                        </span>

                        <div>

                            <strong id="resumePreviewTitle">
                                Resume Preview
                            </strong>

                            <span>
                                Live preview of your resume
                            </span>

                        </div>

                    </div>


                    <div class="resume-preview-toolbar-right">

                        <span class="resume-preview-status">

                            <span class="resume-preview-status-dot"></span>

                            Live

                        </span>


                        <button
                            type="button"
                            class="resume-preview-close"
                            data-preview-close
                            title="Back to editor"
                            aria-label="Close preview"
                        >

                            <i data-lucide="x"></i>

                        </button>

                    </div>

                </header>


                <main class="resume-preview-stage">

                    <div
                        class="resume-preview-document"
                        id="resumePreviewDocument"
                    ></div>

                </main>

            </div>
        `;

        document.body.appendChild(overlay);

        if (window.lucide) {
            lucide.createIcons();
        }

        return overlay;
    }


    function openPreview() {

        const source = document.getElementById("resumePreview");

        if (!source) {

            console.warn(
                "Novus Preview: #resumePreview was not found."
            );

            return;
        }


        const overlay = createPreviewOverlay();

        const documentContainer =
            overlay.querySelector("#resumePreviewDocument");


        documentContainer.innerHTML = "";


        /*
         * Clone the CURRENT live preview.
         *
         * This means whatever the user has entered
         * immediately appears in Preview mode.
         */
        const resumeClone = source.cloneNode(true);

        /*
         * Avoid duplicate IDs because the original
         * live preview still exists behind the overlay.
         */
        removeDuplicateIds(resumeClone);

        resumeClone.classList.add(
            "resume-preview-full-document"
        );

        documentContainer.appendChild(resumeClone);


        overlay.classList.add("is-open");

        overlay.setAttribute(
            "aria-hidden",
            "false"
        );

        document.body.classList.add(
            "preview-modal-open"
        );


        const stage =
            overlay.querySelector(".resume-preview-stage");

        if (stage) {
            stage.scrollTop = 0;
        }


        if (window.lucide) {
            lucide.createIcons();
        }

    }


    function closePreview() {

        const overlay =
            document.getElementById(
                "resumePreviewOverlay"
            );

        if (!overlay) return;


        overlay.classList.remove("is-open");

        overlay.setAttribute(
            "aria-hidden",
            "true"
        );

        document.body.classList.remove(
            "preview-modal-open"
        );


        setTimeout(() => {

            if (!overlay.classList.contains("is-open")) {

                const container =
                    overlay.querySelector(
                        "#resumePreviewDocument"
                    );

                if (container) {
                    container.innerHTML = "";
                }

            }

        }, 220);

    }


    function initializePreviewButton() {

        const button =
            document.getElementById(
                "previewResumeBtn"
            );

        if (!button) return;

        if (
            button.dataset.previewBound === "true"
        ) {
            return;
        }

        button.dataset.previewBound = "true";


        button.addEventListener(
            "click",
            function (event) {

                event.preventDefault();

                openPreview();

            }
        );


        document.addEventListener(
            "click",
            function (event) {

                const closeButton =
                    event.target.closest(
                        "[data-preview-close]"
                    );

                if (closeButton) {
                    closePreview();
                }

            }
        );


        document.addEventListener(
            "keydown",
            function (event) {

                if (event.key !== "Escape") {
                    return;
                }

                const overlay =
                    document.getElementById(
                        "resumePreviewOverlay"
                    );

                if (
                    overlay &&
                    overlay.classList.contains("is-open")
                ) {
                    closePreview();
                }

            }
        );

    }


    document.addEventListener(
        "DOMContentLoaded",
        initializePreviewButton
    );

})();