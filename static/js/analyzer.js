/* ==========================================================
   NOVUS ATS ANALYZER
========================================================== */

/* ==========================================================
   ATS ANALYSIS PERSISTENCE
   Database-backed history.

   Important:
   - Do not use localStorage for ATS analysis snapshots.
   - The backend creates one immutable history row per analysis.
   - This file only restores/render results; the backend remains
     the source of truth for saved analyses.
========================================================== */

window.novusATSAnalysisId = null;

async function fetchATSAnalysisById(analysisId) {
    if (!analysisId) return null;

    const response = await fetch(
        `/api/analyzer/analysis/${encodeURIComponent(analysisId)}`
    );

    const data = await response.json().catch(() => ({}));

    if (!response.ok || !data.success) {
        throw new Error(
            data.message ||
            "Unable to restore this ATS analysis."
        );
    }

    return data.analysis
        ? { ...data, analysis: data.analysis }
        : null;
}

function setATSJobDescription(value) {
    const jobDescription = document.getElementById("jobDescription");
    if (!jobDescription) return;

    jobDescription.value = value || "";
    jobDescription.dispatchEvent(new Event("input"));
}

function setATSAnalyzerMode(showReport) {
    const setup = document.getElementById("analyzerSetupState");
    const report = document.getElementById("atsReport");

    if (setup) {
        setup.hidden = Boolean(showReport);
    }

    if (report) {
        report.hidden = !showReport;

        if (!showReport) {
            report.classList.remove("ats-report-visible");
            report.innerHTML = "";
        }
    }
}

function resetATSAnalyzerState({ clearJobDescription = false } = {}) {
    window.novusATSAnalysis = null;
    window.novusATSAnalysisId = null;

    if (clearJobDescription) {
        const jobDescription = document.getElementById("jobDescription");
        if (jobDescription) {
            jobDescription.value = "";
            jobDescription.dispatchEvent(new Event("input"));
        }
    }

    const url = new URL(window.location.href);
    url.searchParams.delete("analysis_id");
    window.history.replaceState({}, "", url);

    setATSAnalyzerMode(false);
}

function getATSAnalysisIdFromURL() {
    try {
        return new URLSearchParams(window.location.search).get("analysis_id");
    } catch (error) {
        return null;
    }
}

async function restoreATSAnalysis(resumeId, analysisId = null) {
    if (!analysisId) {
        setATSAnalyzerMode(false);
        return false;
    }

    try {
        const saved = await fetchATSAnalysisById(analysisId);

        if (!saved?.analysis) {
            resetATSAnalyzerState();
            return false;
        }

        const savedResumeId = saved.resume_id;

        // Restore the exact resume selection represented by this saved run.
        const resumeSelect = document.getElementById("resumeSelect");
        if (resumeSelect && savedResumeId) {
            const option = Array.from(resumeSelect.options).find(
                candidate => String(candidate.value) === String(savedResumeId)
            );

            if (option) {
                resumeSelect.value = String(savedResumeId);
            }
        }

        // When an analysis_id is present, the saved analysis is the
        // source of truth for which resume belongs to this history entry.
        // Do not compare it with the page's initial/default selection,
        // because the selector may initially point to a different resume.
        // The selector has already been restored above.
        if (
            resumeSelect &&
            savedResumeId &&
            String(resumeSelect.value) !== String(savedResumeId)
        ) {
            console.warn(
                "Saved ATS analysis resume is not available in the selector."
            );
        }

        window.novusATSAnalysisId = saved.analysis_id || null;
        setATSJobDescription(saved.job_description || "");

        window.novusATSAnalysis = saved.analysis;
        renderATSReport(saved.analysis, false);

        return true;
    } catch (error) {
        console.warn("Unable to restore ATS analysis.", error);
        resetATSAnalyzerState();
        return false;
    }
}

document.addEventListener("DOMContentLoaded", () => {

    const resumeSelect =
        document.getElementById("resumeSelect");

    const jobDescription =
        document.getElementById("jobDescription");

    const characterCount =
        document.getElementById("jobDescriptionCount");

    const analyzeButton =
        document.getElementById("analyzeResumeBtn");


    /* ------------------------------------------------------
       Character count
    ------------------------------------------------------ */

    if (jobDescription && characterCount) {

        const updateCharacterCount = () => {

            characterCount.textContent =
                jobDescription.value.length;

        };

        jobDescription.addEventListener(
            "input",
            updateCharacterCount
        );

        updateCharacterCount();
    }


    /* ------------------------------------------------------
       Exact history restore
    ------------------------------------------------------ */

    if (resumeSelect) {
        const analysisId = getATSAnalysisIdFromURL();

        if (analysisId) {
            restoreATSAnalysis(null, analysisId);
        }

        resumeSelect.addEventListener("change", () => {
            resetATSAnalyzerState();
        });
    }


    /* ------------------------------------------------------
       Analyze Resume
    ------------------------------------------------------ */

    if (!analyzeButton) {
        return;
    }


    analyzeButton.addEventListener("click", async () => {

        const resumeId =
            resumeSelect?.value || "";

        const jd =
            jobDescription?.value.trim() || "";


        /* ----------------------------------------------
           Validation
        ---------------------------------------------- */

        if (!resumeId) {

            alert(
                "Please select a resume before analyzing."
            );

            return;
        }


        if (!jd) {

            alert(
                "Please paste a job description before analyzing."
            );

            return;
        }


        /* ----------------------------------------------
           Loading state
        ---------------------------------------------- */

        const originalButtonHTML =
            analyzeButton.innerHTML;

        analyzeButton.disabled = true;

        analyzeButton.innerHTML = `
            <i data-lucide="loader-circle"></i>
            Analyzing...
        `;


        if (window.lucide) {
            lucide.createIcons();
        }


        try {

            /* ------------------------------------------
               Call ATS backend
            ------------------------------------------ */

            const response = await fetch(
                "/api/analyzer/analyze",
                {
                    method: "POST",

                    headers: {
                        "Content-Type": "application/json"
                    },

                    body: JSON.stringify({
                        resume_id: resumeId,
                        job_description: jd
                    })
                }
            );


            const data =
                await response.json();


            /* ------------------------------------------
               Handle backend error
            ------------------------------------------ */

            if (!response.ok || !data.success) {

                throw new Error(
                    data.message ||
                    "ATS analysis failed."
                );

            }


            /* ------------------------------------------
               Store result for next UI step
            ------------------------------------------ */

            window.novusATSAnalysis =
                data.analysis;

            // The backend persists every analysis as a history snapshot.
            // Keep the returned ID so Insights/exact history reopening can
            // point back to this specific analysis.
            window.novusATSAnalysisId =
                data.analysis_id || null;

            if (window.novusATSAnalysisId) {
                const url = new URL(window.location.href);
                url.searchParams.set("analysis_id", window.novusATSAnalysisId);
                window.history.replaceState({}, "", url);
            }

            renderATSReport(data.analysis);




        } catch (error) {

            console.error(
                "ATS analysis error:",
                error
            );


            alert(
                error.message ||
                "Something went wrong while analyzing your resume."
            );


        } finally {

            analyzeButton.disabled = false;

            analyzeButton.innerHTML =
                originalButtonHTML;

            if (window.lucide) {
                lucide.createIcons();
            }

        }

    });

});

/* =========================================================
   NOVUS ATS REPORT
========================================================= */

function escapeATSHTML(value) {
    if (value === null || value === undefined) return "";

    return String(value)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}


function getATSScoreClass(score) {
    if (score >= 85) return "excellent";
    if (score >= 70) return "strong";
    if (score >= 55) return "moderate";
    if (score >= 40) return "needs-improvement";
    return "weak";
}


function getATSPriorityClass(priority) {
    return String(priority || "")
        .toLowerCase()
        .replace(/\s+/g, "-");
}


function formatATSLabel(value) {
    if (!value) return "";

    return String(value)
        .replace(/_/g, " ")
        .replace(/\b\w/g, char => char.toUpperCase());
}


/* =========================================================
   NOVUS PREMIUM ATS SHELL
   Visual shell only. It does not change ATS calculations or
   Resume Studio functionality.
========================================================= */
/* =========================================================
   SCORE BREAKDOWN
========================================================= */

