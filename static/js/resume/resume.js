/* =====================================================
   NOVUS RESUME INITIALIZER
===================================================== */


/* =====================================================
   PAGE INITIALIZATION
===================================================== */

async function initializeResumeStudio() {

    console.log("NOVUS: Resume Studio initializer started.");


    /*
     * Safety checks
     */
    if (typeof ResumeEngine === "undefined") {

        console.error(
            "NOVUS ERROR: ResumeEngine is not available."
        );

        return;
    }


    if (typeof ResumeAPI === "undefined") {

        console.error(
            "NOVUS ERROR: ResumeAPI is not available."
        );

        return;
    }


    console.log(
        "NOVUS: ResumeEngine and ResumeAPI are available."
    );


    let loadedFromDatabase = false;


    /* =================================================
       LOAD FROM DATABASE
    ================================================= */

    try {

        console.log(
            "NOVUS: Calling ResumeAPI.load()..."
        );


        const result =
            await ResumeAPI.load();


        console.log(
            "NOVUS: Resume API response:",
            result
        );


        if (
            result &&
            result.success &&
            result.resume
        ) {

            Object.assign(
                ResumeEngine.state,
                result.resume
            );


            loadedFromDatabase = true;


            console.log(
                "NOVUS: Database resume loaded:",
                ResumeEngine.state
            );
        }

        else {

            console.warn(
                "NOVUS: API returned no resume data.",
                result
            );
        }


    } catch (error) {

        console.error(
            "NOVUS: Database resume load failed:",
            error
        );
    }


    /* =================================================
       LOCAL DRAFT FALLBACK
    ================================================= */

    if (!loadedFromDatabase) {

        console.log(
            "NOVUS: Loading local draft..."
        );


        try {

            if (
                ResumeEngine.storage &&
                typeof ResumeEngine.storage.loadDraft ===
                "function"
            ) {

                ResumeEngine.storage.loadDraft();
            }

        } catch (error) {

            console.error(
                "NOVUS: Local draft loading failed:",
                error
            );
        }
    }


    /* =================================================
       VALIDATE STATE
    ================================================= */

    try {

        ResumeEngine.validateState();

    } catch (error) {

        console.error(
            "NOVUS: Resume state validation failed:",
            error
        );
    }


    /* =================================================
       INITIALIZE MODULES
    ================================================= */

    bindInputs();

    initializeCards();


    /* =================================================
       POPULATE SIMPLE INPUTS
    ================================================= */

    populateInputs();


    /* =================================================
       SECTION MANAGER
    ================================================= */

    if (
        typeof SectionManager !== "undefined"
    ) {

        try {

            SectionManager.init();

        } catch (error) {

            console.error(
                "NOVUS: SectionManager initialization failed:",
                error
            );
        }
    }


    /* =================================================
       LIVE PREVIEW
    ================================================= */

    if (
        typeof updatePreview === "function"
    ) {

        try {

            updatePreview(
                ResumeEngine.state
            );

        } catch (error) {

            console.error(
                "NOVUS: Preview update failed:",
                error
            );
        }
    }


    /* =================================================
       COMPLETION
    ================================================= */

    if (
        typeof updateCompletion === "function"
    ) {

        try {

            updateCompletion(
                ResumeEngine.state
            );

        } catch (error) {

            console.error(
                "NOVUS: Completion update failed:",
                error
            );
        }
    }


    /* =================================================
       SAVE SUPPORT
    ================================================= */

    initializeSaveButton();


    /* =================================================
       LAST SAVED
    ================================================= */

    if (loadedFromDatabase) {

        updateLastSavedFromServer();

    } else {

        updateSaveStatus("Not saved yet");
    }


    console.log(
        "NOVUS: Resume Studio initialization complete."
    );
}


/* =====================================================
   START INITIALIZATION
===================================================== */

if (
    document.readyState === "loading"
) {

    document.addEventListener(
        "DOMContentLoaded",
        initializeResumeStudio
    );

} else {

    /*
     * DOMContentLoaded already happened.
     * Start immediately.
     */
    initializeResumeStudio();
}


/* =====================================================
   BIND INPUTS
===================================================== */

function bindInputs() {

    if (
        typeof EducationModule !== "undefined"
    ) {

        EducationModule.init();
    }


    if (
        typeof SkillsModule !== "undefined"
    ) {

        SkillsModule.init();
    }


    if (
        typeof ProjectsModule !== "undefined"
    ) {

        ProjectsModule.init();
    }


    if (
        typeof ExperienceModule !== "undefined"
    ) {

        ExperienceModule.init();
    }


    if (
        typeof CertificationModule !== "undefined"
    ) {

        CertificationModule.init();
    }


    /*
     * Simple inputs
     */
    document
        .querySelectorAll(".resume-input")
        .forEach(input => {

            if (
                input.dataset.bound === "true"
            ) {

                return;
            }


            input.dataset.bound = "true";


            input.addEventListener(
                "input",
                updateResumeState
            );
        });


    /*
     * Resume title
     */
    const titleInput =
        document.querySelector(
            ".resume-title"
        );


    if (
        titleInput &&
        titleInput.dataset.bound !== "true"
    ) {

        titleInput.dataset.bound = "true";


        titleInput.addEventListener(
            "input",
            () => {

                ResumeEngine.state.title =
                    titleInput.value.trim();


                ResumeEngine.storage.saveDraft();

                autoSaveResume();
            }
        );
    }
}


/* =====================================================
   UPDATE SIMPLE INPUT STATE
===================================================== */

