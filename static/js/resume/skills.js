/* ==========================================
   NOVUS SKILLS MODULE
========================================== */

const SkillsModule = {

    container: null,

    categories: [

        {
            key: "languages",
            title: "Programming Languages",
            placeholder: "Python"
        },

        {
            key: "frameworks",
            title: "Frameworks & Libraries",
            placeholder: "Flask"
        },

        {
            key: "databases",
            title: "Databases",
            placeholder: "SQLite"
        },

        {
            key: "tools",
            title: "Tools & Platforms",
            placeholder: "Git"
        },

        {
            key: "others",
            title: "Other Skills",
            placeholder: "REST APIs"
        }

    ],

    init() {

        this.container = document.getElementById("skillsContainer");

        if (!this.container) return;

        if (!ResumeEngine.state.skills) {

            ResumeEngine.state.skills = {

                languages: [],
                frameworks: [],
                databases: [],
                tools: [],
                others: []

            };

        }

        this.render();

        this.bindEvents();

    },

    render() {

        this.container.innerHTML = "";

        this.categories.forEach(category => {

            this.container.insertAdjacentHTML(

                "beforeend",

                this.categoryTemplate(category)

            );

        });

    },

    categoryTemplate(category) {

        console.log(category.key);
        console.log(ResumeEngine.state.skills);

        const tags = ResumeEngine.state.skills[category.key] || [];

        return `

<div class="skills-category" data-category="${category.key}">

    <div class="category-heading">
        <h3>${category.title}</h3>
        <button
            type="button"
            class="add-skill-btn"
            data-category="${category.key}">
            Add
        </button>
    </div>

    <div class="skill-input-row">

        <input
            type="text"
            class="skill-input"
            data-category="${category.key}"
            placeholder="${category.placeholder}">

    </div>

    <div class="skills-tags">

        ${tags.map(skill => `

            <span class="skill-tag">

                ${skill}

                <button
                    type="button"
                    class="remove-skill-btn"
                    data-category="${category.key}"
                    data-skill="${skill}">

                    ×

                </button>

            </span>

        `).join("")}

    </div>

    <hr>

</div>

`;

    },

    bindEvents() {

        /* ==========================
           ENTER / COMMA
        ========================== */

        this.container.addEventListener("keydown", (event) => {

            const input = event.target.closest(".skill-input");

            if (!input) return;

            if (event.key === "Enter" || event.key === ",") {

                event.preventDefault();

                this.addSkill(

                    input.dataset.category,

                    input.value

                );

                input.value = "";

            }

        });

        /* ==========================
           ADD BUTTON
        ========================== */

        this.container.addEventListener("click", (event) => {

            const addBtn = event.target.closest(".add-skill-btn");

            if (addBtn) {

                const category = addBtn.dataset.category;

                const input = this.container.querySelector(

                    `.skill-input[data-category="${category}"]`

                );

                this.addSkill(category, input.value);

                input.value = "";

                return;

            }

            /* ==========================
               REMOVE TAG
            ========================== */

            const removeBtn = event.target.closest(".remove-skill-btn");

            if (removeBtn) {

                this.removeSkill(

                    removeBtn.dataset.category,

                    removeBtn.dataset.skill

                );

            }

        });

    },

    addSkill(category, value) {

        value = value.trim();

        if (!value) return;

        const skills = ResumeEngine.state.skills[category] || [];
        ResumeEngine.state.skills[category] = skills;

        const exists = skills.some(

            skill =>

                skill.toLowerCase() ===

                value.toLowerCase()

        );

        if (exists) return;

        skills.push(value);

        this.render();

        ResumeEngine.storage.saveDraft();

        autoSaveResume();

        if (typeof updatePreview === "function") {

            updatePreview(ResumeEngine.state);

        }

        if (typeof updateCompletion === "function") {

            updateCompletion(ResumeEngine.state);

        }
        console.log(category);
        console.log(ResumeEngine.state.skills);

    },

    removeSkill(category, skill) {

        ResumeEngine.state.skills[category] =

            ResumeEngine.state.skills[category]

                .filter(

                    item => item !== skill

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

    }

};