function renderATSScoreBreakdown(scoreData) {
    const componentScores = scoreData?.component_scores || {};
    const weights = scoreData?.weights || {};

    const labels = {
        required_skills: "Required Skills",
        technical_keywords: "Technical Keywords",
        practical_experience: "Practical Experience",
        responsibilities: "Responsibilities",
        parseability: "Formatting & Parseability",
        education: "Education",
        preferred_skills: "Preferred Skills"
    };

    return Object.keys(labels).map(key => {
        const score = componentScores[key];
        const weight = weights[key];

        const isAvailable =
            typeof score === "number" &&
            !Number.isNaN(score);

        const displayScore = isAvailable
            ? `${Math.round(score)}%`
            : "Not evaluated";

        const width = isAvailable
            ? Math.max(0, Math.min(100, score))
            : 0;

        return `
            <div class="ats-score-row">

                <div class="ats-score-row-top">

                    <div class="ats-score-label">
                        <span>
                            ${escapeATSHTML(labels[key])}
                        </span>

                        <small>
                            ${weight ? `${escapeATSHTML(weight)}% weight` : ""}
                        </small>
                    </div>

                    <strong>
                        ${escapeATSHTML(displayScore)}
                    </strong>

                </div>

                <div class="ats-progress">
                    <div
                        class="ats-progress-fill"
                        style="width: ${width}%"
                    ></div>
                </div>

            </div>
        `;
    }).join("");
}


/* =========================================================
   RESUME GAP PLAN
========================================================= */

function getATSGapPriorityRank(priority) {
    const ranks = {
        critical: 3,
        high: 2,
        medium: 1
    };

    return ranks[String(priority || "medium").toLowerCase()] || 1;
}


function normalizeATSGapText(value) {
    return String(value || "")
        .toLowerCase()
        .replace(/[.\-_/]+/g, " ")
        .replace(/\s+/g, " ")
        .trim();
}


function getATSGapCategoryKey(category) {
    const value = normalizeATSGapText(category).replace(/ /g, "_");

    if (
        value.includes("required_skill") ||
        value === "required_skills"
    ) {
        return "required_skill";
    }

    if (
        value.includes("preferred_skill") ||
        value === "preferred_skills"
    ) {
        return "preferred_skill";
    }

    if (
        value.includes("technical_keyword") ||
        value === "technical_keywords"
    ) {
        return "technical_keyword";
    }

    if (value.includes("responsibil")) {
        return "responsibility";
    }

    if (value.includes("experience")) {
        return "experience";
    }

    if (value.includes("education")) {
        return "education";
    }

    return value;
}


function buildATSGapModel(gaps) {
    const model = {
        critical: [],
        skills: [],
        content: [],
        optional: []
    };

    if (!Array.isArray(gaps)) {
        return model;
    }

    const deduped = new Map();

    gaps.forEach(gap => {
        if (!gap || typeof gap !== "object") return;

        const item = String(
            gap.item ||
            gap.requirement ||
            gap.text ||
            ""
        ).trim();

        if (!item) return;

        const priority = String(
            gap.priority || "medium"
        ).toLowerCase();

        const categoryKey = getATSGapCategoryKey(gap.category);
        const normalizedItem = normalizeATSGapText(item);

        /*
         * A concept can be emitted by more than one matcher category
         * (for example REST API as both a required skill and a technical
         * keyword). Keep one user-facing card and retain the strongest
         * classification internally.
         */
        const existing = deduped.get(normalizedItem);

        if (
            !existing ||
            getATSGapPriorityRank(priority) >
            getATSGapPriorityRank(existing.priority)
        ) {
            deduped.set(normalizedItem, {
                ...gap,
                item,
                priority,
                categoryKey
            });
        }
    });

    Array.from(deduped.values()).forEach(gap => {
        const { priority, categoryKey } = gap;

        if (categoryKey === "preferred_skill") {
            model.optional.push(gap);
            return;
        }

        if (
            priority === "critical" ||
            categoryKey === "experience" ||
            categoryKey === "education"
        ) {
            model.critical.push(gap);
            return;
        }

        if (
            categoryKey === "required_skill" ||
            categoryKey === "technical_keyword"
        ) {
            model.skills.push(gap);
            return;
        }

        model.content.push(gap);
    });

    const sortGaps = list => list.sort((a, b) => {
        const priorityDifference =
            getATSGapPriorityRank(b.priority) -
            getATSGapPriorityRank(a.priority);

        if (priorityDifference !== 0) {
            return priorityDifference;
        }

        return String(a.item).localeCompare(String(b.item));
    });

    Object.values(model).forEach(sortGaps);

    return model;
}


function hasResumeValue(value) {
    if (typeof value === "string") {
        return value.trim().length > 0;
    }

    if (Array.isArray(value)) {
        return value.length > 0;
    }

    if (value && typeof value === "object") {
        return Object.values(value).some(hasResumeValue);
    }

    return Boolean(value);
}


function getATSResumeCompleteness(resume) {
    const safeResume = resume || {};
    const sections = [
        {
            key: "personal",
            label: "Personal Information",
            icon: "user-round",
            description: "Add your name and contact details.",
            action: "Complete your contact information."
        },
        {
            key: "summary",
            label: "Professional Summary",
            icon: "file-text",
            description: "No professional summary was found.",
            action: "Add a concise 2–3 line summary focused on your background and target role."
        },
        {
            key: "education",
            label: "Education",
            icon: "graduation-cap",
            description: "No education details were found.",
            action: "Add your degree, institution and relevant education details."
        },
        {
            key: "skills",
            label: "Skills",
            icon: "wrench",
            description: "No skills were found.",
            action: "Add the technical skills you genuinely have experience with."
        },
        {
            key: "projects",
            label: "Projects",
            icon: "folder",
            description: "No projects were found.",
            action: "Add relevant projects that demonstrate your practical work."
        }
    ];

    const results = sections.map(section => ({
        ...section,
        complete: hasResumeValue(safeResume[section.key])
    }));

    const completeCount = results.filter(item => item.complete).length;

    return {
        sections: results,
        completeCount,
        totalCount: results.length
    };
}


function renderATSGapItem(gap, compact = false) {
    const priority = String(gap.priority || "medium").toLowerCase();
    const categoryKey = gap.categoryKey || getATSGapCategoryKey(gap.category);
    const item = gap.item || gap.requirement || gap.text || "Requirement";

    let title = item;
    let description = gap.reason || "";
    let action = "";

    if (categoryKey === "experience") {
        title = "Relevant Experience";
        action = "Review your Experience or Projects section for genuine evidence that supports this requirement.";
    } else if (categoryKey === "education") {
        title = "Education Requirement";
        action = "Verify that your Education section clearly shows the qualification requested by the employer.";
    } else if (categoryKey === "responsibility") {
        title = "Responsibility Evidence";
        action = "If you have done this work, strengthen the relevant project or experience bullet with clear evidence.";
    } else if (categoryKey === "required_skill") {
        title = item;
        action = "If you genuinely have this skill, make sure it is visible in your Skills or Projects section.";
    } else if (categoryKey === "technical_keyword") {
        title = item;
        action = "If this technology is genuinely part of your experience, make the relevant evidence easier to find.";
    } else if (categoryKey === "preferred_skill") {
        title = item;
        action = "Optional: add this only if you genuinely have relevant experience with it.";
    }

    if (!description) {
        description =
            categoryKey === "preferred_skill"
                ? "Preferred by the employer but not identified in your resume."
                : "This requirement was not sufficiently supported by your resume content.";
    }

    return `
        <article class="novus-gap-item ${escapeATSHTML(priority)} ${compact ? "is-compact" : ""}">
            <div class="novus-gap-item-icon">
                <i data-lucide="${categoryKey === "experience"
            ? "briefcase-business"
            : categoryKey === "education"
                ? "graduation-cap"
                : categoryKey === "responsibility"
                    ? "list-checks"
                    : categoryKey === "preferred_skill"
                        ? "star"
                        : "circle-alert"
        }"></i>
            </div>

            <div class="novus-gap-item-body">
                <div class="novus-gap-item-meta">
                    <span class="novus-gap-priority">
                        ${escapeATSHTML(formatATSLabel(priority))}
                    </span>
                    ${gap.category
            ? `<span class="novus-gap-source">${escapeATSHTML(formatATSLabel(gap.category))}</span>`
            : ""
        }
                </div>

                <h4>${escapeATSHTML(title)}</h4>
                <p>${escapeATSHTML(description)}</p>

                ${action
            ? `<div class="novus-gap-action"><i data-lucide="arrow-right"></i><span>${escapeATSHTML(action)}</span></div>`
            : ""
        }
            </div>
        </article>
    `;
}


