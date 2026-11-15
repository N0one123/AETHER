
/* ==========================================
   AETHER — DASHBOARD REFRESH
========================================== */

const DASHBOARD_SVG_NS = "http://www.w3.org/2000/svg";

function dashboardSvgElement(name, attributes = {}, text = null) {
    const element = document.createElementNS(DASHBOARD_SVG_NS, name);
    Object.entries(attributes).forEach(([attribute, value]) => {
        element.setAttribute(attribute, value);
    });
    if (text !== null) element.textContent = text;
    return element;
}

function dashboardChartSvg(container, viewBox, label) {
    const svg = dashboardSvgElement("svg", {
        viewBox,
        role: "img",
        "aria-label": label,
        class: "dashboard-chart-svg",
        preserveAspectRatio: "none"
    });
    container.replaceChildren(svg);
    return svg;
}

function renderChartEmpty(container, message) {
    const empty = document.createElement("div");
    empty.className = "chart-empty";
    empty.textContent = message;
    container.replaceChildren(empty);
}

function renderHeartRateChart(points) {
    const container = document.getElementById("vitals-chart");
    if (!container) return;

    const validPoints = points.filter((point) => Number.isFinite(Number(point.value)));
    if (!validPoints.length) {
        renderChartEmpty(container, "No heart-rate measurements recorded");
        return;
    }

    const width = 600;
    const height = 220;
    const margin = { top: 16, right: 18, bottom: 46, left: 44 };
    const plotWidth = width - margin.left - margin.right;
    const plotHeight = height - margin.top - margin.bottom;
    const values = validPoints.map((point) => Number(point.value));
    const minimum = Math.floor((Math.min(...values) - 10) / 10) * 10;
    const maximum = Math.ceil((Math.max(...values) + 10) / 10) * 10;
    const range = Math.max(maximum - minimum, 20);
    const y = (value) => (
        margin.top + (maximum - value) / range * plotHeight
    );
    const x = (index) => (
        margin.left + (
            validPoints.length === 1
                ? plotWidth / 2
                : index / (validPoints.length - 1) * plotWidth
        )
    );
    const svg = dashboardChartSvg(
        container,
        `0 0 ${width} ${height}`,
        "Current heart rate by astronaut"
    );

    for (let tick = 0; tick <= 4; tick += 1) {
        const value = minimum + range * tick / 4;
        const yPosition = y(value);
        svg.append(
            dashboardSvgElement("line", {
                x1: margin.left,
                x2: width - margin.right,
                y1: yPosition,
                y2: yPosition,
                class: "dashboard-chart-gridline"
            }),
            dashboardSvgElement("text", {
                x: margin.left - 8,
                y: yPosition + 3,
                "text-anchor": "end",
                class: "dashboard-chart-axis-label"
            }, `${Math.round(value)}`)
        );
    }

    const path = validPoints.map((point, index) => (
        `${index ? "L" : "M"} ${x(index)} ${y(Number(point.value))}`
    )).join(" ");
    svg.append(dashboardSvgElement("path", {
        d: path,
        class: "dashboard-health-line"
    }));

    validPoints.forEach((point, index) => {
        const pointX = x(index);
        const pointY = y(Number(point.value));
        const circle = dashboardSvgElement("circle", {
            cx: pointX,
            cy: pointY,
            r: 5,
            class: "dashboard-health-point"
        });
        circle.append(
            dashboardSvgElement(
                "title",
                {},
                `${point.name}: ${point.value} ${point.unit || "bpm"}`
            )
        );
        svg.append(
            circle,
            dashboardSvgElement("text", {
                x: pointX,
                y: height - 19,
                "text-anchor": "middle",
                class: "dashboard-chart-axis-label"
            }, point.name.length > 12
                ? `${point.name.slice(0, 11)}…`
                : point.name)
        );
    });

    const caption = document.createElement("div");
    caption.className = "dashboard-chart-caption";
    caption.textContent = "Latest heart rate per astronaut · bpm";
    container.append(caption);
}

