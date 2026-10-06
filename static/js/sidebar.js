(function () {

    "use strict";


    /* =========================================================
       CONFIG
    ========================================================= */

    const STORAGE_KEY = "novus.sidebar.collapsed";

    const MOBILE_BREAKPOINT = 900;


    /* =========================================================
       HELPERS
    ========================================================= */

    function isMobile() {

        return window.innerWidth <= MOBILE_BREAKPOINT;

    }


    function getElements() {

        const layout =
            document.querySelector(".dashboard-layout");

        const sidebar =
            document.querySelector("[data-sidebar]");


        if (!layout || !sidebar) {

            return null;

        }


        return {

            layout,

            sidebar,

            collapseButton:
                document.querySelector(
                    "[data-sidebar-collapse]"
                ),

            mobileButton:
                document.querySelector(
                    "[data-sidebar-mobile]"
                ),

            backdrop:
                document.querySelector(
                    "[data-sidebar-backdrop]"
                ),

            links:
                sidebar.querySelectorAll(
                    ".sidebar-link"
                )

        };

    }


    /* =========================================================
       DESKTOP COLLAPSE
    ========================================================= */

    function setCollapsed(
        collapsed,
        save = true
    ) {

        const elements = getElements();

        if (!elements) {

            return;

        }


        elements.layout.classList.toggle(
            "sidebar-collapsed",
            collapsed
        );


        elements.sidebar.setAttribute(
            "data-collapsed",
            String(collapsed)
        );


        if (elements.collapseButton) {

            const label =
                collapsed
                    ? "Expand sidebar"
                    : "Collapse sidebar";


            elements.collapseButton.setAttribute(
                "aria-label",
                label
            );


            elements.collapseButton.setAttribute(
                "title",
                label
            );

        }


        if (save && !isMobile()) {

            localStorage.setItem(
                STORAGE_KEY,
                collapsed
                    ? "true"
                    : "false"
            );

        }

    }


    /* =========================================================
       MOBILE OPEN
    ========================================================= */

    function openMobileSidebar() {

        const elements = getElements();

        if (!elements) {

            return;

        }


        elements.layout.classList.add(
            "sidebar-mobile-open"
        );


        document.body.classList.add(
            "sidebar-lock-scroll"
        );


        if (elements.mobileButton) {

            elements.mobileButton.setAttribute(
                "aria-expanded",
                "true"
            );

        }

    }


    /* =========================================================
       MOBILE CLOSE
    ========================================================= */

    function closeMobileSidebar() {

        const elements = getElements();

        if (!elements) {

            return;

        }


        elements.layout.classList.remove(
            "sidebar-mobile-open"
        );


        document.body.classList.remove(
            "sidebar-lock-scroll"
        );


        if (elements.mobileButton) {

            elements.mobileButton.setAttribute(
                "aria-expanded",
                "false"
            );

        }

    }


    /* =========================================================
       ACTIVE NAVIGATION
    ========================================================= */

    function setActiveLink() {

        const elements = getElements();

        if (!elements) {

            return;

        }


        const currentPath =
            window.location.pathname
                .replace(/\/+$/, "")
                || "/";


        elements.links.forEach(
            function (link) {

                link.classList.remove(
                    "active"
                );


                link.removeAttribute(
                    "aria-current"
                );


                const exactPath =
                    link.dataset.path;


                const prefixPath =
                    link.dataset.prefix;


                let active = false;


                /* Exact route */

                if (exactPath) {

                    active =
                        currentPath === exactPath;

                }


                /* Prefix route */

                if (prefixPath) {

                    active =
                        currentPath.startsWith(
                            prefixPath
                        );

                }


                if (active) {

                    link.classList.add(
                        "active"
                    );


                    link.setAttribute(
                        "aria-current",
                        "page"
                    );

                }

            }
        );

    }


    /* =========================================================
       RESTORE SIDEBAR STATE
    ========================================================= */

    function restoreState() {

        const saved =
            localStorage.getItem(
                STORAGE_KEY
            );


        setCollapsed(
            saved === "true",
            false
        );

    }


    /* =========================================================
       RESPONSIVE RESIZE
    ========================================================= */

    function handleResize() {

        const elements = getElements();

        if (!elements) {

            return;

        }


        if (isMobile()) {

            /*
             * Mobile uses drawer mode.
             * Do not keep desktop collapsed state.
             */

            elements.layout.classList.remove(
                "sidebar-collapsed"
            );


            closeMobileSidebar();

        }
        else {

            /*
             * Return to normal desktop layout.
             */

            closeMobileSidebar();

            restoreState();

        }

    }


    /* =========================================================
       INITIALIZE
    ========================================================= */

    function init() {

        const elements = getElements();

        if (!elements) {

            return;

        }


        /*
         * Restore saved desktop state.
         */

        restoreState();


        /*
         * Highlight current page.
         */

        setActiveLink();


        /* -----------------------------------------
           Desktop collapse
        ----------------------------------------- */

        if (elements.collapseButton) {

            elements.collapseButton.addEventListener(
                "click",
                function () {

                    if (isMobile()) {

                        return;

                    }


                    const collapsed =
                        elements.layout.classList.contains(
                            "sidebar-collapsed"
                        );


                    setCollapsed(
                        !collapsed
                    );

                }
            );

        }


        /* -----------------------------------------
           Mobile hamburger
        ----------------------------------------- */

        if (elements.mobileButton) {

            elements.mobileButton.addEventListener(
                "click",
                function () {

                    if (!isMobile()) {

                        return;

                    }


                    const opened =
                        elements.layout.classList.contains(
                            "sidebar-mobile-open"
                        );


                    if (opened) {

                        closeMobileSidebar();

                    }
                    else {

                        openMobileSidebar();

                    }

                }
            );

        }


        /* -----------------------------------------
           Mobile backdrop
        ----------------------------------------- */

        if (elements.backdrop) {

            elements.backdrop.addEventListener(
                "click",
                closeMobileSidebar
            );

        }


        /* -----------------------------------------
           Navigation click
        ----------------------------------------- */

        elements.links.forEach(
            function (link) {

                link.addEventListener(
                    "click",
                    function () {

                        /*
                         * Mobile drawer closes
                         * after navigation.
                         *
                         * Desktop stays exactly
                         * as the user left it.
                         */

                        if (isMobile()) {

                            closeMobileSidebar();

                        }

                    }
                );

            }
        );


        /* -----------------------------------------
           Escape closes mobile drawer
        ----------------------------------------- */

        document.addEventListener(
            "keydown",
            function (event) {

                if (
                    event.key === "Escape"
                    && isMobile()
                ) {

                    closeMobileSidebar();

                }

            }
        );


        /* -----------------------------------------
           Responsive resize
        ----------------------------------------- */

        window.addEventListener(
            "resize",
            handleResize
        );

    }


    /* =========================================================
       DOM READY
    ========================================================= */

    if (
        document.readyState === "loading"
    ) {

        document.addEventListener(
            "DOMContentLoaded",
            init,
            { once: true }
        );

    }
    else {

        init();

    }

})();