function renderATSGapGroup(title, eyebrow, description, gaps, type, icon) {
    if (!gaps.length) return "";

    const itemCount = gaps.length;
    const groupClass = `novus-gap-group ${type}`;

    if (type === "skills" || type === "optional") {
        const pills = gaps.map(gap => `
            <span class="novus-gap-pill">
                <span class="novus-gap-pill-dot"></span>
                ${escapeATSHTML(gap.item)}
            </span>
        `).join("");

        return `
            <section class="${groupClass}">
                <div class="novus-gap-group-header">
                    <div class="novus-gap-group-heading">
                        <div class="novus-gap-group-icon">
                            <i data-lucide="${icon}"></i>
                        </div>
                        <div>
                            <span class="novus-gap-eyebrow">${escapeATSHTML(eyebrow)}</span>
                            <h3>${escapeATSHTML(title)}</h3>
                            <p>${escapeATSHTML(description)}</p>
                        </div>
                    </div>
                    <span class="novus-gap-count">${itemCount} ${itemCount === 1 ? "item" : "items"}</span>
                </div>
                <div class="novus-gap-pill-list">${pills}</div>
                <p class="novus-gap-group-note">
                    ${type === "optional"
                ? "These are optional enhancements. Add them only when they genuinely reflect your experience."
                : "If you genuinely have experience with these, make them visible in your Skills or Projects section."
            }
                </p>
            </section>
        `;
    }

    return `
        <section class="${groupClass}">
            <div class="novus-gap-group-header">
                <div class="novus-gap-group-heading">
                    <div class="novus-gap-group-icon">
                        <i data-lucide="${icon}"></i>
                    </div>
                    <div>
                        <span class="novus-gap-eyebrow">${escapeATSHTML(eyebrow)}</span>
                        <h3>${escapeATSHTML(title)}</h3>
                        <p>${escapeATSHTML(description)}</p>
                    </div>
                </div>
                <span class="novus-gap-count">${itemCount} ${itemCount === 1 ? "item" : "items"}</span>
            </div>

            <div class="novus-gap-card-grid">
                ${gaps.map(gap => renderATSGapItem(gap)).join("")}
            </div>
        </section>
    `;
}


function renderATSResumeCompleteness(resume) {
    const completeness = getATSResumeCompleteness(resume);
    const missing = completeness.sections.filter(section => !section.complete);
    const percent = completeness.totalCount
        ? Math.round((completeness.completeCount / completeness.totalCount) * 100)
        : 0;

    if (!missing.length) {
        return `
            <div class="novus-completeness-card complete">
                <div class="novus-completeness-status-icon">
                    <i data-lucide="check-circle-2"></i>
                </div>
                <div class="novus-completeness-copy">
                    <div class="novus-completeness-title-row">
                        <strong>Core resume sections are complete</strong>
                        <span>${completeness.completeCount}/${completeness.totalCount}</span>
                    </div>
                    <div class="novus-completeness-progress">
                        <span style="width:${percent}%"></span>
                    </div>
                    <p>Novus found content in all five core resume sections.</p>
                </div>
            </div>
        `;
    }

    return `
        <div class="novus-completeness-summary">
            <div class="novus-completeness-summary-main">
                <span class="novus-gap-eyebrow">Resume completeness</span>
                <h3>${completeness.completeCount} of ${completeness.totalCount} core sections complete</h3>
                <p>Complete the missing sections so recruiters can understand your profile more clearly.</p>
            </div>
            <div class="novus-completeness-score">
                <strong>${percent}%</strong>
                <span>complete</span>
            </div>
        </div>

        <div class="novus-completeness-progress">
            <span style="width:${percent}%"></span>
        </div>

        <div class="novus-completeness-grid">
            ${missing.map(section => `
                <article class="novus-completeness-item">
                    <div class="novus-completeness-item-icon">
                        <i data-lucide="${section.icon}"></i>
                    </div>
                    <div class="novus-completeness-item-copy">
                        <div class="novus-completeness-item-title">
                            <h4>${escapeATSHTML(section.label)}</h4>
                            <span>Missing</span>
                        </div>
                        <p>${escapeATSHTML(section.description)}</p>
                        <span class="novus-completeness-action">${escapeATSHTML(section.action)}</span>
                    </div>
                </article>
            `).join("")}
        </div>
    `;
}

function renderATSGaps(analysis) {
    const gaps = Array.isArray(analysis)
        ? analysis
        : analysis?.gaps?.gaps || [];

    const model = buildATSGapModel(gaps);

    if (
        !model.critical.length &&
        !model.skills.length &&
        !model.content.length &&
        !model.optional.length
    ) {
        return `
            <div class="novus-gap-success">
                <div class="novus-gap-success-icon">
                    <i data-lucide="check-circle-2"></i>
                </div>
                <div>
                    <span class="novus-gap-eyebrow">All clear</span>
                    <h3>No major improvement gaps detected</h3>
                    <p>Your resume covers the detected job requirements. Review Resume Completeness separately for any missing core sections.</p>
                </div>
            </div>
        `;
    }

    return `
        <div class="novus-gap-plan-intro">
            <div>
                <span class="ats-section-eyebrow">Resume Improvement Plan</span>
                <h3>Focus on the changes that matter most</h3>
                <p>Novus groups related issues so you can see what is missing, why it matters, and what you can do next.</p>
            </div>

            <div class="novus-gap-plan-stats">
                ${model.critical.length ? `<span class="critical">${model.critical.length} Critical</span>` : ""}
                ${model.skills.length ? `<span class="skills">${model.skills.length} Skills</span>` : ""}
                ${model.content.length ? `<span class="content">${model.content.length} Content</span>` : ""}
                ${model.optional.length ? `<span class="optional">${model.optional.length} Optional</span>` : ""}
            </div>
        </div>

        ${renderATSGapGroup(
            "Critical Requirements",
            "Priority 01",
            "Requirements with the greatest potential impact on your job match.",
            model.critical,
            "critical",
            "circle-alert"
        )}

        ${renderATSGapGroup(
            "Skills & Keywords",
            "Priority 02",
            "Relevant terms that are not currently supported by your resume.",
            model.skills,
            "skills",
            "settings-2"
        )}

        ${model.content.length
            ? renderATSGapGroup(
                "Resume Content",
                "Priority 03",
                "Evidence or resume content that could better support the target role.",
                model.content,
                "content",
                "file-text"
            )
            : ""
        }

        ${renderATSGapGroup(
            "Optional Enhancements",
            "Priority 04",
            "Preferred skills that can strengthen alignment but are not mandatory.",
            model.optional,
            "optional",
            "star"
        )}

        <div class="novus-gap-footer">
            <i data-lucide="info"></i>
            <span>Missing a skill does not mean you should add it. Only include technologies, experience and qualifications you can genuinely support.</span>
        </div>
    `;
}

/* =========================================================
   AI ANALYSIS
========================================================= */

