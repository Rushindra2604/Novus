/* ==========================================
   NOVUS STORAGE ENGINE
========================================== */

ResumeEngine.storage = {

    getResumeId() {
        const container = document.querySelector(".resume-studio");
        return container?.dataset.resumeId || "unknown";
    },

    getDraftKey() {
        return `novus_resume_${this.getResumeId()}`;
    },

    saveDraft() {
        try {
            const draftData = {
                state: ResumeEngine.state,
                sections: {
                    metadata: typeof SectionManager !== "undefined" ? SectionManager.sections : {},
                    order: typeof SectionManager !== "undefined" ? SectionManager.sectionOrder : []
                }
            };

            localStorage.setItem(this.getDraftKey(), JSON.stringify(draftData));
        } catch (error) {
            console.error("Draft save failed:", error);
        }
    },

    loadDraft() {
        try {
            const draft = localStorage.getItem(this.getDraftKey());
            if (!draft) return false;

            const data = JSON.parse(draft);

            if (data.state) {
                Object.assign(ResumeEngine.state, data.state);
            } else {
                Object.assign(ResumeEngine.state, data);
            }

            ResumeEngine._storedSectionData = data.sections || null;
            return true;
        } catch (error) {
            console.error("Draft restore failed:", error);
            return false;
        }
    },

    clearDraft() {
        localStorage.removeItem(this.getDraftKey());
    }
};
