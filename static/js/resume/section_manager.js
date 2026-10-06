/* ==========================================
   NOVUS SECTION MANAGER
   Handles fixed + optional resume sections.
========================================== */

const SectionManager = {

    sections: {},
    sectionOrder: [],

    init() {
        this.initializeSections();
        this.initializeSectionOrder();
        this.restoreStoredSectionMetadata();
        this.renderAdditionalSections();
        this.applySectionOrder();
        this.initializeSortable();
        this.initializeVisibilityButtons();
        this.initializeCollapseButtons();
        this.initializeAdditionalSectionButtons();
        this.initializeSectionObserver();
        this.applyVisibility();
        this.updateSectionCount();
    },

    initializeSections() {
        const base = {
            personal: { title: "Personal Information", visible: true, locked: true },
            summary: { title: "Professional Summary", visible: true, locked: false },
            education: { title: "Education", visible: true, locked: false },
            skills: { title: "Skills", visible: true, locked: false },
            projects: { title: "Projects", visible: true, locked: false },
            experience: { title: "Experience", visible: true, locked: false },
            certifications: { title: "Certifications", visible: true, locked: false }
        };

        this.sections = base;
    },

    initializeSectionOrder() {
        this.sectionOrder = [
            "personal",
            "summary",
            "education",
            "skills",
            "projects",
            "experience",
            "certifications"
        ];
    },

    restoreStoredSectionMetadata() {
        const stored = ResumeEngine._storedSectionData;

        if (!stored) return;

        if (stored.metadata && typeof stored.metadata === "object") {
            Object.entries(stored.metadata).forEach(([id, meta]) => {
                if (this.sections[id]) {
                    this.sections[id] = {
                        ...this.sections[id],
                        ...meta
                    };
                } else if (meta && meta.dynamic) {
                    this.sections[id] = {
                        title: meta.title || "Additional Section",
                        visible: meta.visible !== false,
                        locked: false,
                        dynamic: true,
                        type: meta.type || "custom"
                    };
                }
            });
        }

        if (Array.isArray(stored.order)) {
            const valid = stored.order.filter(id => this.sections[id]);
            const missingBase = this.sectionOrder.filter(id => !valid.includes(id));
            const missingDynamic = Object.keys(this.sections).filter(id => !valid.includes(id));
            this.sectionOrder = [...valid, ...missingBase, ...missingDynamic];
        }
    },

    initializeSortable() {
        const container = document.getElementById("resumeSections");
        if (!container || typeof Sortable === "undefined") return;

        if (container._novusSortable) {
            container._novusSortable.destroy();
        }

        container._novusSortable = Sortable.create(container, {
            animation: 180,
            draggable: "[data-section]",
            handle: ".drag-handle",
            onEnd: () => this.updateSectionOrder(container)
        });
    },

    initializeVisibilityButtons() {
        document.querySelectorAll(".section-visibility-btn").forEach(button => {
            if (button.dataset.bound === "true") return;
            button.dataset.bound = "true";

            button.addEventListener("click", event => {
                event.preventDefault();
                event.stopPropagation();
                this.toggleSection(button.dataset.sectionToggle);
            });
        });
    },

    initializeCollapseButtons() {
        document.querySelectorAll(".collapse-btn").forEach(button => {
            if (button.dataset.bound === "true") return;
            button.dataset.bound = "true";

            button.addEventListener("click", event => {
                event.preventDefault();
                const card = button.closest(".editor-card");
                if (!card) return;
                card.classList.toggle("collapsed");
            });
        });
    },

    initializeAdditionalSectionButtons() {
        document.querySelectorAll(".add-section").forEach(button => {
            if (button.dataset.bound === "true") return;
            button.dataset.bound = "true";

            button.addEventListener("click", () => {
                this.addAdditionalSection(button.dataset.section);
            });
        });
    },

    initializeSectionObserver() {
        window.addEventListener("scroll", () => this.updateActiveSection(), { passive: true });
        this.updateActiveSection();
    },

    addAdditionalSection(type) {
        if (!["achievements", "languages", "custom"].includes(type)) return;

        const existing = Object.entries(this.sections).find(
            ([, section]) => section.dynamic && section.type === type && type !== "custom"
        );

        if (existing) {
            this.scrollToSection(existing[0]);
            return;
        }

        const id = type === "custom"
            ? `custom-${Date.now()}`
            : `additional-${type}`;

        const titles = {
            achievements: "Achievements",
            languages: "Languages",
            custom: "Custom Section"
        };

        this.sections[id] = {
            title: titles[type],
            visible: true,
            locked: false,
            dynamic: true,
            type
        };

        this.sectionOrder.push(id);

        if (!Array.isArray(ResumeEngine.state.additionalSections)) {
            ResumeEngine.state.additionalSections = [];
        }

        ResumeEngine.state.additionalSections.push({
            id,
            type,
            title: titles[type],
            content: "",
            visible: true
        });

        this.renderAdditionalSection(id);
        this.renderAdditionalNavItem(id);
        this.renderAdditionalPreview(id);
        this.initializeVisibilityButtons();
        this.initializeCollapseButtons();
        this.applySectionOrder();
        this.applyVisibility();
        this.updateSectionCount();
        this.save();

        requestAnimationFrame(() => this.scrollToSection(id));
    },

    renderAdditionalSections() {
        const additional = Array.isArray(ResumeEngine.state.additionalSections)
            ? ResumeEngine.state.additionalSections
            : [];

        additional.forEach(item => {
            if (!item || !item.id) return;

            if (!this.sections[item.id]) {
                this.sections[item.id] = {
                    title: item.title || "Additional Section",
                    visible: item.visible !== false,
                    locked: false,
                    dynamic: true,
                    type: item.type || "custom"
                };
            }

            if (!this.sectionOrder.includes(item.id)) {
                this.sectionOrder.push(item.id);
            }

            this.renderAdditionalSection(item.id);
            this.renderAdditionalNavItem(item.id);
            this.renderAdditionalPreview(item.id);
        });
    },

    renderAdditionalSection(id) {
        const item = this.getAdditionalData(id);
        const container = document.getElementById("resumeSections");
        if (!item || !container) return;

        const existing = document.getElementById(id);
        if (existing) existing.remove();

        const icon = item.type === "achievements"
            ? "trophy"
            : item.type === "languages"
                ? "languages"
                : "file-plus-2";

        const placeholder = item.type === "achievements"
            ? "Add achievements, awards, leadership, hackathons, or other highlights."
            : item.type === "languages"
                ? "English\nHindi\nTelugu"
                : "Add any additional information that strengthens your resume.";

        const card = document.createElement("section");
        card.className = "editor-card additional-editor-card";
        card.id = id;
        card.dataset.section = id;
        card.dataset.dynamicSection = "true";

        card.innerHTML = `
            <div class="card-header">
                <div class="drag-handle" title="Drag to reorder">
                    <i data-lucide="grip-vertical"></i>
                </div>
                <div class="card-title">
                    <i data-lucide="${icon}"></i>
                    <div>
                        <h2>${escapeHTML(item.title || "Additional Section")}</h2>
                        <p>Optional section for your resume.</p>
                    </div>
                </div>
                <div class="card-actions">
                    <button type="button" class="delete-btn dynamic-section-delete" title="Remove section">
                        <i data-lucide="trash-2"></i>
                    </button>
                    <button type="button" class="collapse-btn" title="Collapse section">
                        <i data-lucide="chevron-up"></i>
                    </button>
                </div>
            </div>
            <div class="card-content">
                ${item.type === "custom" ? `
                    <div class="form-group">
                        <label>Section Title</label>
                        <input type="text" class="additional-title-input" value="${escapeAttr(item.title || "Custom Section")}" placeholder="e.g. Volunteering">
                    </div>
                ` : ""}
                <div class="form-group">
                    <label>${item.type === "languages" ? "Languages" : "Details"}</label>
                    <textarea class="additional-content-input" rows="6" placeholder="${escapeAttr(placeholder)}">${escapeHTML(item.content || "")}</textarea>
                    ${item.type === "languages" ? '<small class="field-help">Enter one language per line.</small>' : ""}
                </div>
            </div>
        `;

        container.appendChild(card);

        card.querySelector(".additional-content-input")?.addEventListener("input", event => {
            item.content = event.target.value;
            this.syncAndRefresh();
        });

        card.querySelector(".additional-title-input")?.addEventListener("input", event => {
            item.title = event.target.value.trim() || "Custom Section";
            this.sections[id].title = item.title;
            this.updateAdditionalNavItem(id);
            this.updateAdditionalPreview(id);
            this.syncAndRefresh();
        });

        card.querySelector(".dynamic-section-delete")?.addEventListener("click", () => {
            this.removeAdditionalSection(id);
        });

        lucide.createIcons();
    },

    renderAdditionalNavItem(id) {
        const nav = document.querySelector(".section-nav");
        if (!nav) return;

        const item = this.getAdditionalData(id);
        if (!item) return;

        const existing = document.getElementById(`progress-${id}`);
        if (existing) return;

        const icon = item.type === "achievements"
            ? "trophy"
            : item.type === "languages"
                ? "languages"
                : "file-plus-2";

        const link = document.createElement("a");
        link.href = `#${id}`;
        link.id = `progress-${id}`;
        link.className = "section-nav-item dynamic-section-nav";
        link.innerHTML = `
            <div class="section-nav-content">
                <i data-lucide="${icon}"></i>
                <span>${escapeHTML(item.title || "Additional Section")}</span>
            </div>
            <button type="button" class="section-visibility-btn" data-section-toggle="${id}" title="Hide Section">
                <i data-lucide="eye"></i>
            </button>
        `;

        nav.appendChild(link);

        link.addEventListener("click", event => {
            if (event.target.closest(".section-visibility-btn")) return;
            event.preventDefault();
            this.scrollToSection(id);
        });

        lucide.createIcons();
    },

    updateAdditionalNavItem(id) {
        const link = document.getElementById(`progress-${id}`);
        const item = this.getAdditionalData(id);
        if (!link || !item) return;
        const label = link.querySelector(".section-nav-content span");
        if (label) label.textContent = item.title || "Additional Section";
    },

    renderAdditionalPreview(id) {
        const item = this.getAdditionalData(id);
        const preview = document.getElementById("resumePreview");
        if (!item || !preview) return;

        const existing = document.querySelector(`[data-preview-section="${id}"]`);
        if (existing) existing.remove();

        const section = document.createElement("section");
        section.className = "preview-section additional-preview-section";
        section.dataset.previewSection = id;
        section.innerHTML = `
            <h3>${escapeHTML(item.title || "Additional Section")}</h3>
            <div class="additional-preview-content"></div>
        `;

        preview.appendChild(section);
        this.updateAdditionalPreview(id);
    },

    updateAdditionalPreview(id) {
        const item = this.getAdditionalData(id);
        const section = document.querySelector(`[data-preview-section="${id}"]`);
        if (!item || !section) return;

        const heading = section.querySelector("h3");
        const content = section.querySelector(".additional-preview-content");

        if (heading) heading.textContent = item.title || "Additional Section";
        if (!content) return;

        const value = (item.content || "").trim();

        if (!value) {
            content.innerHTML = '<div class="empty-preview">Add details in the editor.</div>';
            return;
        }

        if (item.type === "languages") {
            const lines = value.split(/\r?\n|,/).map(v => v.trim()).filter(Boolean);
            content.innerHTML = `<ul class="preview-list">${lines.map(v => `<li>${escapeHTML(v)}</li>`).join("")}</ul>`;
        } else {
            const paragraphs = value.split(/\r?\n\s*\r?\n/).map(v => v.trim()).filter(Boolean);
            content.innerHTML = paragraphs.map(v => `<p>${escapeHTML(v).replace(/\r?\n/g, "<br>")}</p>`).join("");
        }
    },

    getAdditionalData(id) {
        return (ResumeEngine.state.additionalSections || []).find(item => item.id === id);
    },

    removeAdditionalSection(id) {
        const item = this.getAdditionalData(id);
        if (!item) return;

        if (!confirm(`Remove "${item.title || "Additional Section"}"?`)) return;

        ResumeEngine.state.additionalSections = (ResumeEngine.state.additionalSections || [])
            .filter(section => section.id !== id);

        delete this.sections[id];
        this.sectionOrder = this.sectionOrder.filter(sectionId => sectionId !== id);

        document.getElementById(id)?.remove();
        document.getElementById(`progress-${id}`)?.remove();
        document.querySelector(`[data-preview-section="${id}"]`)?.remove();

        this.applySectionOrder();
        this.updateSectionCount();
        this.save();
        updatePreview(ResumeEngine.state);
        updateCompletion(ResumeEngine.state);
    },

    syncAndRefresh() {
        ResumeEngine.storage.saveDraft();
        autoSaveResume();
        updatePreview(ResumeEngine.state);
        updateCompletion(ResumeEngine.state);
    },

    save() {
        ResumeEngine.storage.saveDraft();
        autoSaveResume();
    },

    scrollToSection(sectionId) {
        const section = document.querySelector(`[data-section="${sectionId}"]`);
        if (!section) return;

        const headerOffset = 105;
        const y = section.getBoundingClientRect().top + window.scrollY - headerOffset;
        window.scrollTo({ top: Math.max(0, y), behavior: "smooth" });
        this.setActiveSection(sectionId);
    },

    setActiveSection(sectionId) {
        document.querySelectorAll(".section-nav a").forEach(link => link.classList.remove("active-section"));
        document.getElementById(`progress-${sectionId}`)?.classList.add("active-section");
    },

    updateActiveSection() {
        const sections = document.querySelectorAll("#resumeSections > [data-section]");
        let activeSection = null;
        let closestDistance = Infinity;

        sections.forEach(section => {
            if (section.style.display === "none") return;
            const rect = section.getBoundingClientRect();
            if (rect.bottom < 0 || rect.top > window.innerHeight) return;
            const distance = Math.abs(rect.top - 120);
            if (distance < closestDistance) {
                closestDistance = distance;
                activeSection = section.dataset.section;
            }
        });

        if (activeSection) this.setActiveSection(activeSection);
    },

    updateVisibilityButtons() {
        document.querySelectorAll(".section-visibility-btn").forEach(button => {
            const sectionId = button.dataset.sectionToggle;
            const visible = this.sections[sectionId]?.visible !== false;
            button.innerHTML = visible
                ? '<i data-lucide="eye"></i>'
                : '<i data-lucide="eye-off"></i>';
            button.title = visible ? "Hide Section" : "Show Section";
        });
        lucide.createIcons();
    },

    updateSectionOrder(container) {
        const sections = container.querySelectorAll(":scope > [data-section]");
        this.sectionOrder = Array.from(sections).map(section => section.dataset.section);
        this.applyPreviewOrder();
        this.save();
        this.updateActiveSection();
    },

    applySectionOrder() {
        const container = document.getElementById("resumeSections");
        if (!container) return;

        this.sectionOrder.forEach(sectionId => {
            const section = container.querySelector(`[data-section="${sectionId}"]`);
            if (section) container.appendChild(section);
        });

        this.applyPreviewOrder();
    },

    applyPreviewOrder() {
        const preview = document.getElementById("resumePreview");
        if (!preview) return;

        this.sectionOrder.forEach(sectionId => {
            const section = preview.querySelector(`[data-preview-section="${sectionId}"]`);
            if (section) preview.appendChild(section);
        });
    },

    hideSection(sectionId) {
        if (!this.sections[sectionId]) return;
        this.sections[sectionId].visible = false;
        this.applyVisibility();
        this.save();
    },

    showSection(sectionId) {
        if (!this.sections[sectionId]) return;
        this.sections[sectionId].visible = true;
        this.applyVisibility();
        this.save();
    },

    toggleSection(sectionId) {
        if (!this.sections[sectionId] || this.sections[sectionId].locked) return;
        this.sections[sectionId].visible = !this.sections[sectionId].visible;
        this.applyVisibility();
        this.save();
    },

    applyVisibility() {
        Object.entries(this.sections).forEach(([sectionId, section]) => {
            const editorSection = document.querySelector(`[data-section="${sectionId}"]`);
            if (editorSection) editorSection.style.display = section.visible ? "" : "none";

            const previewSection = document.querySelector(`[data-preview-section="${sectionId}"]`);
            if (previewSection) previewSection.style.display = section.visible ? "" : "none";
        });

        this.updateVisibilityButtons();
    },

    updateSectionCount() {
        const count = document.querySelector(".section-count");
        if (count) count.textContent = `${this.sectionOrder.length} Sections`;
    },

    getSection(sectionId) {
        return this.sections[sectionId];
    },

    getSectionOrder() {
        return [...this.sectionOrder];
    },

    getVisibleSections() {
        return this.sectionOrder.filter(id => this.sections[id]?.visible);
    }
};

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
