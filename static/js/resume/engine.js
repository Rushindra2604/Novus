/* ==========================================
   NOVUS RESUME ENGINE
========================================== */

const ResumeEngine = {

    /* ==========================================
       EVENT SYSTEM
    ========================================== */

    events: {},

    on(event, callback) {

        if (!this.events[event]) {

            this.events[event] = [];

        }

        this.events[event].push(callback);

    },

    emit(event, data) {

        if (!this.events[event]) return;

        this.events[event].forEach(callback => {

            callback(data);

        });

    },

    state: {

        title: "",

        personal: {
            fullName: "",
            headline: "",
            email: "",
            phone: "",
            location: "",
            linkedin: "",
            github: "",
            portfolio: ""
        },

        summary: "",

        education: [],

        skills: {

            languages: [],
            frameworks: [],
            databases: [],
            tools: [],
            others: []

        },

        projects: [],

        experience: [],

        certifications: [],

        additionalSections: []

    },

    validateState() {

        const defaults = {

            languages: [],
            frameworks: [],
            databases: [],
            tools: [],
            others: []

        };

        if (!this.state.skills) {

            this.state.skills = structuredClone(defaults);

        }

        Object.keys(defaults).forEach(key => {

            if (!Array.isArray(this.state.skills[key])) {

                this.state.skills[key] = [];

            }

        });

    },

    version: 1,

    isDirty: false,

    lastSaved: null

};

ResumeEngine.validateState();