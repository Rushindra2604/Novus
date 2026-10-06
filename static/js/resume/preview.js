/* ==========================================
   NOVUS LIVE PREVIEW
========================================== */

function updatePreview(state) {
    const personal = state.personal || {};

    setText("previewName", personal.fullName || "Your Name");
    setText("previewHeadline", personal.headline || "Professional Headline");
    setText("previewEmail", personal.email || "email@example.com");
    setText("previewPhone", personal.phone || "+91 XXXXX XXXXX");
    setText("previewLocation", personal.location || "Location");

    const summary = document.getElementById("previewSummary");
    if (summary) {
        const value = String(state.summary || "").trim();
        summary.textContent = value || "Your professional summary will appear here as you type.";
        summary.classList.toggle("empty-preview", !value);
    }

    setLink("previewLinkedin", personal.linkedin);
    setLink("previewGithub", personal.github);
    setLink("previewPortfolio", personal.portfolio);

    renderEducationPreview(state.education || []);
    renderSkillsPreview(state.skills || {});
    renderProjectsPreview(state.projects || []);
    renderExperiencePreview(state.experience || []);
    renderCertificationPreview(state.certifications || []);

    if (typeof SectionManager !== "undefined") {
        (state.additionalSections || []).forEach(item => {
            SectionManager.renderAdditionalPreview(item.id);
            SectionManager.updateAdditionalPreview(item.id);
        });
        SectionManager.applyPreviewOrder();
        SectionManager.applyVisibility();
    }
}

function setText(id, value) {
    const element = document.getElementById(id);
    if (element) element.textContent = value;
}

function setLink(id, value) {
    const element = document.getElementById(id);
    if (!element) return;
    element.href = value || "#";
}

function renderEducationPreview(educationList) {
    const container = document.getElementById("previewEducation");
    if (!container) return;

    if (!educationList.length) {
        container.innerHTML = '<div class="empty-preview">Education information will appear here.</div>';
        return;
    }

    container.innerHTML = educationList.map(education => `
        <div class="preview-education-item">
            <div class="preview-education-header">
                <h4>${escapeHTML(education.degree || "Degree")}</h4>
                <span class="preview-years">${escapeHTML(formatYears(education.startYear, education.endYear))}</span>
            </div>
            <p class="preview-institution">${escapeHTML(education.institution || "")}</p>
            ${education.score ? `<p class="preview-score">CGPA: ${escapeHTML(education.score)}</p>` : ""}
        </div>
    `).join("");
}

function formatYears(start, end) {
    if (start && end) return `${start} - ${end}`;
    return start || end || "";
}

function renderSkillsPreview(skills) {
    const container = document.getElementById("previewSkills");
    if (!container) return;

    const categories = [
        ["Programming Languages", skills.languages],
        ["Frameworks & Libraries", skills.frameworks],
        ["Databases", skills.databases],
        ["Tools & Platforms", skills.tools],
        ["Other Skills", skills.others]
    ];

    const rows = categories
        .filter(([, data]) => Array.isArray(data) && data.length)
        .map(([title, data]) => `
            <p class="preview-skill-line">
                <strong>${escapeHTML(title)} :</strong> ${data.map(escapeHTML).join(" • ")}
            </p>
        `);

    container.innerHTML = rows.length
        ? rows.join("")
        : '<div class="empty-preview">Skills will appear here.</div>';
}

function renderProjectsPreview(projects) {
    const container = document.getElementById("previewProjects");
    if (!container) return;

    const valid = projects.filter(project =>
        project.title ||
        (project.technologies || []).length ||
        (project.bullets || []).some(Boolean) ||
        project.github ||
        project.liveDemo
    );

    container.innerHTML = valid.map(project => `
        <div class="preview-project">
            ${project.title ? `<h4 class="preview-project-title">${escapeHTML(project.title)}</h4>` : ""}
            ${(project.technologies || []).length ? `<p class="preview-project-tech"><strong>Tech Stack :</strong> ${project.technologies.map(escapeHTML).join(" • ")}</p>` : ""}
            ${(project.bullets || []).some(Boolean) ? `
                <ul class="preview-project-bullets">
                    ${(project.bullets || []).filter(Boolean).map(bullet => `<li>${escapeHTML(bullet)}</li>`).join("")}
                </ul>
            ` : ""}
            ${(project.github || project.liveDemo) ? `
                <div class="preview-project-links">
                    ${project.github ? `<a href="${safeUrl(project.github)}" target="_blank" rel="noopener">🔗 GitHub</a>` : ""}
                    ${project.liveDemo ? `<a href="${safeUrl(project.liveDemo)}" target="_blank" rel="noopener">🌐 Live Demo</a>` : ""}
                </div>
            ` : ""}
        </div>
    `).join("");
}

function renderExperiencePreview(experience) {
    const section = document.getElementById("previewExperienceSection");
    const container = document.getElementById("previewExperience");
    if (!section || !container) return;

    const valid = experience.filter(item =>
        item.jobTitle || item.company || (item.responsibilities || []).some(Boolean)
    );

    section.classList.toggle("hidden", valid.length === 0);

    container.innerHTML = valid.map(item => `
        <div class="preview-experience-item">
            <div class="preview-experience-header">
                <strong>${escapeHTML(item.jobTitle || "")}${item.jobTitle && item.company ? " — " : ""}${escapeHTML(item.company || "")}</strong>
            </div>
            ${formatExperienceDate(item) ? `<div class="preview-experience-meta">${escapeHTML(formatExperienceDate(item))}</div>` : ""}
            ${(item.responsibilities || []).some(Boolean) ? `
                <ul class="preview-experience-bullets">
                    ${(item.responsibilities || []).filter(Boolean).map(value => `<li>${escapeHTML(value)}</li>`).join("")}
                </ul>
            ` : ""}
        </div>
    `).join("");
}

function formatExperienceDate(experience) {
    const location = experience.location || "";
    const start = [experience.startMonth, experience.startYear].filter(Boolean).join(" ");
    const end = experience.currentlyWorking
        ? "Present"
        : [experience.endMonth, experience.endYear].filter(Boolean).join(" ");
    const date = start && end ? `${start} – ${end}` : start || end;
    return location && date ? `${location} | ${date}` : location || date;
}

function renderCertificationPreview(certifications) {

    const section = document.getElementById(
        "previewCertificationsSection"
    );

    const container = document.getElementById(
        "previewCertifications"
    );

    if (!section || !container) return;

    const valid = certifications.filter(
        item => item.name || item.organization
    );

    section.classList.toggle(
        "hidden",
        valid.length === 0
    );

    container.innerHTML = valid.map(item => {

        let title = "";

        if (item.name && item.organization) {

            title =
                `${escapeHTML(item.name)} - ${escapeHTML(item.organization)}`;

        }

        else {

            title =
                escapeHTML(
                    item.name ||
                    item.organization ||
                    "Certification"
                );

        }

        return `
            <div class="preview-certification">
                <div class="preview-certification-title">
                    ${title}
                </div>

                ${
                    item.credentialUrl
                    ? `
                        <a
                            class="preview-certification-link"
                            href="${safeUrl(item.credentialUrl)}"
                            target="_blank"
                            rel="noopener">
                            View Credential
                        </a>
                    `
                    : ""
                }
            </div>
        `;

    }).join("");
}

function safeUrl(value) {
    const url = String(value || "").trim();
    if (/^https?:\/\//i.test(url)) return escapeAttr(url);
    return "#";
}

function escapeHTML(value) {
    return String(value ?? "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

function escapeAttr(value) {
    return escapeHTML(value).replace(/`/g, "&#096;");
}
