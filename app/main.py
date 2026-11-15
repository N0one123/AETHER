from contextlib import asynccontextmanager
import sqlite3
from urllib.parse import parse_qs
from fastapi.responses import RedirectResponse
from fastapi import FastAPI, Request, Form
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates


from app.cores import astronaut
from app.cores import evaluation
from app.cores import tracking
from app.cores import health
from app.cores import emergency_response
from app.services.dashboard import get_dashboard_data
from app.services.astronaut_page import get_astronaut_page_data
from app.services.tracking_page import get_tracking_page_data
from app.services.evaluation_page import get_evaluation_page_data
from app.services.health_page import get_health_page_data
from app.services.emergency_page import get_emergency_page_data
from app.services import radiation
from app.database.schema import initialise_database


@asynccontextmanager
async def lifespan(_app):
    initialise_database()
    yield

app = FastAPI(
    title="AETHER",
    description="Astronaut Evaluation Tracking Health and Emergency Response",
    version="0.1.0",
    lifespan=lifespan
)

cores = [
    astronaut,
    evaluation,
    tracking,
    health,
    emergency_response
]

templates = Jinja2Templates(directory="app/templates")

app.mount(
    "/static",
    StaticFiles(directory="app/static"),
    name="static"
)


@app.get("/")
def home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "active_page": "dashboard",
            "dashboard_data": get_dashboard_data()
        }
    )

@app.get("/astronauts")
def astronauts_page(request: Request):
    data = get_astronaut_page_data()

    messages = {
        "registered": "Astronaut registered successfully.",
        "updated": "Astronaut details updated successfully.",
        "deleted": "Astronaut removed successfully.",
        "duplicate": "That astronaut ID already exists.",
        "invalid": "Astronaut ID and name are required.",
        "invalid_update": "Astronaut ID and status are required.",
        "not_found": "Astronaut not found. Refresh the page and try again.",
        "error": "Astronaut operation failed. Please try again."
    }

    data["page_message"] = messages.get(
        request.query_params.get("message")
    )

    return templates.TemplateResponse(
        request=request,
        name="core_page.html",
        context={
            "active_page": "astronauts",
            **data
        }
    )


@app.post("/astronauts/register")
async def register_astronaut_route(request: Request):
    form = parse_qs((await request.body()).decode())

    astronaut_id = form.get("astronaut_id", [""])[0].strip()
    name = form.get("name", [""])[0].strip()
    mission = form.get("mission", [""])[0].strip() or None

    try:
        astronaut.register_astronaut(
            astronaut_id=astronaut_id,
            name=name,
            mission=mission
        )
        message = "registered"

    except ValueError:
        message = "invalid"

    except sqlite3.IntegrityError:
        message = "duplicate"

    except Exception:
        message = "error"

    return RedirectResponse(
        url=f"/astronauts?message={message}",
        status_code=303
    )


@app.post("/astronauts/update")
def update_astronaut_route(
    astronaut_id: str = Form(...),
    mission: str = Form(""),
    status: str = Form(...)
):
    astronaut_id = astronaut_id.strip()
    mission = mission.strip() or None
    status = status.strip()

    if not astronaut_id or not status:
        return RedirectResponse(
            url="/astronauts?message=invalid_update",
            status_code=303
        )

    try:
        astronaut.update_astronaut(
            astronaut_id,
            mission=mission,
            status=status
        )
        message = "updated"

    except ValueError:
        message = "not_found"

    except Exception as error:
        print("ASTRONAUT UPDATE ERROR:", repr(error))
        message = "error"

    return RedirectResponse(
        url=f"/astronauts?message={message}",
        status_code=303
    )


