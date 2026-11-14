
"""
AETHER — Evaluation Page

Prepares symptom evaluation data for the shared core interface.
"""

from app.cores import evaluation
from app.engines.evaluation_engine import get_engine_status


def get_evaluation_page_data(selected_symptoms=None):

    status = evaluation.get_status()
    engine_status = get_engine_status()

    # The Evaluation Core returns a dictionary keyed by symptom ID.
    symptom_catalogue = evaluation.get_symptoms()
    symptoms = list(symptom_catalogue.values())

    # Run assessment only when symptoms have been submitted.
    assessment = None

    if selected_symptoms is not None:
        assessment = evaluation.evaluate_astronaut_symptoms(
            selected_symptoms
        )

    return {
        "page_title": "Evaluation Core",
        "page_description": (
            "Evaluate astronaut-reported symptoms against "
            "documented spaceflight health research."
        ),

        "core_status": status.get("status", "Unknown"),

        "metrics": [
            {
                "label": "Known Symptoms",
                "value": engine_status.get("symptoms_available", 0),
                "detail": "Symptoms in the evaluation catalogue"
            },
            {
                "label": "Research Associations",
                "value": engine_status.get("conditions_available", 0),
                "detail": "Conditions represented in the catalogue"
            },
            {
                "label": "Research Sources",
                "value": engine_status.get("sources_available", 0),
                "detail": "References supporting the catalogue"
            }
        ],

        "content_title": "Astronaut Symptom Evaluation",

        "content_description": (
            "Select symptoms reported by an astronaut. "
            "AETHER will identify documented associations "
            "and display the supporting research."
        ),

        "symptoms": symptoms,
        "assessment": assessment,

        "assessment_note": (
            "Results represent documented associations, not "
            "medical diagnoses, probabilities or confirmation "
            "of a condition."
        )
    }
