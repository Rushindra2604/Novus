/* ==========================================
   NOVUS PROJECTS MODULE
========================================== */
console.log("Projects Module Loaded");
const ProjectsModule = {

    container: null,

    init() {

        this.container = document.getElementById("projectsContainer");

        if (!this.container) return;

        if (!Array.isArray(ResumeEngine.state.projects)) {

            ResumeEngine.state.projects = [];

        }

        if (ResumeEngine.state.projects.length === 0) {

            this.addProject(false);

        }

        else {

            this.render();

        }

        document
            .getElementById("addProjectBtn")
            ?.addEventListener("click", () => {

                this.addProject();

            });

        this.bindEvents();

    },

    /* ==========================================
       DEFAULT PROJECT
    ========================================== */

    createProject() {

        return {

            title: "",

            technologies: [],

            bullets: [

                "",
                "",
                ""

            ],

            github: "",

            liveDemo: "",

            expanded: true

        };

    },

    /* ==========================================
       ADD PROJECT
    ========================================== */

    addProject(save = true) {

        ResumeEngine.state.projects.push(

            this.createProject()

        );

        ResumeEngine.state.projects.forEach(project => {

            project.expanded = false;

        });

        ResumeEngine.state.projects[

            ResumeEngine.state.projects.length - 1

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

        ResumeEngine.state.projects.forEach(

            (project, index) => {

                this.container.insertAdjacentHTML(

                    "beforeend",

                    this.template(project, index)

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
           INPUT CHANGES
        ========================== */

        this.container.addEventListener("input", (event) => {

            const input = event.target;

            const item = input.closest(".project-item");

            if (!item) return;

            const index = Number(item.dataset.index);

            const project = ResumeEngine.state.projects[index];

            if (!project) return;

            /* --------------------------
               NORMAL INPUTS
            -------------------------- */

            if (input.classList.contains("project-input")) {

                const field = input.dataset.field;

                project[field] = input.value.trim();

            }

            /* --------------------------
               BULLET INPUTS
            -------------------------- */

            if (input.classList.contains("bullet-input")) {

                const bulletIndex = Number(

                    input.dataset.bullet

                );

                project.bullets[bulletIndex] =

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
           CLICK EVENTS
        ========================== */

        this.container.addEventListener("click", (event) => {

            /* --------------------------
               COLLAPSE
            -------------------------- */

            const collapseBtn = event.target.closest(".toggle-project-btn");

            if (collapseBtn) {

                const index = Number(

                    collapseBtn.closest(".project-item")

                        .dataset.index

                );

                this.toggleProject(index);

                return;

            }

            /* --------------------------
               DELETE PROJECT
            -------------------------- */

            const deleteBtn = event.target.closest(".remove-project-btn");

            if (deleteBtn) {

                const index = Number(

                    deleteBtn.closest(".project-item")

                        .dataset.index

                );

                this.removeProject(index);

                return;

            }

            /* --------------------------
               ADD TECH
            -------------------------- */

            const addTech = event.target.closest(".add-tech-btn");

            if (addTech) {

                const item = addTech.closest(".project-item");

                const index = Number(item.dataset.index);

                const input = item.querySelector(".tech-input");

                this.addTechnology(

                    index,

                    input.value

                );

                input.value = "";

                return;

            }

            /* --------------------------
               REMOVE TECH
            -------------------------- */

            const removeTech = event.target.closest(".remove-tech-btn");

            if (removeTech) {

                const item = removeTech.closest(".project-item");

                const index = Number(item.dataset.index);

                this.removeTechnology(

                    index,

                    removeTech.dataset.tech

                );

                return;

            }

            /* --------------------------
               ADD BULLET
            -------------------------- */

            const addBullet = event.target.closest(".add-bullet-btn");

            if (addBullet) {

                const item = addBullet.closest(".project-item");

                const index = Number(item.dataset.index);

                this.addBullet(index);

                return;

            }

            /* --------------------------
               REMOVE BULLET
            -------------------------- */

            const removeBullet = event.target.closest(".remove-bullet-btn");

            if (removeBullet) {

                const item = removeBullet.closest(".project-item");

                const index = Number(item.dataset.index);

                const bullet = Number(

                    removeBullet.dataset.bullet

                );

                this.removeBullet(

                    index,

                    bullet

                );

            }

        });

        /* ==========================
           ENTER = ADD TECH
        ========================== */

        this.container.addEventListener("keydown", (event) => {

            const input = event.target.closest(".tech-input");

            if (!input) return;

            if (event.key === "Enter" || event.key === ",") {

                event.preventDefault();

                const item = input.closest(".project-item");

                const index = Number(item.dataset.index);

                this.addTechnology(

                    index,

                    input.value

                );

                input.value = "";

            }

        });

    },   

    /*==========================================
       TOGGLE PROJECT
    ========================================== */

    toggleProject(index) {

        ResumeEngine.state.projects.forEach((project, i) => {

            project.expanded = i === index
                ? !project.expanded
                : false;

        });

        this.render();

    },

    /* ==========================================
       REMOVE PROJECT
    ========================================== */

    removeProject(index) {

        const project = ResumeEngine.state.projects[index];

        const title = project.title || `Project ${index + 1}`;

        const confirmed = confirm(

            `Delete "${title}" ?`

        );

        if (!confirmed) return;

        ResumeEngine.state.projects.splice(index, 1);

        if (ResumeEngine.state.projects.length === 0) {

            this.addProject(false);

            return;

        }

        ResumeEngine.state.projects[0].expanded = true;

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
       ADD TECHNOLOGY
    ========================================== */

    addTechnology(index, value) {

        value = value.trim();

        if (!value) return;

        const technologies =
            ResumeEngine.state.projects[index].technologies;

        const exists = technologies.some(

            tech =>

                tech.toLowerCase() ===

                value.toLowerCase()

        );

        if (exists) return;

        technologies.push(value);

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
       REMOVE TECHNOLOGY
    ========================================== */

    removeTechnology(index, technology) {

        ResumeEngine.state.projects[index].technologies =

            ResumeEngine.state.projects[index]

                .technologies

                .filter(

                    tech => tech !== technology

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
       ADD BULLET
    ========================================== */

    addBullet(index) {

        ResumeEngine.state.projects[index]

            .bullets

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
       REMOVE BULLET
    ========================================== */

    removeBullet(index, bulletIndex) {

        const bullets =

            ResumeEngine.state.projects[index]

                .bullets;

        if (bullets.length <= 1) return;

        bullets.splice(bulletIndex, 1);

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

    template(project, index) {

        return `

<div class="project-item" data-index="${index}">

    <div class="project-header">

        <button
            type="button"
            class="toggle-project-btn">

            <i data-lucide="${project.expanded ? "chevron-down" : "chevron-right"}"></i>

        </button>

        <h3>

            ${project.title || `Project ${index + 1}`}

        </h3>

        <button
            type="button"
            class="remove-project-btn">

            <i data-lucide="trash-2"></i>

        </button>

    </div>

    ${project.expanded ? this.projectContent(project, index) : ""}

</div>

`;

    },

    /*==========================================
       PROJECT CONTENT
    ==========================================*/

    projectContent(project, index) {

        return `

<div class="project-body">

    <!-- ===============================
         PROJECT TITLE
    ================================ -->

    <div class="form-group">

        <label>

            Project Title

        </label>

        <input
            type="text"
            class="project-input"
            data-field="title"
            value="${project.title || ""}"
            placeholder="Resume Optimizer">

    </div>

    <!-- ===============================
         TECH STACK
    ================================ -->

    <div class="form-group">

        <div class="field-label-row">
            <label>Tech Stack</label>
            <button type="button" class="add-tech-btn">Add</button>
        </div>

        <div class="tech-input-row">

            <input
                type="text"
                class="tech-input"
                placeholder="Python">

        </div>

        <div class="tech-tags">

            ${project.technologies.map(tech => `

                <span class="skill-tag">

                    ${tech}

                    <button
                        type="button"
                        class="remove-tech-btn"
                        data-tech="${tech}">

                        ×

                    </button>

                </span>

            `).join("")}

        </div>

    </div>

    <!-- ===============================
         PROJECT HIGHLIGHTS
    ================================ -->

    <div class="form-group">

        <div class="field-label-row">
            <label>Project Highlights</label>
            <button
                type="button"
                class="secondary-btn add-bullet-btn">
                <i data-lucide="plus"></i>
                Add Bullet
            </button>
        </div>

        ${project.bullets.map((bullet, bulletIndex) => `

            <div class="bullet-row">

                <input
                    type="text"
                    class="bullet-input"
                    data-bullet="${bulletIndex}"
                    value="${bullet}"
                    placeholder="Describe an achievement...">

                <button
                    type="button"
                    class="remove-bullet-btn"
                    data-bullet="${bulletIndex}">

                    <i data-lucide="trash-2"></i>

                </button>

            </div>

        `).join("")}

    </div>

    <!-- ===============================
         GITHUB
    ================================ -->

    <div class="form-group">

        <label>

            GitHub Repository

        </label>

        <input
            type="url"
            class="project-input"
            data-field="github"
            value="${project.github || ""}"
            placeholder="https://github.com/username/project">

    </div>

    <!-- ===============================
         LIVE DEMO
    ================================ -->

    <div class="form-group">

        <label>

            Live Demo

        </label>

        <input
            type="url"
            class="project-input"
            data-field="liveDemo"
            value="${project.liveDemo || ""}"
            placeholder="https://example.com">

    </div>

    <hr>

</div>

`;

    }

};