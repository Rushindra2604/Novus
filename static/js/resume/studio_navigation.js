document.addEventListener("DOMContentLoaded", () => {
    const toggle = document.getElementById("studioNavToggle");
    const drawer = document.getElementById("studioNavDrawer");
    const close = document.getElementById("studioNavClose");
    const backdrop = document.getElementById("studioNavBackdrop");

    if (!toggle || !drawer || !close || !backdrop) return;

    const setOpen = (open) => {
        drawer.classList.toggle("open", open);
        backdrop.classList.toggle("open", open);
        drawer.setAttribute("aria-hidden", String(!open));
        toggle.setAttribute("aria-expanded", String(open));
        document.body.classList.toggle("studio-nav-open", open);
    };

    toggle.addEventListener("click", () => setOpen(!drawer.classList.contains("open")));
    close.addEventListener("click", () => setOpen(false));
    backdrop.addEventListener("click", () => setOpen(false));

    document.addEventListener("keydown", (event) => {
        if (event.key === "Escape") setOpen(false);
    });
});