function updateResumeState(event) {

    const input =
        event.target;


    const section =
        input.dataset.section;


    const field =
        input.dataset.field;


    if (
        !section ||
        !(section in ResumeEngine.state)
    ) {

        return;
    }


    const value =
        input.value;


    if (
        typeof ResumeEngine.state[section] ===
        "object" &&
        ResumeEngine.state[section] !== null &&
        field
    ) {

        ResumeEngine.state[section][field] =
            value.trim();

    } else {

        ResumeEngine.state[section] =
            value.trim();
    }


    ResumeEngine.isDirty = true;


    ResumeEngine.storage.saveDraft();

    autoSaveResume();


    if (
        typeof updatePreview === "function"
    ) {

        updatePreview(
            ResumeEngine.state
        );
    }


    if (
        typeof updateCompletion === "function"
    ) {

        updateCompletion(
            ResumeEngine.state
        );
    }
}


/* =====================================================
   INITIALIZE COLLAPSIBLE CARDS
===================================================== */

function initializeCards() {

    document
        .querySelectorAll(".collapse-btn")
        .forEach(button => {

            if (
                button.dataset.bound === "true"
            ) {

                return;
            }


            button.dataset.bound = "true";


            button.addEventListener(
                "click",
                event => {

                    event.preventDefault();


                    const section =
                        button.closest(
                            ".editor-card"
                        );


                    if (!section) {

                        return;
                    }


                    section.classList.toggle(
                        "collapsed"
                    );
                }
            );
        });
}


/* =====================================================
   POPULATE INPUTS
===================================================== */

function populateInputs() {

    console.log(
        "NOVUS: Populating editor inputs..."
    );


    document
        .querySelectorAll(".resume-input")
        .forEach(input => {

            const section =
                input.dataset.section;


            const field =
                input.dataset.field;


            if (
                !section
            ) {

                return;
            }


            if (
                typeof ResumeEngine.state[section] ===
                "object" &&
                ResumeEngine.state[section] !== null &&
                field
            ) {

                const value =
                    ResumeEngine.state[section][field];


                if (
                    value !== undefined &&
                    value !== null
                ) {

                    input.value = value;
                }


            } else if (
                ResumeEngine.state[section] !==
                undefined
            ) {

                input.value =
                    ResumeEngine.state[section] || "";
            }
        });


    /*
     * Resume title
     */
    const titleInput =
        document.querySelector(
            ".resume-title"
        );


    if (
        titleInput &&
        ResumeEngine.state.title
    ) {

        titleInput.value =
            ResumeEngine.state.title;
    }


    console.log(
        "NOVUS: Editor inputs populated."
    );
}


/* =====================================================
   SAVE BUTTON SUPPORT
===================================================== */

function initializeSaveButton() {

    const button =
        document.getElementById(
            "saveResumeBtn"
        );


    if (
        !button ||
        button.dataset.bound === "true"
    ) {

        return;
    }


    button.dataset.bound = "true";


    button.addEventListener(
        "click",
        async event => {

            event.preventDefault();

            await saveResumeNow();
        }
    );
}


/* =====================================================
   SAVE RESUME
===================================================== */

async function saveResumeNow() {

    const button =
        document.getElementById("saveResumeBtn");

    if (button) button.disabled = true;

    if (
        typeof ResumeAPI.hasMeaningfulContent === "function" &&
        !ResumeAPI.hasMeaningfulContent(
            ResumeEngine.state
        )
    ) {

        updateSaveStatus("Not saved yet");

        if (button) button.disabled = false;

        return;
    }

    updateSaveStatus("Saving...");

    try {

        const result =
            await ResumeAPI.save();


        if (
            !result.success
        ) {

            throw new Error(
                result.message ||
                "Save failed"
            );
        }


        ResumeEngine.isDirty =
            false;


        ResumeEngine.lastSaved =
            new Date();


        ResumeEngine.storage.saveDraft();


        updateSaveStatus(
            "Saved"
        );


        updateLastSaved(
            ResumeEngine.lastSaved
        );


    } catch (error) {

        console.error(
            "NOVUS: Resume save failed:",
            error
        );


        updateSaveStatus(
            "Save Failed"
        );


    } finally {

        if (button) {

            button.disabled = false;
        }
    }
}


/* =====================================================
   LAST SAVED TIME
===================================================== */

function updateLastSaved(date) {

    const element =
        document.getElementById(
            "lastSavedValue"
        );


    if (
        !element ||
        !date
    ) {

        return;
    }


    element.textContent =
        date.toLocaleTimeString(
            [],
            {
                hour: "2-digit",
                minute: "2-digit"
            }
        );
}


/* =====================================================
   LOAD LAST SAVED TIME
===================================================== */

async function updateLastSavedFromServer() {

    const element =
        document.getElementById(
            "lastSavedValue"
        );


    if (!element) {

        return;
    }


    try {

        const resumeId =
            ResumeAPI.getResumeId();


        if (!resumeId) {

            console.warn(
                "NOVUS: Resume ID not found."
            );

            return;
        }


        const response =
            await fetch(
                `/api/resume/meta/${resumeId}`
            );


        if (!response.ok) {

            return;
        }


        const data =
            await response.json();


        if (
            data.success &&
            data.updated_at
        ) {

            const date =
                new Date(
                    data.updated_at.replace(
                        " ",
                        "T"
                    ) + "Z"
                );


            if (
                !Number.isNaN(
                    date.getTime()
                )
            ) {

                updateLastSaved(
                    date
                );
            }
        }


    } catch (error) {

        console.warn(
            "NOVUS: Could not load last saved time.",
            error
        );
    }
}