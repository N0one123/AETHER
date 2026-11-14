
"""
AETHER — Evaluation Engine

Compares astronaut-reported symptoms against the
NASA-informed condition catalogue.

Responsibilities:
- Validate symptom selections.
- Identify associated conditions.
- Explain symptom matches.
- Retrieve supporting research sources.
- Report unmatched symptoms.
- Clearly communicate assessment limitations.

This engine does not provide medical diagnoses.
"""

from app.data.symptoms import (
    CONDITIONS,
    NASA_SOURCES,
    get_all_symptoms,
)


def normalize_symptom(symptom):
    """Convert a symptom input into its catalogue identifier."""

    if not isinstance(symptom, str):
        return None

    return symptom.strip().lower().replace(" ", "_")


def get_symptom_catalogue():
    """Build a lookup of all recognised symptom identifiers."""

    return {
        symptom["id"]: symptom
        for symptom in get_all_symptoms()
    }


def evaluate_symptoms(selected_symptoms):
    """
    Evaluate a collection of astronaut-reported symptoms.

    Args:
        selected_symptoms: A list of symptom identifiers or names.

    Returns:
        A structured assessment containing:
        - recognised symptoms
        - unrecognised inputs
        - associated conditions
        - matched symptoms
        - supporting research sources
        - assessment limitations
    """

    if not isinstance(selected_symptoms, (list, tuple, set)):
        raise TypeError(
            "Selected symptoms must be a list, tuple or set."
        )

    if not selected_symptoms:
        return {
            "status": "empty",
            "message": "No symptoms were selected.",
            "selected_symptoms": [],
            "unrecognised_symptoms": [],
            "matched_conditions": [],
            "unmatched_symptoms": [],
            "total_selected": 0,
            "total_matches": 0,
        }

    catalogue = get_symptom_catalogue()

    recognised = []
    unrecognised = []

    # Normalise and remove duplicate selections.

    for raw_symptom in selected_symptoms:

        symptom_id = normalize_symptom(raw_symptom)

        if not symptom_id:
            unrecognised.append(str(raw_symptom))
            continue

        if symptom_id not in catalogue:
            unrecognised.append(str(raw_symptom))
            continue

        if symptom_id not in recognised:
            recognised.append(symptom_id)

    if not recognised:
        return {
            "status": "invalid",
            "message": "No recognised symptoms were provided.",
            "selected_symptoms": [],
            "unrecognised_symptoms": unrecognised,
            "matched_conditions": [],
            "unmatched_symptoms": [],
            "total_selected": 0,
            "total_matches": 0,
        }

    matched_conditions = []
    matched_symptoms = set()

    # Compare selected symptoms against every condition.

    for condition_id, condition in CONDITIONS.items():

        condition_symptoms = set(condition["symptoms"])

        matches = [
            symptom
            for symptom in recognised
            if symptom in condition_symptoms
        ]

        if not matches:
            continue

        matched_symptoms.update(matches)

        # Retrieve source information.

        sources = []

        for source_id in condition.get("sources", []):

            source = NASA_SOURCES.get(source_id)

            if not source:
                continue

            sources.append({
                "id": source_id,
                "name": source["name"],
                "url": source["url"],
            })

        matched_conditions.append({
            "id": condition_id,
            "name": condition["name"],
            "category": condition["category"],
            "description": condition["description"],

            "matched_symptoms": [
                {
                    "id": symptom,
                    "name": symptom.replace("_", " ").title(),
                }
                for symptom in matches
            ],

            "matched_symptom_count": len(matches),

            "clinical_observations": (
                condition.get("clinical_observations", [])
            ),

            "research_indicators": (
                condition.get("research_indicators", [])
            ),

            "sources": sources,

            "limitations": condition.get(
                "limitations",
                "Further professional assessment is required."
            ),
        })

    # Sort by number of matching symptoms.
    # This is an ordering mechanism, NOT a probability score.

    matched_conditions.sort(
        key=lambda condition: condition["matched_symptom_count"],
        reverse=True,
    )

    unmatched_symptoms = [
        {
            "id": symptom,
            "name": symptom.replace("_", " ").title(),
        }
        for symptom in recognised
        if symptom not in matched_symptoms
    ]

    return {
        "status": (
            "complete"
            if matched_conditions
            else "no_matches"
        ),

        "message": (
            "Symptom assessment completed."
            if matched_conditions
            else "No associated conditions were found in the catalogue."
        ),

        "selected_symptoms": [
            {
                "id": symptom,
                "name": symptom.replace("_", " ").title(),
            }
            for symptom in recognised
        ],

        "unrecognised_symptoms": unrecognised,

        "matched_conditions": matched_conditions,

        "unmatched_symptoms": unmatched_symptoms,

        "total_selected": len(recognised),

        "total_matches": len(matched_conditions),

        "assessment_note": (
            "These results identify associations in the "
            "NASA-informed catalogue. They are not medical "
            "diagnoses, probabilities or confirmations of disease. "
            "Clinical assessment and additional evidence may be required."
        ),
    }


def get_engine_status():
    """Return information about the evaluation engine."""

    try:
        return {
            "status": "Operational",
            "conditions_available": len(CONDITIONS),
            "symptoms_available": len(get_all_symptoms()),
            "sources_available": len(NASA_SOURCES),
        }

    except Exception as error:
        return {
            "status": "Error",
            "error": str(error),
        }
