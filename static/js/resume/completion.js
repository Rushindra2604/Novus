/* ==========================================
   NOVUS COMPLETION ENGINE
========================================== */

const SECTION_WEIGHTS = {

    personal: 15,

    summary: 10,

    education: 5,

    skills: 15,

    projects: 20,

    experience: 10,

    certifications: 10,

    additional: 10,

    keywords: 5

};

function updateCompletion(state) {

    let score = 0;

    /* ==========================================
       PERSONAL
    ========================================== */

    const personal = state.personal;

    const personalComplete =

        personal.fullName &&
        personal.headline &&
        personal.email &&
        personal.phone;

    if (personalComplete) {

        score += SECTION_WEIGHTS.personal;

        markCompleted("progress-personal");

    }

    else {

        markIncomplete("progress-personal");

    }

    /* ==========================================
       SUMMARY
    ========================================== */

    const summaryComplete =

        state.summary &&
        state.summary.trim() !== "";

    if (summaryComplete) {

        score += SECTION_WEIGHTS.summary;

        markCompleted("progress-summary");

    }

    else {

        markIncomplete("progress-summary");

    }

    /* ==========================================
       EDUCATION
    ========================================== */

    const educationComplete =

        state.education &&
        state.education.length > 0 &&
        state.education.every(edu =>

            edu.degree &&
            edu.institution &&
            edu.startYear &&
            edu.endYear &&
            edu.score

        );

    if (educationComplete) {

        score += SECTION_WEIGHTS.education;

        markCompleted("progress-education");

    }

    else {

        markIncomplete("progress-education");

    }

    /* ==========================================
    SKILLS
    ========================================== */

    const skills = state.skills || {};

    const skillsComplete =

        (skills.languages?.length || 0) +

        (skills.frameworks?.length || 0) +

        (skills.databases?.length || 0) +

        (skills.tools?.length || 0) +

        (skills.others?.length || 0);

    if (skillsComplete > 0) {

        score += SECTION_WEIGHTS.skills;

        markCompleted("progress-skills");

    }

    else {

        markIncomplete("progress-skills");

    }

    /* ==========================================
       PROJECTS
    ========================================== */

    const projectsComplete =

        state.projects &&
        state.projects.length > 0 &&
        state.projects.every(project =>

            project.title &&
            project.technologies &&
            project.technologies.length > 0 &&
            project.bullets &&
            project.bullets.some(bullet => bullet.trim() !== "")

        );

    if (projectsComplete) {

        score += SECTION_WEIGHTS.projects;

        markCompleted("progress-projects");

    }

    else {

        markIncomplete("progress-projects");

    }

    /* ==========================================
       EXPERIENCE
    ========================================== */

    const experienceComplete =

        state.experience &&
        state.experience.length > 0 &&
        state.experience.every(experience =>

            experience.jobTitle &&
            experience.company &&
            experience.responsibilities &&
            experience.responsibilities.some(
                responsibility => responsibility.trim() !== ""
            )

        );

    if (experienceComplete) {

        score += SECTION_WEIGHTS.experience;

        markCompleted("progress-experience");

    }
    else {

        markIncomplete("progress-experience");

    }

    /* ==========================================
       CERTIFICATIONS
    ========================================== */

    const certificationsComplete =

        state.certifications &&
        state.certifications.length > 0 &&
        state.certifications.every(certification =>

            certification.name &&
            certification.organization

        );

    if (certificationsComplete) {

        score += SECTION_WEIGHTS.certifications;

        markCompleted("progress-certifications");

    }
    else {

        markIncomplete("progress-certifications");

    }

    /* ==========================================
       SCORE
    ========================================== */

    const completionValue = document.getElementById("completionValue");

    state.completion = score;

    if (completionValue) {

        completionValue.textContent = score + "%";

    }

}

/* ==========================================
   HELPERS
========================================== */

function markCompleted(id) {

    const item = document.getElementById(id);

    if (!item) return;

    item.classList.add("completed");

}

function markIncomplete(id) {

    const item = document.getElementById(id);

    if (!item) return;

    item.classList.remove("completed");

}