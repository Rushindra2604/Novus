/* ==========================================
   NOVUS EXPERIENCE MODULE
========================================== */

const ExperienceModule = {

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

        this.container = document.getElementById("experienceContainer");

        if (!this.container) return;

        if (!Array.isArray(ResumeEngine.state.experience)) {

            ResumeEngine.state.experience = [];

        }

        if (ResumeEngine.state.experience.length === 0) {

            this.addExperience(false);

        }

        else {

            this.render();

        }

        document
            .getElementById("addExperienceBtn")
            ?.addEventListener("click", () => {

                this.addExperience();

            });

        this.bindEvents();

    },

    /* ==========================================
       DEFAULT EXPERIENCE
    ========================================== */

    createExperience() {

        return {

            jobTitle: "",

            company: "",

            location: "",

            startMonth: "",

            startYear: "",

            endMonth: "",

            endYear: "",

            currentlyWorking: false,

            responsibilities: [

                "",
                "",
                ""

            ],

            expanded: true

        };

    },

    /* ==========================================
       ADD EXPERIENCE
    ========================================== */

    addExperience(save = true) {

        ResumeEngine.state.experience.push(

            this.createExperience()

        );

        ResumeEngine.state.experience.forEach(exp => {

            exp.expanded = false;

        });

        ResumeEngine.state.experience[

            ResumeEngine.state.experience.length - 1

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

        ResumeEngine.state.experience.forEach(

            (experience, index) => {

                this.container.insertAdjacentHTML(

                    "beforeend",

                    this.template(experience, index)

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

            const item = input.closest(".experience-item");

            if (!item) return;

            const index = Number(item.dataset.index);

            const experience = ResumeEngine.state.experience[index];

            if (!experience) return;

            if (input.classList.contains("experience-input")) {

                const field = input.dataset.field;

                experience[field] = input.value.trim();

            }

            if (input.classList.contains("responsibility-input")) {

                const responsibilityIndex = Number(

                    input.dataset.responsibility

                );

                experience.responsibilities[responsibilityIndex] =

                    input.value;

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
           CHANGE EVENTS
        ========================== */

        this.container.addEventListener("change", (event) => {

            const checkbox = event.target.closest(".current-job-checkbox");

            if (!checkbox) return;

            const item = checkbox.closest(".experience-item");

            const index = Number(item.dataset.index);

            ResumeEngine.state.experience[index].currentlyWorking =

                checkbox.checked;

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

        /* ==========================
           CLICK EVENTS
        ========================== */

        this.container.addEventListener("click", (event) => {

            /* --------------------------
               TOGGLE EXPERIENCE
            -------------------------- */

            const toggleBtn = event.target.closest(".toggle-experience-btn");

            if (toggleBtn) {

                const index = Number(

                    toggleBtn.closest(".experience-item")

                        .dataset.index

                );

                this.toggleExperience(index);

                return;

            }

            /* --------------------------
               REMOVE EXPERIENCE
            -------------------------- */

            const removeBtn = event.target.closest(".remove-experience-btn");

            if (removeBtn) {

                const index = Number(

                    removeBtn.closest(".experience-item")

                        .dataset.index

                );

                this.removeExperience(index);

                return;

            }

            /* --------------------------
               ADD RESPONSIBILITY
            -------------------------- */

            const addBtn = event.target.closest(".add-responsibility-btn");

            if (addBtn) {

                const index = Number(

                    addBtn.closest(".experience-item")

                        .dataset.index

                );

                this.addResponsibility(index);

                return;

            }

            /* --------------------------
               REMOVE RESPONSIBILITY
            -------------------------- */

            const removeResponsibility = event.target.closest(".remove-responsibility-btn");

            if (removeResponsibility) {

                const item = removeResponsibility.closest(".experience-item");

                const index = Number(item.dataset.index);

                const responsibilityIndex = Number(

                    removeResponsibility.dataset.responsibility

                );

                this.removeResponsibility(

                    index,

                    responsibilityIndex

                );

            }

        });

    },
    
    /* ==========================================
       TOGGLE EXPERIENCE
    ========================================== */

    toggleExperience(index) {

        ResumeEngine.state.experience.forEach((experience, i) => {

            experience.expanded =

                i === index

                    ? !experience.expanded

                    : false;

        });

        this.render();

    },

    /* ==========================================
       REMOVE EXPERIENCE
    ========================================== */

    removeExperience(index) {

        const experience = ResumeEngine.state.experience[index];

        const title =

            experience.jobTitle ||

            `Experience ${index + 1}`;

        const confirmed = confirm(

            `Delete "${title}" ?`

        );

        if (!confirmed) return;

        ResumeEngine.state.experience.splice(index, 1);

        if (ResumeEngine.state.experience.length === 0) {

            this.addExperience(false);

            return;

        }

        ResumeEngine.state.experience[0].expanded = true;

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
       ADD RESPONSIBILITY
    ========================================== */

    addResponsibility(index) {

        ResumeEngine.state.experience[index]

            .responsibilities

            .push("");

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
       REMOVE RESPONSIBILITY
    ========================================== */

    removeResponsibility(index, responsibilityIndex) {

        const responsibilities =

            ResumeEngine.state.experience[index]

                .responsibilities;

        if (responsibilities.length <= 1) return;

        responsibilities.splice(

            responsibilityIndex,

            1

        );

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
       MONTH OPTIONS
    ========================================== */

    monthOptions(selectedMonth = "") {

        return this.months.map(month => `

            <option
                value="${month}"
                ${selectedMonth === month ? "selected" : ""}>

                ${month}

            </option>

        `).join("");

    },

    /* ==========================================
       YEAR OPTIONS
    ========================================== */

    yearOptions(selectedYear = "") {

        const currentYear = new Date().getFullYear();

        let options = "";

        for (

            let year = currentYear + 5;

            year >= 1990;

            year--

        ) {

            options += `

<option
    value="${year}"
    ${String(selectedYear) === String(year) ? "selected" : ""}>

    ${year}

</option>

`;

        }

        return options;

    },

    /* ==========================================
       TEMPLATE
    ========================================== */

    template(experience, index) {

        return `

<div class="experience-item" data-index="${index}">

    <div class="experience-header">

        <button
            type="button"
            class="toggle-experience-btn">

            <i data-lucide="${experience.expanded ? "chevron-down" : "chevron-right"}"></i>

        </button>

        <h3>

            ${experience.jobTitle || `Experience ${index + 1}`}

        </h3>

        <button
            type="button"
            class="remove-experience-btn">

            <i data-lucide="trash-2"></i>

        </button>

    </div>

    ${experience.expanded ? this.experienceContent(experience, index) : ""}

</div>

`;

    },

    /* ==========================================
       EXPERIENCE CONTENT
    ========================================== */

    experienceContent(experience, index) {

        return `

<div class="experience-body">

    <!-- ===============================
         JOB TITLE
    ================================ -->

    <div class="form-group">

        <label>

            Job Title

        </label>

        <input
            type="text"
            class="experience-input"
            data-field="jobTitle"
            value="${experience.jobTitle || ""}"
            placeholder="Python Backend Developer">

    </div>

    <!-- ===============================
         COMPANY
    ================================ -->

    <div class="form-group">

        <label>

            Company Name

        </label>

        <input
            type="text"
            class="experience-input"
            data-field="company"
            value="${experience.company || ""}"
            placeholder="ABC Technologies">

    </div>

    <!-- ===============================
         LOCATION
    ================================ -->

    <div class="form-group">

        <label>

            Location (Optional)

        </label>

        <input
            type="text"
            class="experience-input"
            data-field="location"
            value="${experience.location || ""}"
            placeholder="Hyderabad">

    </div>

    <!-- ===============================
         START DATE
    ================================ -->

    <div class="form-row">

        <div class="form-group">

            <label>

                Start Month

            </label>

            <select
                class="experience-input"
                data-field="startMonth">

                <option value="">Month</option>

                ${this.monthOptions(experience.startMonth)}

            </select>

        </div>

        <div class="form-group">

            <label>

                Start Year

            </label>

            <select
                class="experience-input"
                data-field="startYear">

                <option value="">Year</option>

                ${this.yearOptions(experience.startYear)}

            </select>

        </div>

    </div>

    <!-- ===============================
         CURRENT JOB
    ================================ -->

    <div class="form-group">

        <label class="checkbox-label">

            <input
                type="checkbox"
                class="current-job-checkbox"
                ${experience.currentlyWorking ? "checked" : ""}>

            Currently Working Here

        </label>

    </div>

    <!-- ===============================
         END DATE
    ================================ -->

    <div class="form-row">

        <div class="form-group">

            <label>

                End Month

            </label>

            <select
                class="experience-input"
                data-field="endMonth"
                ${experience.currentlyWorking ? "disabled" : ""}>

                <option value="">Month</option>

                ${this.monthOptions(experience.endMonth)}

            </select>

        </div>

        <div class="form-group">

            <label>

                End Year

            </label>

            <select
                class="experience-input"
                data-field="endYear"
                ${experience.currentlyWorking ? "disabled" : ""}>

                <option value="">Year</option>

                ${this.yearOptions(experience.endYear)}

            </select>

        </div>

    </div>

    <!-- ===============================
         RESPONSIBILITIES
    ================================ -->

    <div class="form-group">

        <div class="field-label-row">
            <label>Responsibilities</label>
            <button
                type="button"
                class="secondary-btn add-responsibility-btn">
                <i data-lucide="plus"></i>
                Add Responsibility
            </button>
        </div>

        ${experience.responsibilities.map((responsibility, responsibilityIndex) => `

            <div class="bullet-row">

                <input
                    type="text"
                    class="responsibility-input"
                    data-responsibility="${responsibilityIndex}"
                    value="${responsibility}"
                    placeholder="Developed REST APIs using Flask...">

                <button
                    type="button"
                    class="remove-responsibility-btn"
                    data-responsibility="${responsibilityIndex}">

                    <i data-lucide="trash-2"></i>

                </button>

            </div>

        `).join("")}

    </div>

    <hr>

</div>

`;

    }

};