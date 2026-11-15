
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

RESEARCH_INDICATOR_LABELS = {
    "activity_patterns": "daily activity",
    "balance_assessment": "balance checks",
    "behavioural_assessments": "wellbeing checks",
    "body_fluid_distribution": "body fluid levels",
    "body_mass": "body weight",
    "bone_mineral_density": "bone strength",
    "cognitive_performance": "memory and focus",
    "coordination_assessment": "coordination checks",
    "fluid_shift_measurements": "fluid changes in the body",
    "headache_duration": "how long headaches last",
    "headache_frequency": "how often headaches happen",
    "light_exposure": "light levels",
    "mood_assessments": "mood checks",
    "muscle_mass": "muscle size",
    "muscle_strength": "muscle strength",
    "ocular_imaging": "eye scans",
    "optical_coherence_tomography": "detailed scans of the back of the eye",
    "pain_intensity": "pain levels",
    "physical_performance": "physical ability",
    "refractive_error_measurements": "eyesight and focusing",
    "sensorimotor_assessment": "balance and movement checks",
    "sensorimotor_testing": "balance and movement tests",
    "sleep_duration": "amount of sleep",
    "sleep_patterns": "sleep habits",
    "sleep_quality": "how restful sleep is",
    "sleep_timing": "sleep schedule",
    "vestibular_testing": "balance and inner-ear tests",
    "visual_acuity": "sharpness of vision",
}

CLINICAL_OBSERVATION_LABELS = {
    "altered_motor_coordination": "changes in coordination",
    "altered_postural_control": "changes in posture and balance",
    "altered_sleep_duration": "changes in sleep length",
    "altered_sleep_timing": "changes in sleep schedule",
    "bone_density_changes": "changes in bone strength",
    "chorioretinal_folds": "folds in tissue at the back of the eye",
    "facial_puffiness": "puffiness in the face",
    "globe_flattening": "changes in the shape of the eye",
    "locomotion_difficulties": "difficulty moving around",
    "motion_sensitivity": "sensitivity to movement",
    "optic_disc_edema": "swelling at the back of the eye",
    "reduced_lower_body_volume": "reduced fluid in the lower body",
    "reduced_muscle_mass": "loss of muscle",
    "reduced_muscle_strength": "reduced muscle strength",
    "refractive_error_changes": "changes in how the eyes focus",
    "retinal_folds": "folds in tissue at the back of the eye",
    "vestibular_adaptation_changes": (
        "balance changes as the body adjusts to weightlessness"
    ),
}


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


def _build_simulated_suggestions(condition, matched_symptoms):
    """Generate review suggestions from matched catalogue data."""

    symptom_names = ", ".join(
        symptom.replace("_", " ").title()
        for symptom in matched_symptoms
    )
    suggestions = [{
        "label": "Symptom tracking",
        "text": f"Track changes over time in: {symptom_names}.",
    }]

    research_indicators = condition.get("research_indicators", [])
    if research_indicators:
        indicator_names = ", ".join(
            RESEARCH_INDICATOR_LABELS.get(
                indicator,
                indicator.replace("_", " ")
            )
            for indicator in research_indicators
        )
        suggestions.append({
            "label": "Possible checks",
            "text": indicator_names,
        })

    clinical_observations = condition.get("clinical_observations", [])
    if clinical_observations:
        observation_names = ", ".join(
            CLINICAL_OBSERVATION_LABELS.get(
                observation,
                observation.replace("_", " ")
            )
            for observation in clinical_observations
        )
        suggestions.append({
            "label": "Things to notice",
            "text": observation_names,
        })

    return suggestions


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

            "simulated_suggestions": _build_simulated_suggestions(
                condition,
                matches
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