function renderATSAnalysis(aiAnalysis) {
    if (!aiAnalysis) return "";

    const strengths = Array.isArray(aiAnalysis.strengths)
        ? aiAnalysis.strengths.filter(Boolean)
        : [];

    const criticalIssues = Array.isArray(aiAnalysis.critical_issues)
        ? aiAnalysis.critical_issues.filter(Boolean)
        : [];

    const priorities = Array.isArray(aiAnalysis.improvement_priorities)
        ? aiAnalysis.improvement_priorities.filter(Boolean)
        : [];

    return `
        <section class="ats-ai-section novus-ai-detail-section">
            <div class="novus-ai-detail-heading">
                <div>
                    <span class="ats-section-eyebrow">Gemini AI</span>
                    <h2>AI-Powered Insights</h2>
                    <p>Evidence-based observations from your resume and the target job.</p>
                </div>
            </div>

            ${aiAnalysis.overall_assessment ? `
                <div class="novus-ai-assessment">
                    <div class="novus-ai-assessment-icon">
                        <i data-lucide="sparkles"></i>
                    </div>
                    <div>
                        <span class="novus-ai-mini-label">Overall Assessment</span>
                        <p>${escapeATSHTML(aiAnalysis.overall_assessment)}</p>
                    </div>
                </div>
            ` : ""}

            <div class="novus-ai-insight-grid">
                <article class="novus-ai-insight-box strength">
                    <div class="novus-ai-insight-box-head">
                        <span class="novus-ai-insight-box-icon"><i data-lucide="check"></i></span>
                        <h3>Strengths</h3>
                        <span>${strengths.length}</span>
                    </div>
                    ${strengths.length
                        ? `<ul>${strengths.map(item => `<li>${escapeATSHTML(item)}</li>`).join("")}</ul>`
                        : `<p class="novus-ai-empty-note">No strengths were returned for this analysis.</p>`
                    }
                </article>

                <article class="novus-ai-insight-box issue">
                    <div class="novus-ai-insight-box-head">
                        <span class="novus-ai-insight-box-icon"><i data-lucide="circle-alert"></i></span>
                        <h3>Critical Issues</h3>
                        <span>${criticalIssues.length}</span>
                    </div>
                    ${criticalIssues.length
                        ? `<ul>${criticalIssues.map(item => `<li>${escapeATSHTML(item)}</li>`).join("")}</ul>`
                        : `<p class="novus-ai-empty-note">No critical issues were identified.</p>`
                    }
                </article>
            </div>

            ${priorities.length ? `
                <div class="novus-ai-priorities">
                    <div class="novus-ai-priorities-head">
                        <h3>Improvement Priorities</h3>
                        <span>Evidence-based recommendations</span>
                    </div>

                    <div class="novus-ai-priority-list">
                        ${priorities.map((item, index) => `
                            <article class="novus-ai-priority-row">
                                <span class="novus-ai-priority-number">${String(item.priority || index + 1).padStart(2, "0")}</span>
                                <div>
                                    <span class="novus-ai-priority-area">${escapeATSHTML(item.area || "Improvement")}</span>
                                    <h4>${escapeATSHTML(item.issue || "")}</h4>
                                    <p>${escapeATSHTML(item.recommendation || "")}</p>
                                </div>
                            </article>
                        `).join("")}
                    </div>
                </div>
            ` : ""}
        </section>
    `;
}

/* =========================================================
   AI RESUME IMPROVEMENTS
========================================================= */

window.novusATSRewriteItems = [];
window.novusATSCurrentRewrite = null;


function getResumeItemTitle(item, fallback) {
    if (!item || typeof item !== "object") {
        return fallback;
    }

    return (
        item.title ||
        item.name ||
        item.project_name ||
        item.projectName ||
        item.role ||
        item.position ||
        fallback
    );
}


function getResumeItemBullets(item) {
    if (!item || typeof item !== "object") {
        return [];
    }

    const possibleKeys = [
        "bullets",
        "bullet_points",
        "bulletPoints",
        "descriptions"
    ];

    for (const key of possibleKeys) {
        if (Array.isArray(item[key])) {
            return item[key]
                .filter(value =>
                    typeof value === "string" &&
                    value.trim()
                )
                .map(value => value.trim());
        }
    }

    if (
        typeof item.description === "string" &&
        item.description.trim()
    ) {
        return [item.description.trim()];
    }

    return [];
}


function buildATSRewriteItems(analysis) {
    const resume = analysis?.resume || {};
    const items = [];

    /* ---------------------------------------------------------
       Professional Summary
    --------------------------------------------------------- */

    if (
        typeof resume.summary === "string" &&
        resume.summary.trim()
    ) {
        items.push({
            id: "summary",
            contentType: "summary",
            sectionType: "summary",
            sectionIndex: -1,
            bulletIndex: -1,
            group: "Professional Summary",
            groupIcon: "file-text",
            label: "Professional Summary",
            content: resume.summary.trim()
        });
    }

    /* ---------------------------------------------------------
       Projects
    --------------------------------------------------------- */

    const projects = Array.isArray(resume.projects)
        ? resume.projects
        : [];

    projects.forEach((project, projectIndex) => {
        const projectTitle = getResumeItemTitle(
            project,
            `Project ${projectIndex + 1}`
        );

        const bullets = getResumeItemBullets(project);

        bullets.forEach((bullet, bulletIndex) => {
            items.push({
                id: `project-${projectIndex}-${bulletIndex}`,
                contentType: "bullet",
                sectionType: "projects",
                sectionIndex: projectIndex,
                bulletIndex,
                group: "Projects",
                groupItem: projectTitle,
                groupIcon: "folder",
                label: `Bullet ${bulletIndex + 1}`,
                content: bullet
            });
        });
    });

    /* ---------------------------------------------------------
       Experience
    --------------------------------------------------------- */

    const experience = Array.isArray(resume.experience)
        ? resume.experience
        : [];

    experience.forEach((entry, experienceIndex) => {
        const experienceTitle = getResumeItemTitle(
            entry,
            `Experience ${experienceIndex + 1}`
        );

        const bullets = getResumeItemBullets(entry);

        bullets.forEach((bullet, bulletIndex) => {
            items.push({
                id: `experience-${experienceIndex}-${bulletIndex}`,
                contentType: "bullet",
                sectionType: "experience",
                sectionIndex: experienceIndex,
                bulletIndex,
                group: "Experience",
                groupItem: experienceTitle,
                groupIcon: "briefcase",
                label: `Bullet ${bulletIndex + 1}`,
                content: bullet
            });
        });
    });

    return items;
}


function renderAIImprovementItem(item, index) {
    return `
        <div class="novus-ai-item">
            <div class="novus-ai-item-content">

                <div class="novus-ai-item-meta">
                    <span class="novus-ai-item-number">
                        ${String(index + 1).padStart(2, "0")}
                    </span>

                    <div>
                        ${item.groupItem
            ? `
                                    <strong>
                                        ${escapeATSHTML(item.groupItem)}
                                    </strong>
                                `
            : ""
        }

                        <p>
                            ${escapeATSHTML(
            item.content
        )}
                        </p>
                    </div>
                </div>

                <button
                    type="button"
                    class="novus-ai-view-btn"
                    data-ai-item-index="${index}"
                >
                    <i data-lucide="sparkles"></i>
                    <span>View</span>
                </button>

            </div>
        </div>
    `;
}


function renderAIImprovementGroup(
    title,
    icon,
    items,
    groupName
) {
    if (!items.length) {
        return `
            <div class="novus-ai-group novus-ai-group-empty">

                <div class="novus-ai-group-header">
                    <div class="novus-ai-group-title">
                        <span class="novus-ai-group-icon">
                            <i data-lucide="${icon}"></i>
                        </span>

                        <strong>
                            ${escapeATSHTML(title)}
                        </strong>
                    </div>

                    <span class="novus-ai-count">
                        0
                    </span>
                </div>

                <p class="novus-ai-empty">
                    No editable content found.
                </p>

            </div>
        `;
    }

    return `
        <div
            class="novus-ai-group"
            data-ai-group="${escapeATSHTML(groupName)}"
        >

            <button
                type="button"
                class="novus-ai-group-header"
                data-ai-group-toggle
            >
                <div class="novus-ai-group-title">

                    <span class="novus-ai-group-icon">
                        <i data-lucide="${icon}"></i>
                    </span>

                    <strong>
                        ${escapeATSHTML(title)}
                    </strong>

                </div>

                <div class="novus-ai-group-right">

                    <span class="novus-ai-count">
                        ${items.length}
                        ${items.length === 1
            ? "suggestion"
            : "suggestions"
        }
                    </span>

                    <i
                        data-lucide="chevron-down"
                        class="novus-ai-chevron"
                    ></i>

                </div>
            </button>

            <div class="novus-ai-group-body">
                ${items.map(item =>
            renderAIImprovementItem(
                item,
                window.novusATSRewriteItems.indexOf(item)
            )
        ).join("")}
            </div>

        </div>
    `;
}