@app.post("/astronauts/delete")
def delete_astronaut_route(astronaut_id: str = Form(...)):
    astronaut_id = astronaut_id.strip()

    if not astronaut_id:
        return RedirectResponse(
            url="/astronauts?message=invalid",
            status_code=303
        )

    try:
        message = (
            "deleted"
            if astronaut.remove_astronaut(astronaut_id)
            else "not_found"
        )

    except Exception as error:
        print("ASTRONAUT DELETION ERROR:", repr(error))
        message = "error"

    return RedirectResponse(
        url=f"/astronauts?message={message}",
        status_code=303
    )


@app.get("/evaluation")
def evaluation_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="core_page.html",
        context={"active_page": "evaluation",
                 **get_evaluation_page_data()}
    )

@app.post("/evaluation/assess")
def assess_evaluation_symptoms(
    request: Request,
    selected_symptoms: list[str] = Form(default=[])
):
    try:
        data = get_evaluation_page_data(
            selected_symptoms=selected_symptoms
        )

        return templates.TemplateResponse(
            request=request,
            name="core_page.html",
            context={
                "active_page": "evaluation",
                **data
            }
        )

    except Exception as error:
        print("EVALUATION ERROR:", repr(error))

        return templates.TemplateResponse(
            request=request,
            name="core_page.html",
            context={
                "active_page": "evaluation",
                **get_evaluation_page_data(),
                "error": "assessment_failed"
            },
            status_code=500
        )
    

@app.get("/tracking")
def tracking_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="core_page.html",
        context={
            "active_page": "tracking",
            **get_tracking_page_data()
        }
    )

@app.get("/health")
def health_page(request: Request):
    try:
        data = get_health_page_data()

        messages = {
            "measurement_recorded": "Measurement successfully recorded.",
            "health_alerts_resolved": "Measurement is back within its monitoring rule. Matching Health alerts were resolved.",
            "invalid_measurement": "Invalid measurement type.",
            "invalid_data": "Invalid data or astronaut ID. Check your entries.",
            "processing_failed": "Health processing failed. Check the system logs.",
            "rule_saved": "Monitoring rule saved successfully.",
            "rule_removed": "Monitoring rule removed.",
            "defaults_enabled": "Default monitoring rules enabled.",
            "defaults_disabled": "Default monitoring rules disabled. Existing custom rules were preserved.",
            "defaults_failed": "Could not update default monitoring rules. Check the system logs.",
            "invalid_rule": "Invalid monitoring rule. Check the boundaries and severity.",
            "rule_failed": "Monitoring rule operation failed. Check the system logs.",
            "measurement_recorded": "Measurement recorded. No abnormality detected.",
            "alert_created": "Abnormal measurement detected. Emergency alert created.",
            "alert_exists": "Abnormal measurement detected. An active alert already exists.",
            "alert_failed": "Measurement recorded, but Emergency Response could not create the alert.",
            "invalid_measurement": "Invalid measurement or astronaut ID.",
            "record_failed": "Could not process the measurement. Check the application logs."
        }

        return templates.TemplateResponse(
            request=request,
            name="core_page.html",
            context={
                "active_page": "health",
                "page_message": messages.get(
                    request.query_params.get("message")
                ),
                **data
            }
        )

    except Exception as error:
        import traceback

        traceback.print_exc()

        return {
            "error": str(error),
            "type": type(error).__name__
        }