function renderRadiationChart(series) {
    const container = document.getElementById("radiation-chart");
    if (!container) return;

    const validSeries = series.filter((item) => item.actual.length);
    if (!validSeries.length) {
        renderChartEmpty(container, "No radiation measurements recorded");
        return;
    }

    const width = 600;
    const height = 220;
    const margin = { top: 16, right: 18, bottom: 42, left: 48 };
    const plotWidth = width - margin.left - margin.right;
    const plotHeight = height - margin.top - margin.bottom;
    const plottedSeries = validSeries.map((item) => ({
        ...item,
        actual: item.actual.map((point) => ({
            ...point,
            time: Date.parse(point.timestamp),
            value: Number(point.dose_msv)
        })),
        predicted: item.predicted.map((point) => ({
            ...point,
            time: Date.parse(point.timestamp),
            value: Number(point.dose_msv)
        }))
    })).filter((item) => (
        item.actual.every((point) => Number.isFinite(point.time) && Number.isFinite(point.value))
        && item.predicted.every((point) => Number.isFinite(point.time) && Number.isFinite(point.value))
    ));

    if (!plottedSeries.length) {
        renderChartEmpty(container, "Radiation chart data is unavailable");
        return;
    }

    const allPoints = plottedSeries.flatMap((item) => (
        [...item.actual, ...item.predicted]
    ));
    let minimumTime = Math.min(...allPoints.map((point) => point.time));
    let maximumTime = Math.max(...allPoints.map((point) => point.time));
    if (minimumTime === maximumTime) maximumTime = minimumTime + 1;
    const maximumDose = Math.max(...allPoints.map((point) => point.value));
    const yMaximum = maximumDose > 0 ? maximumDose * 1.12 : 1;
    const x = (time) => (
        margin.left + (time - minimumTime) / (maximumTime - minimumTime) * plotWidth
    );
    const y = (value) => (
        margin.top + (yMaximum - value) / yMaximum * plotHeight
    );
    const svg = dashboardChartSvg(
        container,
        `0 0 ${width} ${height}`,
        "Recorded and projected radiation dose by astronaut"
    );

    for (let tick = 0; tick <= 4; tick += 1) {
        const value = yMaximum * tick / 4;
        const yPosition = y(value);
        svg.append(
            dashboardSvgElement("line", {
                x1: margin.left,
                x2: width - margin.right,
                y1: yPosition,
                y2: yPosition,
                class: "dashboard-chart-gridline"
            }),
            dashboardSvgElement("text", {
                x: margin.left - 8,
                y: yPosition + 3,
                "text-anchor": "end",
                class: "dashboard-chart-axis-label"
            }, value.toPrecision(2))
        );
    }

    for (let tick = 0; tick <= 4; tick += 1) {
        const time = minimumTime + (
            (maximumTime - minimumTime) * tick / 4
        );
        const label = new Date(time).toLocaleDateString(undefined, {
            month: "short",
            year: "2-digit",
            timeZone: "UTC"
        });
        svg.append(dashboardSvgElement("text", {
            x: x(time),
            y: height - 12,
            "text-anchor": tick === 0
                ? "start"
                : tick === 4 ? "end" : "middle",
            class: "dashboard-chart-axis-label"
        }, label));
    }

    const colors = ["#5ee4ff", "#3ad6b4", "#ffc85c", "#ff9a4d", "#b69cff"];
    const legend = document.createElement("div");
    legend.className = "dashboard-chart-legend";

    plottedSeries.forEach((item, index) => {
        const color = colors[index % colors.length];
        const actualPath = item.actual.map((point, pointIndex) => (
            `${pointIndex ? "L" : "M"} ${x(point.time)} ${y(point.value)}`
        )).join(" ");
        svg.append(dashboardSvgElement("path", {
            d: actualPath,
            stroke: color,
            class: "dashboard-radiation-actual-line"
        }));

        const lastActual = item.actual[item.actual.length - 1];
        const forecastPoints = [lastActual, ...item.predicted];
        const forecastPath = forecastPoints.map((point, pointIndex) => (
            `${pointIndex ? "L" : "M"} ${x(point.time)} ${y(point.value)}`
        )).join(" ");
        svg.append(dashboardSvgElement("path", {
            d: forecastPath,
            stroke: color,
            class: "dashboard-radiation-predicted-line"
        }));

        item.actual.forEach((point) => {
            const circle = dashboardSvgElement("circle", {
                cx: x(point.time),
                cy: y(point.value),
                r: 3.5,
                fill: color,
                stroke: color,
                class: "dashboard-radiation-point"
            });
            circle.append(dashboardSvgElement(
                "title",
                {},
                `${item.name}: ${point.value} mSv · recorded`
            ));
            svg.append(circle);
        });

        item.predicted.forEach((point) => {
            const circle = dashboardSvgElement("circle", {
                cx: x(point.time),
                cy: y(point.value),
                r: 4,
                fill: "none",
                stroke: color,
                class: "dashboard-radiation-point"
            });
            circle.append(dashboardSvgElement(
                "title",
                {},
                `${item.name}: ${point.value} mSv · projected in ${point.months_ahead} months`
            ));
            svg.append(circle);
        });

        const legendItem = document.createElement("span");
        legendItem.className = "dashboard-chart-legend-name";
        const swatch = document.createElement("i");
        swatch.style.setProperty("--series-color", color);
        legendItem.append(swatch, document.createTextNode(item.name));
        legend.append(legendItem);
    });

    const key = document.createElement("div");
    key.className = "dashboard-chart-key";
    [
        ["is-actual", "Recorded"],
        ["is-predicted", "Projected"]
    ].forEach(([className, label]) => {
        const keyItem = document.createElement("span");
        const marker = document.createElement("i");
        marker.className = className;
        keyItem.append(marker, document.createTextNode(label));
        key.append(keyItem);
    });
    const caption = document.createElement("div");
    caption.className = "dashboard-chart-caption";
    caption.textContent = "Accumulated dose · mSv";
    container.append(legend, caption, key);
}