function renderAIImprovements(analysis) {
    const items = buildATSRewriteItems(analysis);

    window.novusATSRewriteItems = items;

    const summaryItems = items.filter(
        item => item.contentType === "summary"
    );

    const projectItems = items.filter(
        item => item.sectionType === "projects"
    );

    const experienceItems = items.filter(
        item => item.sectionType === "experience"
    );

    return `
        <section class="ats-report-section novus-ai-improvements">

            <div class="novus-ai-hero">

                <div class="novus-ai-hero-icon">
                    <i data-lucide="sparkles"></i>
                </div>

                <div class="novus-ai-hero-content">

                    <span class="ats-section-eyebrow">
                        Gemini AI
                    </span>

                    <h2>
                        AI Resume Improvements
                    </h2>

                    <p>
                        Review and apply AI-powered suggestions
                        using your existing resume content.
                        Novus does not add new experience.
                    </p>

                </div>

                <div class="novus-ai-hero-stat">

                    <strong>
                        ${items.length}
                    </strong>

                    <span>
                        ${items.length === 1
            ? "Content item"
            : "Content items"
        }
                    </span>

                </div>

            </div>


            <div class="novus-ai-workspace">

                <div class="novus-ai-library">

                    <div class="novus-ai-library-header">

                        <div>
                            <span class="ats-section-eyebrow">
                                Review
                            </span>

                            <h3>
                                Your Resume Content
                            </h3>
                        </div>

                        <span class="novus-ai-content-badge">
                            ${items.length} available
                        </span>

                    </div>


                    <div class="novus-ai-groups">

                        ${renderAIImprovementGroup(
            "Professional Summary",
            "file-text",
            summaryItems,
            "summary"
        )}

                        ${renderAIImprovementGroup(
            "Projects",
            "folder",
            projectItems,
            "projects"
        )}

                        ${renderAIImprovementGroup(
            "Experience",
            "briefcase",
            experienceItems,
            "experience"
        )}

                    </div>

                </div>


                <div
                    class="novus-ai-review"
                    id="novusAIReview"
                >

                    <div class="novus-ai-review-empty">

                        <div class="novus-ai-review-empty-icon">
                            <i data-lucide="sparkles"></i>
                        </div>

                        <h3>
                            Select content to improve
                        </h3>

                        <p>
                            Choose a summary or bullet from
                            the left. Your AI suggestion will
                            appear here for review.
                        </p>

                    </div>

                </div>

            </div>

        </section>
    `;
}


/* =========================================================
   AI IMPROVEMENT INTERACTIONS
========================================================= */

function getATSJobDescription() {
    return (
        document
            .getElementById("jobDescription")
            ?.value
            .trim() || ""
    );
}


function getATSResumeId() {
    return (
        document
            .getElementById("resumeSelect")
            ?.value || ""
    );
}


function getATSReviewContainer() {
    return document.getElementById("novusAIReview");
}


function renderATSReviewLoading(item) {
    const review = getATSReviewContainer();

    if (!review) return;

    review.innerHTML = `
        <div class="novus-ai-review-loading">

            <div class="novus-ai-loading-icon">
                <i data-lucide="sparkles"></i>
            </div>

            <h3>
                Improving your content
            </h3>

            <p>
                Gemini is refining the wording while
                preserving your original experience.
            </p>

            <div class="novus-ai-loader"></div>

        </div>
    `;

    if (window.lucide) {
        lucide.createIcons();
    }
}


function renderATSRewritePreview(content, item) {
    const safeContent = escapeATSHTML(content || "");

    if (item?.contentType === "bullet") {
        return `
            <ul class="novus-ai-bullet-preview">
                <li>${safeContent}</li>
            </ul>
        `;
    }

    return `<p>${safeContent}</p>`;
}

function renderATSReview(item) {
    const review = getATSReviewContainer();

    if (!review) return;

    const current =
        window.novusATSCurrentRewrite;

    if (!current) {
        review.innerHTML = `
            <div class="novus-ai-review-empty">
                <h3>
                    Select content to improve
                </h3>
            </div>
        `;

        return;
    }

    const rewrite = current.rewrite || {};
    const validation = current.validation || {};

    const isSafe =
        validation.is_safe === true;

    const changes =
        Array.isArray(rewrite.changes)
            ? rewrite.changes
            : [];

    const keywords =
        Array.isArray(rewrite.used_keywords)
            ? rewrite.used_keywords
            : [];

    const unsupported =
        Array.isArray(validation.unsupported_keywords)
            ? validation.unsupported_keywords
            : [];

    review.innerHTML = `
        <div class="novus-ai-review-header">

            <div>

                <span class="ats-section-eyebrow">
                    AI Suggestion
                </span>

                <h3>
                    ${escapeATSHTML(
        item.groupItem ||
        item.label
    )}
                </h3>

                ${item.groupItem
            ? `
                            <span class="novus-ai-review-subtitle">
                                ${escapeATSHTML(item.label)}
                            </span>
                        `
            : ""
        }

            </div>

            <button
                type="button"
                class="novus-ai-close-btn"
                data-ai-close-review
                aria-label="Close review"
            >
                <i data-lucide="x"></i>
            </button>

        </div>


        <div class="novus-ai-comparison">

            <div class="novus-ai-content-card original">

                <span class="novus-ai-card-label">
                    Original Content
                </span>

                ${renderATSRewritePreview(item.content, item)}

            </div>


            <div class="novus-ai-content-card improved">

                <span class="novus-ai-card-label">
                    AI Suggested Rewrite
                </span>

                ${renderATSRewritePreview(
                    rewrite.rewritten || "",
                    item
                )}

            </div>

        </div>


        ${changes.length
            ? `
                    <div class="novus-ai-changes">

                        <h4>
                            What changed
                        </h4>

                        <ul>
                            ${changes.map(change => `
                                <li>
                                    ${escapeATSHTML(change)}
                                </li>
                            `).join("")}
                        </ul>

                    </div>
                `
            : ""
        }


        ${keywords.length
            ? `
                    <div class="novus-ai-keywords">

                        <h4>
                            Relevant keywords used
                        </h4>

                        <div class="novus-ai-keyword-list">
                            ${keywords.map(keyword => `
                                <span>
                                    ${escapeATSHTML(keyword)}
                                </span>
                            `).join("")}
                        </div>

                    </div>
                `
            : ""
        }


        ${isSafe
            ? `
                    <div class="novus-ai-validation safe">

                        <i data-lucide="shield-check"></i>

                        <div>
                            <strong>
                                Validated by Novus
                            </strong>

                            <span>
                                No unsupported keywords or
                                new numerical claims detected.
                            </span>
                        </div>

                    </div>
                `
            : `
                    <div class="novus-ai-validation warning">

                        <i data-lucide="triangle-alert"></i>

                        <div>
                            <strong>
                                Review recommended
                            </strong>

                            <span>
                                Novus found wording that
                                should be reviewed before
                                applying this suggestion.
                            </span>

                            ${unsupported.length
                ? `
                                        <small>
                                            Unsupported:
                                            ${escapeATSHTML(
                    unsupported.join(", ")
                )}
                                        </small>
                                    `
                : ""
            }

                        </div>

                    </div>
                `
        }


        <div class="novus-ai-actions">

            <button
                type="button"
                class="novus-ai-primary-btn"
                data-ai-apply
            >
                <i data-lucide="check"></i>

                ${isSafe
            ? "Apply to Resume"
            : "Apply Anyway"
        }

            </button>


            <button
                type="button"
                class="novus-ai-secondary-btn"
                data-ai-try-again
            >
                <i data-lucide="refresh-cw"></i>

                Try Another

            </button>


            <button
                type="button"
                class="novus-ai-secondary-btn"
                data-ai-close-review
            >
                <i data-lucide="x"></i>

                Keep Original

            </button>

        </div>


        <div class="novus-ai-tip">

            <i data-lucide="lightbulb"></i>

            <span>
                Applying this suggestion updates only this
                selected piece of your resume. Your Resume
                Studio content remains under your control.
            </span>

        </div>
    `;

    if (window.lucide) {
        lucide.createIcons();
    }
}


async function requestATSRewrite(item) {
    const resumeId = getATSResumeId();
    const jobDescription = getATSJobDescription();

    if (!resumeId) {
        alert("Please select a resume first.");
        return;
    }

    if (!jobDescription) {
        alert("Please provide a job description first.");
        return;
    }

    renderATSReviewLoading(item);

    try {
        const response = await fetch(
            "/api/analyzer/rewrite",
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    resume_id: resumeId,
                    content_type: item.contentType,
                    content: item.content,
                    job_description: jobDescription
                })
            }
        );

        const data =
            await response.json();

        if (!response.ok || !data.success) {
            throw new Error(
                data.message ||
                "AI rewrite failed."
            );
        }

        window.novusATSCurrentRewrite = {
            item,
            rewrite: data.rewrite,
            validation: data.validation
        };

        renderATSReview(item);

    } catch (error) {

        console.error(
            "ATS rewrite error:",
            error
        );

        const review =
            getATSReviewContainer();

        if (review) {
            review.innerHTML = `
                <div class="novus-ai-error">

                    <i data-lucide="circle-alert"></i>

                    <h3>
                        Couldn't generate the suggestion
                    </h3>

                    <p>
                        ${escapeATSHTML(
                /429|RESOURCE_EXHAUSTED|quota/i.test(
                    error.message || ""
                )
                    ? "Gemini AI quota is currently exhausted. Please try again later or check your Gemini API quota and billing settings."
                    : "We couldn't generate the AI suggestion right now. Please try again."
            )}
                    </p>

                    <button
                        type="button"
                        class="novus-ai-secondary-btn"
                        data-ai-retry-current
                    >
                        Try Again
                    </button>

                </div>
            `;

            if (window.lucide) {
                lucide.createIcons();
            }
        }
    }
}


