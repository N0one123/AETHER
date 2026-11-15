
/* ==========================================
   AETHER — DASHBOARD REFRESH
========================================== */

async function refreshDashboard() {
    const dashboard = document.querySelector(".dashboard");

    if (!dashboard) return;

    try {
        const response = await fetch("/api/dashboard");

        if (!response.ok) {
            throw new Error("Dashboard API request failed.");
        }

        const data = await response.json();

        // Update summary metrics
        const metricCards = document.querySelectorAll(".metric-card");

        data.metrics.forEach((metric, index) => {
            const card = metricCards[index];

            if (!card) return;

            const value = card.querySelector(".metric-value");
            const detail = card.querySelector(".metric-detail");

            if (value) value.textContent = metric.value;
            if (detail) detail.textContent = metric.detail;
        });

        // Update core statuses
        const coreCards = document.querySelectorAll(".core-card");

        data.cores.forEach((core, index) => {
            const card = coreCards[index];

            if (!card) return;

            const status = card.querySelector(".core-status");

            if (status) {
                status.textContent = core.status;
            }
        });

        // Update mission status
        const missionStatus = document.querySelector(".mission-status");

        if (missionStatus) {
            missionStatus.textContent = data.mission.status;
        }

    } catch (error) {
        console.error("AETHER dashboard refresh failed:", error);
    }
}


/* ==========================================
   AETHER — EMERGENCY RESPONSE
========================================== */

(() => {

    console.log("AETHER Emergency JS loaded");

    const createAlertButton = document.getElementById("create-alert");
    const viewActiveButton = document.getElementById("view-active");

    const alertForm = document.getElementById("create-alert-form");
    const cancelAlertButton = document.getElementById("cancel-create-alert");

    const activeIncidents = document.getElementById("active-incidents");
    const astronautInput = document.getElementById("alert-astronaut");


    // OPEN CREATE ALERT FORM
    if (createAlertButton && alertForm) {

        createAlertButton.addEventListener("click", () => {

            alertForm.hidden = false;

            alertForm.scrollIntoView({
                behavior: "smooth",
                block: "center"
            });

            astronautInput?.focus({
                preventScroll: true
            });

        });

    }


    // CLOSE CREATE ALERT FORM
    if (cancelAlertButton && alertForm) {

        cancelAlertButton.addEventListener("click", () => {

            alertForm.hidden = true;

        });

    }


    // VIEW ACTIVE INCIDENTS
    if (viewActiveButton && activeIncidents) {

        viewActiveButton.addEventListener("click", () => {

            activeIncidents.scrollIntoView({
                behavior: "smooth",
                block: "start"
            });

        });

    }


    // CLOSE FORM WITH ESCAPE
    document.addEventListener("keydown", (event) => {

        if (
            event.key === "Escape" &&
            alertForm &&
            !alertForm.hidden
        ) {
            alertForm.hidden = true;
        }

    });


    // REPORT MISSING ELEMENTS
    if (!createAlertButton) {
        console.warn("AETHER: Create Alert button not found.");
    }

    if (!alertForm) {
        console.warn("AETHER: Alert form not found.");
    }

})();


/* ==========================================
   AETHER — AUTOMATIC DASHBOARD UPDATES
========================================== */

refreshDashboard();

setInterval(refreshDashboard, 5000);


/* ==========================================
   AETHER — ASTRONAUT PROFILE EDITOR
========================================== */

(() => {
    const editor = document.getElementById("astronaut-editor");

    if (!editor) return;

    const name = document.getElementById("astronaut-editor-name");
    const mission = document.getElementById("astronaut-edit-mission");
    const status = document.getElementById("astronaut-edit-status");
    const editAstronautId = editor.querySelector("[data-edit-astronaut-id]");
    const deleteAstronautId = editor.querySelector("[data-delete-astronaut-id]");
    const deleteForm = editor.querySelector("[data-astronaut-delete-form]");

    document.querySelectorAll(".astronaut-edit-trigger").forEach((trigger) => {
        trigger.addEventListener("click", () => {
            const astronautName = trigger.dataset.astronautName;

            name.textContent = astronautName;
            mission.value = trigger.dataset.astronautMission;
            status.value = trigger.dataset.astronautStatus;
            editAstronautId.value = trigger.dataset.astronautId;
            deleteAstronautId.value = trigger.dataset.astronautId;
            deleteForm.dataset.astronautName = astronautName;

            editor.showModal();
            status.focus();
        });
    });

    editor.querySelectorAll("[data-close-astronaut-editor]").forEach((button) => {
        button.addEventListener("click", () => editor.close());
    });

    editor.addEventListener("click", (event) => {
        if (event.target === editor) editor.close();
    });

    deleteForm.addEventListener("submit", (event) => {
        const astronautName = deleteForm.dataset.astronautName;

        if (!window.confirm(`Delete ${astronautName} and all associated records? This cannot be undone.`)) {
            event.preventDefault();
        }
    });
})();


/* ==========================================
   AETHER — HEALTH MONITORING RULES
========================================== */

