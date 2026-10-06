/* ==========================================
   NOVUS CERTIFICATION MODULE
========================================== */

const CertificationModule = {

    container: null,

    months: [

        "Jan",
        "Feb",
        "Mar",
        "Apr",
        "May",
        "Jun",
        "Jul",
        "Aug",
        "Sep",
        "Oct",
        "Nov",
        "Dec"

    ],

    init() {

        this.container = document.getElementById("certificationContainer");

        if (!this.container) return;

        if (!Array.isArray(ResumeEngine.state.certifications)) {

            ResumeEngine.state.certifications = [];

        }

        if (ResumeEngine.state.certifications.length === 0) {

            this.addCertification(false);

        }

        else {

            this.render();

        }

        document
            .getElementById("addCertificationBtn")
            ?.addEventListener("click", () => {

                this.addCertification();

            });

        this.bindEvents();

    },

    /* ==========================================
       DEFAULT CERTIFICATION
    ========================================== */

    createCertification() {

        return {

            name: "",

            organization: "",

            credentialUrl: "",

            expanded: true

        };

    },

    /* ==========================================
       ADD CERTIFICATION
    ========================================== */

    addCertification(save = true) {

        ResumeEngine.state.certifications.push(

            this.createCertification()

        );

        ResumeEngine.state.certifications.forEach(certification => {

            certification.expanded = false;

        });

        ResumeEngine.state.certifications[

            ResumeEngine.state.certifications.length - 1

        ].expanded = true;

        this.render();

        if (save) {

            ResumeEngine.storage.saveDraft();

            autoSaveResume();

        }

        if (typeof updatePreview === "function") {

            updatePreview(ResumeEngine.state);

        }

        if (typeof updateCompletion === "function") {

            updateCompletion(ResumeEngine.state);

        }

    },

    /* ==========================================
       RENDER
    ========================================== */

    render() {

        this.container.innerHTML = "";

        ResumeEngine.state.certifications.forEach(

            (certification, index) => {

                this.container.insertAdjacentHTML(

                    "beforeend",

                    this.template(certification, index)

                );

            }

        );

        if (window.lucide) {

            lucide.createIcons();

        }

    },

    /* ==========================================
       EVENTS
    ========================================== */

    bindEvents() {

        /* ==========================
           INPUT EVENTS
        ========================== */

        this.container.addEventListener("input", (event) => {

            const input = event.target;

            const item = input.closest(".certification-item");

            if (!item) return;

            const index = Number(item.dataset.index);

            const certification =

                ResumeEngine.state.certifications[index];

            if (!certification) return;

            if (input.classList.contains("certification-input")) {

                const field = input.dataset.field;

                certification[field] = input.value.trim();

            }

            ResumeEngine.storage.saveDraft();

            autoSaveResume();

            if (typeof updatePreview === "function") {

                updatePreview(ResumeEngine.state);

            }

            if (typeof updateCompletion === "function") {

                updateCompletion(ResumeEngine.state);

            }

        });

        /* ==========================
           CLICK EVENTS
        ========================== */

        this.container.addEventListener("click", (event) => {

            /* --------------------------
               TOGGLE
            -------------------------- */

            const toggleBtn = event.target.closest(

                ".toggle-certification-btn"

            );

            if (toggleBtn) {

                const index = Number(

                    toggleBtn
                        .closest(".certification-item")
                        .dataset.index

                );

                this.toggleCertification(index);

                return;

            }

            /* --------------------------
               REMOVE
            -------------------------- */

            const removeBtn = event.target.closest(

                ".remove-certification-btn"

            );

            if (removeBtn) {

                const index = Number(

                    removeBtn
                        .closest(".certification-item")
                        .dataset.index

                );

                this.removeCertification(index);

                return;

            }

        });

    },

    /* ==========================================
       TOGGLE CERTIFICATION
    ========================================== */

    toggleCertification(index) {

        ResumeEngine.state.certifications.forEach((certification, i) => {

            certification.expanded =

                i === index

                    ? !certification.expanded

                    : false;

        });

        this.render();

    },

    /* ==========================================
       REMOVE CERTIFICATION
    ========================================== */

    removeCertification(index) {

        const certification =

            ResumeEngine.state.certifications[index];

        const title =

            certification.name ||

            `Certification ${index + 1}`;

        const confirmed = confirm(

            `Delete "${title}" ?`

        );

        if (!confirmed) return;

        ResumeEngine.state.certifications.splice(index, 1);

        if (ResumeEngine.state.certifications.length === 0) {

            this.addCertification(false);

            return;

        }

        ResumeEngine.state.certifications[0].expanded = true;

        this.render();

        ResumeEngine.storage.saveDraft();

        autoSaveResume();

        if (typeof updatePreview === "function") {

            updatePreview(ResumeEngine.state);

        }

        if (typeof updateCompletion === "function") {

            updateCompletion(ResumeEngine.state);

        }

    },

    /* ==========================================
       TEMPLATE
    ========================================== */

    template(certification, index) {

        return `

<div class="certification-item" data-index="${index}">

    <div class="certification-header">

        <button
            type="button"
            class="toggle-certification-btn">

            <i data-lucide="${certification.expanded ? "chevron-down" : "chevron-right"}"></i>

        </button>

        <h3>

            ${certification.name || `Certification ${index + 1}`}

        </h3>

        <button
            type="button"
            class="remove-certification-btn">

            <i data-lucide="trash-2"></i>

        </button>

    </div>

    ${certification.expanded
                ? this.certificationContent(certification, index)
                : ""}

</div>

`;

    },

    /* ==========================================
       CERTIFICATION CONTENT
    ========================================== */

    certificationContent(certification, index) {

        return `

<div class="certification-body">

    <!-- ===============================
         CERTIFICATION NAME
    ================================ -->

    <div class="form-group">

        <label>

            Certification Name

        </label>

        <input
            type="text"
            class="certification-input"
            data-field="name"
            value="${certification.name || ""}"
            placeholder="AWS Certified Cloud Practitioner">

    </div>

    <!-- ===============================
         ORGANIZATION
    ================================ -->

    <div class="form-group">

        <label>

            Issuing Organization

        </label>

        <input
            type="text"
            class="certification-input"
            data-field="organization"
            value="${certification.organization || ""}"
            placeholder="Amazon Web Services">

    </div>

    <!-- ===============================
         CREDENTIAL URL
    ================================ -->

    <div class="form-group">

        <label>

            Credential URL (Optional)

        </label>

        <input
            type="url"
            class="certification-input"
            data-field="credentialUrl"
            value="${certification.credentialUrl || ""}"
            placeholder="https://www.credly.com/...">

    </div>

    <hr>

</div>

`;

    }

};