async function applyATSRewrite() {
    const current =
        window.novusATSCurrentRewrite;

    if (!current) return;

    const item = current.item;
    const rewrite = current.rewrite || {};
    const validation = current.validation || {};

    const rewritten =
        rewrite.rewritten?.trim();

    if (!rewritten) {
        alert("No improved content is available.");
        return;
    }

    if (validation.is_safe !== true) {
        const confirmed = window.confirm(
            "Novus recommends reviewing this suggestion before applying it. " +
            "Are you sure you want to replace the original content?"
        );

        if (!confirmed) {
            return;
        }
    }

    const resumeId = getATSResumeId();

    try {
        const response = await fetch(
            "/api/analyzer/apply-rewrite",
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    resume_id: resumeId,
                    content_type: item.contentType,
                    section_type: item.sectionType,
                    section_index: item.sectionIndex,
                    bullet_index: item.bulletIndex,

                    // Important: send the exact original content
                    // so the backend can locate the correct bullet.
                    original_content: item.content,
                    content: rewritten
                })
            }
        );

        const data =
            await response.json();

        if (!response.ok || !data.success) {
            throw new Error(
                data.message ||
                "Unable to update your resume."
            );
        }

        const previousContent =
            item.content;

        window.novusATSLastAppliedItemId =
            item.id;

        window.novusATSLastAppliedOriginal =
            previousContent;

        item.content = rewritten;

        window.novusATSCurrentRewrite = null;

        renderATSAppliedState(
            item,
            previousContent,
            rewritten
        );

    } catch (error) {

        console.error(
            "ATS apply rewrite error:",
            error
        );

        alert(
            error.message ||
            "Unable to update the resume."
        );
    }
}


function renderATSAppliedState(
    item,
    previousContent,
    rewritten
) {
    const review =
        getATSReviewContainer();

    if (!review) return;

    review.innerHTML = `
        <div class="novus-ai-applied">

            <div class="novus-ai-applied-icon">
                <i data-lucide="check"></i>
            </div>

            <span class="ats-section-eyebrow">
                Resume Updated
            </span>

            <h3>
                Content applied successfully
            </h3>

            <p>
                The selected content in your resume has been
                replaced with the validated AI suggestion.
            </p>

            <div class="novus-ai-applied-content">
                ${escapeATSHTML(rewritten)}
            </div>

            <div class="novus-ai-applied-actions">

                <button
                    type="button"
                    class="novus-ai-secondary-btn"
                    data-ai-undo
                    data-ai-undo-content="${escapeATSHTML(
        previousContent
    )}"
                >
                    <i data-lucide="undo-2"></i>
                    Undo
                </button>

                <button
                    type="button"
                    class="novus-ai-primary-btn"
                    data-ai-reanalyze
                >
                    <i data-lucide="refresh-cw"></i>
                    Reanalyze Resume
                </button>

            </div>

            <div class="novus-ai-tip">
                <i data-lucide="lightbulb"></i>

                <span>
                    The change is saved to your resume and will
                    be reflected in Resume Studio. Reanalyze to
                    refresh the ATS score for this job.
                </span>
            </div>

        </div>
    `;

    if (window.lucide) {
        lucide.createIcons();
    }
}


async function undoATSRewrite() {
    const current =
        window.novusATSCurrentRewrite;

    /*
     * The current rewrite object is cleared after apply,
     * so use the selected item stored in the global state.
     */
    const item =
        window.novusATSRewriteItems.find(
            candidate =>
                candidate.id ===
                window.novusATSLastAppliedItemId
        );

    if (!item) {
        alert("Undo information is no longer available.");
        return;
    }

    const original =
        window.novusATSLastAppliedOriginal;

    if (!original) {
        alert("Original content is unavailable.");
        return;
    }

    try {
        const response = await fetch(
            "/api/analyzer/apply-rewrite",
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    resume_id: getATSResumeId(),
                    content_type: item.contentType,
                    section_type: item.sectionType,
                    section_index: item.sectionIndex,
                    bullet_index: item.bulletIndex,
                    content: original
                })
            }
        );

        const data =
            await response.json();

        if (!response.ok || !data.success) {
            throw new Error(
                data.message ||
                "Unable to undo the change."
            );
        }

        item.content = original;

        window.novusATSLastAppliedItemId = null;
        window.novusATSLastAppliedOriginal = null;

        const review =
            getATSReviewContainer();

        if (review) {
            review.innerHTML = `
                <div class="novus-ai-review-empty">

                    <div class="novus-ai-review-empty-icon">
                        <i data-lucide="undo-2"></i>
                    </div>

                    <h3>
                        Original content restored
                    </h3>

                    <p>
                        The selected resume content has been
                        restored.
                    </p>

                </div>
            `;

            if (window.lucide) {
                lucide.createIcons();
            }
        }

    } catch (error) {
        alert(
            error.message ||
            "Unable to undo the change."
        );
    }
}


function bindAIImprovementEvents() {
    const report =
        document.getElementById("atsReport");

    if (!report) return;

    report.querySelectorAll(
        "[data-ai-group-toggle]"
    ).forEach(button => {

        button.addEventListener(
            "click",
            () => {

                const group =
                    button.closest(
                        ".novus-ai-group"
                    );

                if (!group) return;

                group.classList.toggle(
                    "is-collapsed"
                );

            }
        );
    });


    report.querySelectorAll(
        "[data-ai-item-index]"
    ).forEach(button => {

        button.addEventListener(
            "click",
            () => {

                const index =
                    Number(
                        button.dataset.aiItemIndex
                    );

                const item =
                    window.novusATSRewriteItems[
                    index
                    ];

                if (!item) return;

                window.novusATSCurrentRewrite = {
                    item,
                    rewrite: null,
                    validation: null
                };

                const review =
                    getATSReviewContainer();

                if (!review) return;

                review.innerHTML = `
                    <div class="novus-ai-review-start">

                        <span class="ats-section-eyebrow">
                            ${escapeATSHTML(
                    item.groupItem ||
                    item.label
                )}
                        </span>

                        <h3>
                            Ready to improve this content?
                        </h3>

                        <div class="novus-ai-start-content">
                            ${escapeATSHTML(
                    item.content
                )}
                        </div>

                        <p>
                            Gemini will improve the wording
                            while preserving the facts,
                            technologies and responsibilities
                            already present in your resume.
                        </p>

                        <button
                            type="button"
                            class="novus-ai-primary-btn"
                            data-ai-start-rewrite
                        >
                            <i data-lucide="sparkles"></i>
                            Improve with AI
                        </button>

                    </div>
                `;

                if (window.lucide) {
                    lucide.createIcons();
                }

            }
        );
    });


    report.addEventListener(
        "click",
        async event => {

            const startButton =
                event.target.closest(
                    "[data-ai-start-rewrite]"
                );

            if (startButton) {

                const item =
                    window.novusATSCurrentRewrite?.item;

                if (item) {
                    await requestATSRewrite(item);
                }

                return;
            }


            const retryButton =
                event.target.closest(
                    "[data-ai-retry-current]"
                );

            if (retryButton) {

                const item =
                    window.novusATSCurrentRewrite?.item;

                if (item) {
                    await requestATSRewrite(item);
                }

                return;
            }


            const tryAgainButton =
                event.target.closest(
                    "[data-ai-try-again]"
                );

            if (tryAgainButton) {

                const item =
                    window.novusATSCurrentRewrite?.item;

                if (item) {
                    await requestATSRewrite(item);
                }

                return;
            }


            const applyButton =
                event.target.closest(
                    "[data-ai-apply]"
                );

            if (applyButton) {

                await applyATSRewrite();

                return;
            }


            const closeButton =
                event.target.closest(
                    "[data-ai-close-review]"
                );

            if (closeButton) {

                const review =
                    getATSReviewContainer();

                if (review) {
                    review.innerHTML = `
                        <div class="novus-ai-review-empty">

                            <div class="novus-ai-review-empty-icon">
                                <i data-lucide="sparkles"></i>
                            </div>

                            <h3>
                                Select content to improve
                            </h3>

                            <p>
                                Choose another resume item
                                to review an AI suggestion.
                            </p>

                        </div>
                    `;

                    if (window.lucide) {
                        lucide.createIcons();
                    }
                }

                return;
            }


            const undoButton =
                event.target.closest(
                    "[data-ai-undo]"
                );

            if (undoButton) {
                await undoATSRewrite();
                return;
            }


            const reanalyzeButton =
                event.target.closest(
                    "[data-ai-reanalyze]"
                );

            if (reanalyzeButton) {

                const analyzeButton =
                    document.getElementById(
                        "analyzeResumeBtn"
                    );

                if (analyzeButton) {
                    analyzeButton.click();
                }

                return;
            }

        }
    );
}