(() => {
    const cards = document.querySelectorAll("[data-health-rule-card]");

    if (!cards.length) return;

    const setExpanded = (card, expanded) => {
        const summary = card.querySelector("[data-health-rule-summary]");
        const details = card.querySelector(".health-rule-details");
        const title = card.querySelector(".health-rule-title");
        const fullTitle = title.title;
        const titleCharacters = Array.from(fullTitle);

        summary.setAttribute("aria-expanded", String(expanded));
        details.hidden = !expanded;
        card.classList.toggle("is-expanded", expanded);
        title.textContent = expanded || titleCharacters.length <= 11
            ? fullTitle
            : `${titleCharacters.slice(0, 10).join("")}...`;
    };

    cards.forEach((card) => {
        const summary = card.querySelector("[data-health-rule-summary]");
        const details = card.querySelector(".health-rule-details");
        const editToggle = card.querySelector("[data-health-rule-edit-toggle]");
        const editForm = card.querySelector(".health-rule-edit-form");
        const cancelEdit = card.querySelector("[data-health-rule-edit-cancel]");
        const title = card.querySelector(".health-rule-title");
        const titleCharacters = Array.from(title.title);

        title.textContent = titleCharacters.length <= 11
            ? title.title
            : `${titleCharacters.slice(0, 10).join("")}...`;

        summary.addEventListener("click", () => {
            const shouldExpand = summary.getAttribute("aria-expanded") !== "true";

            cards.forEach((otherCard) => {
                if (otherCard !== card) setExpanded(otherCard, false);
            });

            setExpanded(card, shouldExpand);
        });

        editToggle.addEventListener("click", () => {
            const editing = editToggle.getAttribute("aria-expanded") !== "true";
            editToggle.setAttribute("aria-expanded", String(editing));
            editToggle.textContent = editing ? "Close Editor" : "Edit";
            editForm.hidden = !editing;
        });

        cancelEdit.addEventListener("click", () => {
            editForm.reset();
            editForm.hidden = true;
            editToggle.setAttribute("aria-expanded", "false");
            editToggle.textContent = "Edit";
        });
    });
})();


/* ==========================================
   AETHER — RADIATION DOSE PROJECTION
========================================== */

(() => {
    const projection = document.getElementById("radiation-projection");

    if (!projection) return;

    const astronautSelect = projection.querySelector("[data-radiation-astronaut]");
    const horizon = projection.querySelector("[data-radiation-horizon]");
    const monthsLabel = projection.querySelector("[data-radiation-months]");
    const baselineLabel = projection.querySelector("[data-radiation-baseline]");
    const doseLabel = projection.querySelector("[data-radiation-projected-dose]");
    const severityLabel = projection.querySelector("[data-radiation-projected-severity]");

    if (
        !astronautSelect ||
        !horizon ||
        !monthsLabel ||
        !baselineLabel ||
        !doseLabel ||
        !severityLabel
    ) {
        if (!astronautSelect && !horizon) return;
        console.error("AETHER: Radiation projection controls are incomplete.");
        return;
    }

    const doseIncreasePerMonth = Number(projection.dataset.doseIncreasePerMonth);
    const maxMonths = Number(projection.dataset.maxMonths);
    const thresholds = {
        medium: Number(projection.dataset.thresholdMedium),
        high: Number(projection.dataset.thresholdHigh),
        critical: Number(projection.dataset.thresholdCritical)
    };
    const numberFormat = new Intl.NumberFormat(undefined, {
        maximumFractionDigits: 1
    });

    const updateProjection = () => {
        const selectedOption = astronautSelect.selectedOptions[0];
        const baseline = Number(selectedOption?.dataset.baseline);
        const months = Number(horizon.value);

        if (
            !Number.isFinite(doseIncreasePerMonth) ||
            !Number.isFinite(maxMonths) ||
            !Number.isFinite(baseline) ||
            !Number.isFinite(months) ||
            baseline < 0 ||
            months < 0 ||
            months > maxMonths ||
            !Object.values(thresholds).every(Number.isFinite)
        ) {
            console.error("AETHER: Radiation projection inputs are invalid.");
            return;
        }

        const projectedDose = baseline + months * doseIncreasePerMonth;
        let severity = null;

        if (projectedDose >= thresholds.critical) {
            severity = "critical";
        } else if (projectedDose >= thresholds.high) {
            severity = "high";
        } else if (projectedDose >= thresholds.medium) {
            severity = "medium";
        }

        baselineLabel.textContent = numberFormat.format(baseline);
        doseLabel.textContent = numberFormat.format(projectedDose);
        monthsLabel.textContent = months === 0
            ? "Present"
            : `${months} months ahead${months === 24 ? " (2 years)" : ""}`;

        severityLabel.className = "health-rule-severity";
        severityLabel.textContent = severity
            ? `${severity.toUpperCase()} (PROJECTED)`
            : "No alert projected";

        if (severity) {
            severityLabel.classList.add(`severity-tag-${severity}`);
        } else {
            severityLabel.classList.add("is-disabled");
        }
    };

    astronautSelect.addEventListener("change", updateProjection);
    horizon.addEventListener("input", updateProjection);
    updateProjection();
})();