@app.post("/health/record-measurement")
def record_health_measurement(
    astronaut_id: str = Form(...),
    measurement: str = Form(...),
    value: float = Form(...)
):
    units = {
        "heart_rate": "bpm",
        "blood_oxygen": "%",
        "body_temperature": "°C",
        "respiratory_rate": "breaths/min",
        "systolic_blood_pressure": "mmHg",
        "diastolic_blood_pressure": "mmHg"
    }

    astronaut_id = astronaut_id.strip()
    measurement = measurement.strip().lower()

    if measurement not in units:
        return RedirectResponse(
            url="/health?message=invalid_measurement",
            status_code=303
        )

    try:
        result = health.process_measurement({
            "astronaut_id": astronaut_id,
            "measurement": measurement,
            "value": value,
            "unit": units[measurement],
            "source": "manual_entry",
            "simulated": False
        })

        evaluation = result["evaluation"]
        alert = result["alert"]

        if result["alert_error"]:
            print("HEALTH ALERT ERROR:", result["alert_error"])
            message = "alert_failed"

        elif evaluation["abnormal"] and alert and alert.get("created"):
            message = "alert_created"

        elif evaluation["abnormal"] and alert and alert.get("duplicate"):
            message = "alert_exists"

        elif evaluation["abnormal"]:
            message = "alert_failed"

        elif result["alert_error"]:
            print("HEALTH ALERT RESOLUTION ERROR:", result["alert_error"])
            message = "record_failed"

        elif result["resolved_alerts"]:
            message = "health_alerts_resolved"

        else:
            message = "measurement_recorded"

    except ValueError as error:
        print("HEALTH VALIDATION ERROR:", error)
        message = "invalid_measurement"

    except Exception as error:
        print("HEALTH PROCESSING ERROR:", repr(error))
        message = "record_failed"

    return RedirectResponse(
        url=f"/health?message={message}",
        status_code=303
    )

@app.post("/health/configure-rule")
def configure_health_rule(
    measurement: str = Form(...),
    minimum: float | None = Form(None),
    maximum: float | None = Form(None),
    severity: str = Form("medium"),
    description: str = Form(""),
    rule_id: str | None = Form(None)
):
    try:
        health.configure_monitoring_rule(
            measurement=measurement,
            minimum=minimum,
            maximum=maximum,
            severity=severity,
            description=description.strip(),
            rule_id=rule_id
        )

        return RedirectResponse(
            url="/health?message=rule_saved",
            status_code=303
        )

    except ValueError as error:
        print("HEALTH RULE VALIDATION ERROR:", str(error))

        return RedirectResponse(
            url="/health?message=invalid_rule",
            status_code=303
        )

    except Exception as error:
        print("HEALTH RULE ERROR:", repr(error))

        return RedirectResponse(
            url="/health?message=rule_failed",
            status_code=303
        )

@app.post("/health/remove-rule")
def remove_health_rule(
    rule_id: str = Form(...)
):
    try:
        removed = health.remove_monitoring_rule(rule_id)

        message = "rule_removed" if removed else "invalid_rule"

        return RedirectResponse(
            url=f"/health?message={message}",
            status_code=303
        )

    except Exception as error:
        print("HEALTH RULE REMOVAL ERROR:", repr(error))

        return RedirectResponse(
            url="/health?message=rule_failed",
            status_code=303
        )


@app.post("/health/default-rules")
def set_health_default_rules(enabled: str = Form(...)):
    if enabled not in {"true", "false"}:
        return RedirectResponse(
            url="/health?message=invalid_rule",
            status_code=303
        )

    should_enable = enabled == "true"

    try:
        health.set_default_monitoring_rules_enabled(should_enable)
        message = "defaults_enabled" if should_enable else "defaults_disabled"

        return RedirectResponse(
            url=f"/health?message={message}",
            status_code=303
        )

    except ValueError as error:
        print("HEALTH DEFAULT RULE VALIDATION ERROR:", str(error))
        return RedirectResponse(
            url="/health?message=invalid_rule",
            status_code=303
        )

    except Exception as error:
        print("HEALTH DEFAULT RULE ERROR:", repr(error))
        return RedirectResponse(
            url="/health?message=defaults_failed",
            status_code=303
        )


@app.get("/radiation")
def radiation_page(request: Request):
    data = radiation.get_radiation_page_data(
        selected_astronaut_id=request.query_params.get("astronaut_id")
    )
    messages = {
        "measurement_recorded": "Radiation dose reading recorded.",
        "alert_created": "Dose reading recorded and a radiation alert was created.",
        "alert_failed": (
            "Dose reading was recorded, but Emergency Response could not "
            "create its alert."
        ),
        "invalid_measurement": (
            "Dose reading is invalid or the astronaut does not exist."
        ),
        "record_failed": "Could not record the dose reading. Check the application logs."
    }

    return templates.TemplateResponse(
        request=request,
        name="core_page.html",
        context={
            "active_page": "radiation",
            "page_message": messages.get(
                request.query_params.get("message")
            ),
            **data
        }
    )