/* =========================================================
   MAIN REPORT RENDERER
========================================================= */

function uniqueATSDisplayTerms(values) {
    const result = [];
    const seen = new Set();

    (Array.isArray(values) ? values : []).forEach(value => {
        const text = String(value || "").trim();
        if (!text) return;

        const key = text
            .toLowerCase()
            .replace(/[.\-_/]+/g, " ")
            .replace(/\s+/g, " ")
            .trim();

        if (seen.has(key)) return;

        seen.add(key);
        result.push(text);
    });

    return result;
}

function getATSReportContainer() {
    let report = document.getElementById("atsReport");

    if (report) {
        return report;
    }

    report = document.createElement("section");
    report.id = "atsReport";
    report.className = "ats-report";

    const main = document.querySelector(".dashboard-main") || document.querySelector("main");

    if (main) {
        main.appendChild(report);
    } else {
        document.body.appendChild(report);
    }

    return report;
}


function renderATSReport(analysis, autoScroll = true) {

    if (!analysis) {
        console.error("ATS report data is missing.");
        return;
    }

    const report = getATSReportContainer();
    const scoreData = analysis.score || {};
    const score = Number(scoreData.score || 0);
    const level = scoreData.level || "Unknown";
    const scoreClass = getATSScoreClass(score);
    const gapSummary = analysis.gap_summary || {};
    const aiItems = buildATSRewriteItems(analysis);
    const resume = analysis.resume || {};
    const matches = analysis.matches || {};
    const aiAnalysis = analysis.ai_analysis || {};

    const matched = Array.isArray(matches.required_skills?.matched)
        ? matches.required_skills.matched : [];

    const missing = Array.isArray(matches.required_skills?.missing)
        ? matches.required_skills.missing : [];

    const techMatched = Array.isArray(matches.technical_keywords?.matched)
        ? matches.technical_keywords.matched : [];

    const displayMatched = uniqueATSDisplayTerms(
        matched.concat(techMatched)
    );

    const displayMissing = uniqueATSDisplayTerms(missing);

    const completeness = getATSResumeCompleteness(resume);

    const reportGapInput = Array.isArray(analysis.gaps?.gaps)
        ? analysis.gaps.gaps
        : [];
    const reportGapModel = buildATSGapModel(reportGapInput);
    const renderedGapCount =
        reportGapModel.critical.length +
        reportGapModel.skills.length +
        reportGapModel.content.length +
        reportGapModel.optional.length;

    const scoreText = score >= 85
        ? "Excellent match"
        : score >= 70
            ? "Strong match"
            : score >= 55
                ? "Moderate match"
                : "Needs improvement";

    const fitLabel = score >= 85
        ? "Excellent Fit"
        : score >= 70
            ? "Good Fit"
            : score >= 55
                ? "Potential Fit"
                : "Needs Work";

    const matchSentence = score >= 85
        ? "Your resume matches this job very strongly."
        : score >= 70
            ? "Your resume matches this job strongly."
            : score >= 55
                ? "Your resume has a moderate match with this job."
                : "Your resume needs more alignment with this job.";

    const firstName = String(
        resume.personal?.fullName || "Your resume"
    ).trim().split(/\s+/)[0] || "there";

    const priorities = Array.isArray(aiAnalysis.improvement_priorities)
        ? aiAnalysis.improvement_priorities
        : [];

    const fallbackGaps = Array.isArray(analysis.gaps?.gaps)
        ? analysis.gaps.gaps
        : [];

    const topImprovements = priorities.length
        ? priorities.slice(0, 3)
        : fallbackGaps.slice(0, 3).map((gap, index) => ({
            priority: index + 1,
            area: formatATSLabel(gap.category || "Resume improvement"),
            issue: gap.item || gap.requirement || gap.text || "Improve resume alignment",
            recommendation: gap.reason || gap.action || "Review the relevant resume evidence."
        }));

    const strengths = Array.isArray(aiAnalysis.strengths)
        ? aiAnalysis.strengths
        : [];

    const criticalIssues = Array.isArray(aiAnalysis.critical_issues)
        ? aiAnalysis.critical_issues
        : [];

    const overallAssessment =
        aiAnalysis.overall_assessment ||
        "Novus has completed the resume-to-job comparison. Review the highest-impact gaps and keywords below.";

    const safeScore = Math.max(0, Math.min(100, score));

    report.innerHTML = `
        <div class="novus-v2-report-head">
            <div>
                <span class="novus-v2-kicker">ATS ANALYSIS</span>
                <h1>Resume Match Report</h1>
                <p>
                    ${escapeATSHTML(resume.title || "Selected resume")}
                    <span aria-hidden="true">·</span>
                    Your Resume
                </p>
            </div>

            <div class="novus-v2-head-actions">
                <a href="/insights" class="novus-v2-outline-btn">
                    <i data-lucide="arrow-left"></i>
                    Back to Insights
                </a>
                <a href="/analyzer" class="novus-v2-primary-btn">
                    <i data-lucide="plus"></i>
                    Analyze New Job
                </a>
            </div>
        </div>

        <!-- SCORE HERO -->
        <section class="novus-v2-score-card">
            <div class="novus-v2-score-main">
                <div
                    class="novus-v2-score-ring ${scoreClass}"
                    style="--score-deg:${safeScore * 3.6}deg"
                >
                    <div>
                        <strong>${score.toFixed(0)}%</strong>
                        <span>ATS SCORE</span>
                    </div>
                </div>

                <div class="novus-v2-score-copy">
                    <div class="novus-v2-score-title">
                        <h2>${escapeATSHTML(
                            score >= 85 ? "Excellent Match" :
                            score >= 70 ? "Strong Match" :
                            score >= 55 ? "Moderate Match" :
                            "Needs Improvement"
                        )}</h2>
                        <span class="novus-v2-fit-badge ${scoreClass}">
                            ${escapeATSHTML(fitLabel)}
                        </span>
                    </div>

                    <p>
                        ${escapeATSHTML(matchSentence)}
                    </p>

                    <small>
                        Novus calculates this score using deterministic resume-to-job matching.
                        AI suggestions are shown separately and do not change the score.
                    </small>
                </div>
            </div>
        </section>

        <!-- SUMMARY CARDS -->
        <section class="novus-v2-stat-grid" aria-label="Analysis summary">
            <article class="novus-v2-stat-card">
                <div class="novus-v2-stat-icon matched">
                    <i data-lucide="check-circle-2"></i>
                </div>
                <div>
                    <strong>${displayMatched.length}</strong>
                    <h3>Matched Keywords</h3>
                    <p>Detected in the job description</p>
                </div>
            </article>

            <article class="novus-v2-stat-card">
                <div class="novus-v2-stat-icon missing">
                    <i data-lucide="circle-alert"></i>
                </div>
                <div>
                    <strong>${displayMissing.length}</strong>
                    <h3>Missing Keywords</h3>
                    <p>Potential alignment gaps</p>
                </div>
            </article>

            <article class="novus-v2-stat-card">
                <div class="novus-v2-stat-icon sections">
                    <i data-lucide="layers-3"></i>
                </div>
                <div>
                    <strong>${completeness.totalCount}</strong>
                    <h3>Core Sections</h3>
                    <p>${completeness.completeCount} currently complete</p>
                </div>
            </article>
        </section>

        <!-- BREAKDOWN + KEYWORDS -->
        <section class="novus-v2-two-column">
            <article class="novus-v2-card">
                <div class="novus-v2-card-head">
                    <div>
                        <span class="novus-v2-kicker">SCORING</span>
                        <h2>Score Breakdown</h2>
                        <p>See how each ATS category contributes to the result.</p>
                    </div>
                    <span class="novus-v2-total">
                        Total: ${score.toFixed(0)}%
                    </span>
                </div>

                <div class="novus-v2-breakdown">
                    ${renderATSScoreBreakdown(scoreData)}
                </div>
            </article>

            <article class="novus-v2-card">
                <div class="novus-v2-card-head">
                    <div>
                        <span class="novus-v2-kicker">KEYWORD MATCH</span>
                        <h2>Matched & Missing</h2>
                        <p>Keywords detected across the job requirements.</p>
                    </div>
                    <a href="#novus-v2-keywords" class="novus-v2-text-btn">View all</a>
                </div>

                <div id="novus-v2-keywords" class="novus-v2-keyword-block matched">
                    <div class="novus-v2-keyword-head">
                        <strong><i data-lucide="check"></i> Matched Keywords</strong>
                        <span>${displayMatched.length}</span>
                    </div>
                    <div class="novus-v2-keywords">
                        ${
                            displayMatched.slice(0, 12).map(k =>
                                `<span>${escapeATSHTML(k)}</span>`
                            ).join("")
                            || `<em>No matched keywords found.</em>`
                        }
                    </div>
                </div>

                <div class="novus-v2-keyword-block missing">
                    <div class="novus-v2-keyword-head">
                        <strong><i data-lucide="circle-alert"></i> Missing Keywords</strong>
                        <span>${displayMissing.length}</span>
                    </div>
                    <div class="novus-v2-keywords">
                        ${
                            displayMissing.slice(0, 12).map(k =>
                                `<span>${escapeATSHTML(k)}</span>`
                            ).join("")
                            || `<em>No required keywords are missing.</em>`
                        }
                    </div>
                </div>
            </article>
        </section>

        <!-- THREE INSIGHT CARDS -->
        <section class="novus-v2-three-column">
            <article class="novus-v2-card novus-v2-improvements-card">
                <div class="novus-v2-card-head">
                    <div>
                        <span class="novus-v2-kicker">IMPROVEMENT PLAN</span>
                        <h2>Top Improvements</h2>
                        <p>Focus on the changes with the clearest impact.</p>
                    </div>
                </div>

                <div class="novus-v2-priority-list">
                    ${
                        topImprovements.length
                            ? topImprovements.map((item, index) => `
                                <div class="novus-v2-priority">
                                    <span>${String(item.priority || index + 1).padStart(2, "0")}</span>
                                    <div>
                                        <strong>${escapeATSHTML(
                                            item.issue || item.area || "Improvement"
                                        )}</strong>
                                        <p>${escapeATSHTML(
                                            item.recommendation || "Review the relevant resume evidence."
                                        )}</p>
                                    </div>
                                </div>
                            `).join("")
                            : `
                                <div class="novus-v2-empty-mini">
                                    <i data-lucide="check-circle-2"></i>
                                    <span>No major improvements were identified.</span>
                                </div>
                            `
                    }
                </div>
            </article>

            <article class="novus-v2-card novus-v2-ai-summary-card">
                <div class="novus-v2-card-head">
                    <div>
                        <span class="novus-v2-kicker">GEMINI AI</span>
                        <h2>AI Insights</h2>
                        <p>Contextual observations from your resume and job description.</p>
                    </div>
                    <span class="novus-v2-powered">Powered by Gemini</span>
                </div>

                <p class="novus-v2-assessment">
                    ${escapeATSHTML(overallAssessment)}
                </p>

                ${
                    criticalIssues.length
                        ? `
                            <div class="novus-v2-ai-issue">
                                <i data-lucide="circle-alert"></i>
                                <span>${escapeATSHTML(criticalIssues[0])}</span>
                            </div>
                        `
                        : strengths.length
                            ? `
                                <div class="novus-v2-ai-issue positive">
                                    <i data-lucide="check-circle-2"></i>
                                    <span>${escapeATSHTML(strengths[0])}</span>
                                </div>
                            `
                            : ""
                }
            </article>

            <article class="novus-v2-card novus-v2-actions-card">
                <div class="novus-v2-card-head">
                    <div>
                        <span class="novus-v2-kicker">ACTIONS</span>
                        <h2>Quick Actions</h2>
                    </div>
                </div>

                <div class="novus-v2-actions">
                    <a href="/resume-studio" class="novus-v2-action">
                        <i data-lucide="file-text"></i>
                        <span>
                            <strong>Go to Resume Studio</strong>
                            <small>Edit your resume content</small>
                        </span>
                        <i data-lucide="arrow-right"></i>
                    </a>

                    <button type="button" class="novus-v2-action" data-ai-reanalyze>
                        <i data-lucide="refresh-cw"></i>
                        <span>
                            <strong>Re-analyze with Current JD</strong>
                            <small>Check your score after changes</small>
                        </span>
                        <i data-lucide="arrow-right"></i>
                    </button>

                    <a href="/insights" class="novus-v2-action">
                        <i data-lucide="bar-chart-3"></i>
                        <span>
                            <strong>View in Insights</strong>
                            <small>Review this saved analysis later</small>
                        </span>
                        <i data-lucide="arrow-right"></i>
                    </a>
                </div>
            </article>
        </section>

        <!-- COMPACT AI IMPROVEMENT ENTRY -->
        <section class="novus-v2-ai-banner">
            <div class="novus-v2-ai-banner-icon">
                <i data-lucide="sparkles"></i>
            </div>
            <div>
                <span class="novus-v2-kicker">GEMINI AI</span>
                <h2>AI Resume Improvements</h2>
                <p>
                    Review and apply AI-powered suggestions using content already present in your resume.
                </p>
            </div>
            <span class="novus-v2-ai-count">
                ${aiItems.length} ${aiItems.length === 1 ? "suggestion" : "suggestions"}
            </span>
            <button type="button" class="novus-v2-ai-toggle" data-ai-expand>
                View AI Improvements
                <i data-lucide="arrow-right"></i>
            </button>
        </section>

        <!-- DETAILED ANALYSIS -->
        <section class="novus-v2-details">
            <details>
                <summary>
                    <span>
                        <i data-lucide="scan-search"></i>
                        Resume Gaps & Evidence
                    </span>
                    <small>
                        ${renderedGapCount} ${renderedGapCount === 1 ? "item" : "items"}
                    </small>
                </summary>
                <div class="novus-v2-detail-body">
                    ${renderATSGaps(analysis)}
                </div>
            </details>

            <details>
                <summary>
                    <span>
                        <i data-lucide="file-check-2"></i>
                        Resume Completeness
                    </span>
                    <small>
                        ${completeness.completeCount}/${completeness.totalCount} complete
                    </small>
                </summary>
                <div class="novus-v2-detail-body">
                    ${renderATSResumeCompleteness(resume)}
                </div>
            </details>

            <details>
                <summary>
                    <span>
                        <i data-lucide="brain"></i>
                        Detailed AI Insights
                    </span>
                    <small>Strengths, issues & priorities</small>
                </summary>
                <div class="novus-v2-detail-body">
                    ${renderATSAnalysis(aiAnalysis)}
                </div>
            </details>
        </section>

        <!-- FULL AI WORKSPACE, HIDDEN UNTIL REQUESTED -->
        <div id="novus-v2-ai-details" class="novus-v2-ai-details">
            ${renderAIImprovements(analysis)}
        </div>
    `;

    setATSAnalyzerMode(true);
    report.classList.add("ats-report-visible");
    bindAIImprovementEvents();

    const aiToggle = report.querySelector("[data-ai-expand]");
    const aiDetails = report.querySelector("#novus-v2-ai-details");

    if (aiToggle && aiDetails) {
        aiToggle.addEventListener("click", () => {
            const isOpen = aiDetails.classList.toggle("is-open");
            aiToggle.classList.toggle("is-open", isOpen);
            aiToggle.innerHTML = isOpen
                ? `Hide AI Improvements <i data-lucide="arrow-up"></i>`
                : `View AI Improvements <i data-lucide="arrow-right"></i>`;

            if (window.lucide) {
                lucide.createIcons();
            }

            if (isOpen) {
                aiDetails.scrollIntoView({
                    behavior: "smooth",
                    block: "start"
                });
            }
        });
    }

    if (window.lucide) {
        lucide.createIcons();
    }

    if (autoScroll) {
        setTimeout(() => {
            report.scrollIntoView({
                behavior: "smooth",
                block: "start"
            });
        }, 100);
    }
}

