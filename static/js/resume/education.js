/* ==========================================
   NOVUS EDUCATION MODULE
========================================== */

const EducationModule = {

    container: null,

    init() {

        this.container = document.getElementById("educationContainer");

        if (!this.container) return;

        if (!Array.isArray(ResumeEngine.state.education)) {

            ResumeEngine.state.education = [];

        }

        if (ResumeEngine.state.education.length === 0) {

            this.addEducation(false);

        }

        else {

            this.render();

        }

        document
            .getElementById("addEducationBtn")
            ?.addEventListener("click", () => {

                this.addEducation();

            });

        /* ===============================
           INPUT EVENTS
        =============================== */

        this.container.addEventListener("input", (event) => {

            const input = event.target.closest(".education-input");

            if (!input) return;

            const item = input.closest(".education-item");

            const index = Number(item.dataset.index);

            const field = input.dataset.field;

            ResumeEngine.state.education[index][field] =
                input.value.trim();

            ResumeEngine.storage.saveDraft();

            autoSaveResume();

            if (typeof updatePreview === "function") {

                updatePreview(ResumeEngine.state);

            }

            if (typeof updateCompletion === "function") {

                updateCompletion(ResumeEngine.state);

            }

        });

        /* ===============================
           REMOVE EDUCATION
        =============================== */

        this.container.addEventListener("click", (event) => {

            const btn = event.target.closest(".remove-education-btn");

            if (!btn) return;

            const index = Number(

                btn.closest(".education-item").dataset.index

            );

            ResumeEngine.state.education.splice(index, 1);

            if (ResumeEngine.state.education.length === 0) {

                this.addEducation(false);

                return;

            }

            this.render();

            ResumeEngine.storage.saveDraft();

            autoSaveResume();

            if (typeof updatePreview === "function") {

                updatePreview(ResumeEngine.state);

            }

            if (typeof updateCompletion === "function") {

                updateCompletion(ResumeEngine.state);

            }

        });

    },

    /* ==========================================
       ADD EDUCATION
    ========================================== */

    addEducation(save = true) {

        ResumeEngine.state.education.push({

            degree: "",

            institution: "",

            startYear: "",

            endYear: "",

            score: ""

        });

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

        ResumeEngine.state.education.forEach((education, index) => {

            this.container.insertAdjacentHTML(

                "beforeend",

                this.template(education, index)

            );

        });

        if (window.lucide) {

            lucide.createIcons();

        }

    },

    /* ==========================================
       TEMPLATE
    ========================================== */

    template(education, index) {

        return `

<div class="education-item" data-index="${index}">

    <div class="education-header">

        <h3>

            Education ${index + 1}

        </h3>

        <button
            type="button"
            class="remove-education-btn">

            <i data-lucide="trash-2"></i>

        </button>

    </div>

    <div class="form-group">

        <label>

            Degree

        </label>

        <input
            type="text"
            class="education-input"
            data-field="degree"
            value="${education.degree || ""}"
            placeholder="Bachelor of Technology">

    </div>

    <div class="form-group">

        <label>

            Institution

        </label>

        <input
            type="text"
            class="education-input"
            data-field="institution"
            value="${education.institution || ""}"
            placeholder="ICFAI University">

    </div>

    <div class="form-row">

        <div class="form-group">

            <label>

                Start Year

            </label>

            <input
                type="text"
                class="education-input"
                data-field="startYear"
                value="${education.startYear || ""}"
                placeholder="2021">

        </div>

        <div class="form-group">

            <label>

                End Year

            </label>

            <input
                type="text"
                class="education-input"
                data-field="endYear"
                value="${education.endYear || ""}"
                placeholder="2025">

        </div>

    </div>

    <div class="form-group">

        <label>

            CGPA / Percentage

        </label>

        <input
            type="text"
            class="education-input"
            data-field="score"
            value="${education.score || ""}"
            placeholder="CGPA 8.50 / 10">

    </div>

    <hr>

</div>

`;

    }

};