async function refreshDashboard() {
    const dashboard = document.querySelector(".dashboard");

    if (!dashboard) return;

    try {
        const response = await fetch("/api/dashboard");

        if (!response.ok) {
            throw new Error("Dashboard API request failed.");
        }

        const data = await response.json();
        renderHeartRateChart(data.heart_rate_chart || []);
        renderRadiationChart(data.radiation_chart || []);

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


/* ==========================================
   AETHER — SIMULATION LAB STATUS
========================================== */

(() => {
    const panel = document.querySelector("[data-simulation-status-url]");

    if (!panel) return;

    const runningLabel = panel.querySelector("[data-simulation-running]");
    const speedLabel = panel.querySelector("[data-simulation-speed]");
    const retentionLabel = panel.querySelector("[data-simulation-retention]");
    const timeLabel = panel.querySelector("[data-simulation-time]");
    const liveSpeedControl = panel.querySelector(
        "[data-simulation-speed-control]"
    );
    const liveSpeedValue = panel.querySelector(
        "[data-simulation-speed-value]"
    );
    const liveSpeedError = panel.querySelector(
        "[data-simulation-speed-error]"
    );
    const startSpeedControl = document.querySelector(
        "[data-simulation-start-speed]"
    );
    const startSpeedValue = document.querySelector(
        "[data-simulation-start-speed-value]"
    );

    const renderSpeed = (speed, updateStartControl = true) => {
        speedLabel.textContent =
            `Speed: ${speed}x (${speed} simulated seconds per real second)`;
        if (
            liveSpeedValue
            && document.activeElement !== liveSpeedControl
        ) {
            liveSpeedValue.textContent = `${speed}x`;
        }
        if (startSpeedValue && updateStartControl) {
            startSpeedValue.textContent =
                `${speed}x — ${speed} simulated seconds per real second`;
        }
    };

    const refreshSimulationStatus = async () => {
        try {
            const response = await fetch(panel.dataset.simulationStatusUrl);
            if (!response.ok) {
                throw new Error("Simulation status request failed.");
            }

            const status = await response.json();
            runningLabel.textContent = status.running ? "RUNNING" : "STOPPED";
            runningLabel.className = `health-rule-status ${
                status.running ? "is-enabled" : "is-disabled"
            }`;
            renderSpeed(
                status.speed,
                document.activeElement !== startSpeedControl
            );
            retentionLabel.textContent =
                `On stop: ${status.retention === "retain"
                    ? "keep generated history"
                    : "clear generated history"}`;
            timeLabel.textContent =
                `Simulated time: ${status.simulation_time || "Not started"}`;

            if (
                liveSpeedControl
                && document.activeElement !== liveSpeedControl
            ) {
                liveSpeedControl.value = status.speed;
            }

            const abnormalMeasurements = new Set(
                status.abnormal_measurements || []
            );
            Object.entries(status.current || {}).forEach(([measurement, value]) => {
                const card = panel.querySelector(
                    `[data-simulation-reading="${measurement}"]`
                );
                const reading = panel.querySelector(
                    `[data-simulation-reading="${measurement}"] strong`
                );
                if (card) {
                    card.classList.toggle(
                        "is-abnormal",
                        abnormalMeasurements.has(measurement)
                    );
                }
                if (reading) {
                    reading.textContent = `${value} ${reading.textContent.split(" ").slice(-1)[0]}`;
                }
            });

            const radiationCard = panel.querySelector(
                '[data-simulation-reading="radiation"]'
            );
            const radiation = panel.querySelector(
                '[data-simulation-reading="radiation"] strong'
            );
            if (radiationCard) {
                radiationCard.classList.toggle(
                    "is-abnormal",
                    Boolean(status.radiation_severity)
                );
            }
            if (radiation && status.current_dose_msv !== null) {
                radiation.textContent = `${Number(status.current_dose_msv).toFixed(4)} mSv`;
            }
        } catch (error) {
            console.error("AETHER Simulation Lab status update failed:", error);
        }
    };

    if (liveSpeedControl) {
        liveSpeedControl.addEventListener("input", () => {
            liveSpeedValue.textContent = `${liveSpeedControl.value}x`;
            liveSpeedError.textContent = "";
        });

        liveSpeedControl.addEventListener("change", async () => {
            liveSpeedControl.disabled = true;
            liveSpeedError.textContent = "";
            try {
                const response = await fetch("/api/simulation/speed", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/x-www-form-urlencoded"
                    },
                    body: new URLSearchParams({
                        speed: liveSpeedControl.value
                    })
                });
                const status = await response.json();
                if (!response.ok) {
                    throw new Error(status.detail || "Could not update speed.");
                }

                liveSpeedControl.value = status.speed;
                renderSpeed(status.speed);
            } catch (error) {
                liveSpeedError.textContent = error.message;
                console.error("AETHER Simulation Lab speed update failed:", error);
                refreshSimulationStatus();
            } finally {
                liveSpeedControl.disabled = false;
            }
        });
    }

    if (startSpeedControl) {
        startSpeedControl.addEventListener("input", () => {
            renderSpeed(startSpeedControl.value);
        });
    }

    refreshSimulationStatus();
    window.setInterval(refreshSimulationStatus, 1000);
})();