@app.post("/radiation/record-measurement")
def record_radiation_measurement(
    astronaut_id: str = Form(...),
    dose_msv: float = Form(...),
    source: str = Form("manual_entry"),
    notes: str = Form("")
):
    try:
        result = radiation.process_measurement(
            astronaut_id=astronaut_id,
            dose_msv=dose_msv,
            source=source,
            notes=notes
        )

        if result["alert_error"]:
            print("RADIATION ALERT ERROR:", result["alert_error"])
            message = "alert_failed"
        elif result["alert"]:
            message = "alert_created"
        else:
            message = "measurement_recorded"

    except ValueError as error:
        print("RADIATION VALIDATION ERROR:", str(error))
        message = "invalid_measurement"

    except Exception as error:
        print("RADIATION PROCESSING ERROR:", repr(error))
        message = "record_failed"

    return RedirectResponse(
        url=f"/radiation?message={message}",
        status_code=303
    )


@app.get("/emergency-response")
def emergency_response_page(request: Request):
    data = get_emergency_page_data()

    incident_id = request.query_params.get("incident")

    selected_alert = (
        emergency_response.get_alert(incident_id)
        if incident_id
        else None
    )

    return templates.TemplateResponse(
        request=request,
        name="core_page.html",
        context={
            "active_page": "emergency",
            "error": request.query_params.get("error"),
            "success": request.query_params.get("success"),
            "selected_alert": selected_alert,
            **data
        }
    )

@app.post("/emergency-response/create-alert")
def create_emergency_alert(
    astronaut_id: str = Form(...),
    title: str = Form(...),
    description: str = Form(""),
    severity: str = Form("medium")
):
    astronaut_id = astronaut_id.strip()

    # Verify astronaut exists
    astronaut_record = astronaut.get_astronaut(astronaut_id)

    if not astronaut_record:
        return RedirectResponse(
            url="/emergency-response?error=astronaut_not_found",
            status_code=303
        )

    try:
        emergency_response.create_alert(
            astronaut_id=astronaut_id,
            title=title,
            description=description,
            severity=severity,
            source="manual"
        )

        return RedirectResponse(
            url="/emergency-response?success=alert_created",
            status_code=303
        )

    except Exception as error:
        print("ALERT CREATION ERROR:", repr(error))

        return RedirectResponse(
            url="/emergency-response?error=creation_failed",
            status_code=303
        )
    
@app.post("/emergency-response/resolve-alert")
def resolve_emergency_alert(alert_id: str = Form(...)):
    try:
        resolved = emergency_response.resolve_alert(alert_id)

        if resolved:
            return RedirectResponse(
                url="/emergency-response?success=alert_resolved",
                status_code=303
            )

        return RedirectResponse(
            url="/emergency-response?error=resolve_failed",
            status_code=303
        )

    except Exception as error:
        print("ALERT RESOLUTION ERROR:", repr(error))

        return RedirectResponse(
            url="/emergency-response?error=resolve_failed",
            status_code=303
        )


@app.get("/api/status")
def system_status():
    core_statuses = []

    for core in cores:
        try:
            core_statuses.append(core.get_status())

        except Exception as error:
            core_statuses.append({
                "id": core.__name__.split(".")[-1],
                "name": "Unknown",
                "status": "Error",
                "error": str(error)
            })

    return {
        "system": "AETHER",
        "total_cores": len(cores),
        "cores": core_statuses
    }


@app.get("/api/dashboard")
def dashboard_api():
    return get_dashboard_data()
