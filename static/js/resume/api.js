/* ==========================================
   NOVUS API
========================================== */

const ResumeAPI = {

    /* ==========================================
       GET RESUME ID
    ========================================== */

    getResumeId() {

        const container =
            document.querySelector(".resume-studio");

        if (!container) {
            throw new Error(
                "Resume Studio container not found."
            );
        }

        const resumeId =
            container.dataset.resumeId;

        /*
         * A new Resume Studio session does not have
         * a database ID yet.
         *
         * Return null instead of throwing.
         * ResumeAPI.save() will then create the
         * database resume when meaningful content exists.
         */
        return resumeId || null;
    },

    hasMeaningfulContent(state) {

        if (!state || typeof state !== "object") {
            return false;
        }

        const check = (value, key = "") => {

            if (typeof value === "string") {

                const text = value.trim();

                if (!text) {
                    return false;
                }

                if (
                    key === "title" &&
                    text === "Untitled Resume"
                ) {
                    return false;
                }

                return true;
            }

            if (Array.isArray(value)) {

                return value.some(item =>
                    check(item)
                );
            }

            if (value && typeof value === "object") {

                return Object.entries(value).some(
                    ([childKey, childValue]) => {

                        if (
                            childKey === "id" ||
                            childKey === "type" ||
                            childKey === "visible" ||
                            childKey === "expanded"
                        ) {
                            return false;
                        }

                        return check(
                            childValue,
                            childKey
                        );
                    }
                );
            }

            return false;
        };

        return check(state);
    },


    /* ==========================================
       LOAD RESUME
    ========================================== */
    async load() {

        const resumeId = this.getResumeId();

        /*
         * /resume/new has no database ID yet.
         * This is a valid new-resume state,
         * not an error.
         */
        if (!resumeId) {

            return {
                success: true,
                resume: null,
                isNew: true
            };
        }

        const response = await fetch(
            `/api/resume/load/${resumeId}`
        );

        if (!response.ok) {
            throw new Error(
                `Load failed (${response.status})`
            );
        }

        return await response.json();
    },


    /* ==========================================
       SAVE RESUME
    ========================================== */

    async save() {

        const resumeId = this.getResumeId();

        /*
         * NEW RESUME
         *
         * There is no database ID yet.
         * Create the database resume only after
         * the user has entered meaningful content.
         */
        if (!resumeId) {

            const state = ResumeEngine.state;

            const hasContent = this.hasMeaningfulContent(state);

            if (!hasContent) {

                return {
                    success: true,
                    skipped: true,
                    message: "Nothing to save yet."
                };
            }

            const response = await fetch(
                "/api/resume/create",
                {
                    method: "POST",

                    headers: {
                        "Content-Type": "application/json"
                    },

                    body: JSON.stringify({
                        resume: state
                    })
                }
            );

            if (!response.ok) {
                throw new Error(
                    `Resume creation failed (${response.status})`
                );
            }

            const result = await response.json();

            if (!result.success || !result.resume_id) {
                throw new Error(
                    result.message ||
                    "Resume creation failed."
                );
            }

            /*
             * IMPORTANT:
             * Store the newly created database ID
             * in the current Resume Studio.
             */
            const studio =
                document.querySelector(".resume-studio");

            if (studio) {

                studio.dataset.resumeId =
                    String(result.resume_id);
            }

            /*
             * Now change:
             *
             * /resume/new
             *
             * to:
             *
             * /resume/23
             *
             * without reloading the page.
             */
            window.history.replaceState(
                {},
                "",
                `/resume/${result.resume_id}`
            );

            return result;
        }

        /*
         * EXISTING RESUME
         *
         * Keep the current autosave behavior.
         */
        const response = await fetch(
            `/api/resume/save/${resumeId}`,
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
            throw new Error(
                `Save failed (${response.status})`
            );
        }

        return await response.json();
    },
}