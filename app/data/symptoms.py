
"""
AETHER — NASA-Informed Evaluation Catalogue

Organises documented spaceflight health concerns,
associated astronaut-reported symptoms, clinical observations,
and research indicators.

IMPORTANT:
- This catalogue supports educational health assessment.
- It does not diagnose medical conditions.
- Symptom associations are not proof of a condition.
- Clinical observations are not ordinary self-reported symptoms.
- Research indicators require appropriate measurements or testing.
"""

# ---------------------------------------------------------
# RESEARCH SOURCES
# ---------------------------------------------------------

NASA_SOURCES = {

    "human_body_in_space": {
        "name": "NASA — The Human Body in Space",
        "url": (
            "https://www.nasa.gov/humans-in-space/"
            "the-human-body-in-space/"
        ),
        "type": "NASA primary source",
        "supports": [
            "fluid redistribution",
            "musculoskeletal changes",
            "vision changes",
            "sleep and physiological adaptation",
        ],
    },

    "space_adaptation_sickness": {
        "name": "NASA — Space Adaptation Sickness Technical Brief",
        "url": (
            "https://www.nasa.gov/wp-content/uploads/2025/09/"
            "ochmo-mtb-004-space-adaptation-sickness-sas.pdf"
        ),
        "type": "NASA technical brief",
        "supports": [
            "space adaptation sickness",
            "nausea",
            "vomiting",
            "malaise",
            "disorientation",
            "appetite changes",
            "concentration changes",
        ],
    },

    "sans_technical_brief": {
        "name": "NASA — SANS Technical Brief",
        "url": (
            "https://www.nasa.gov/wp-content/uploads/2024/02/"
            "ochmo-mtb-001-sans.pdf"
        ),
        "type": "NASA technical brief",
        "supports": [
            "SANS clinical observations",
            "ocular imaging",
            "optic disc edema",
            "globe flattening",
            "retinal and chorioretinal folds",
        ],
    },

    "sans_risk": {
        "name": "NASA — Risk of Spaceflight Associated Neuro-ocular Syndrome",
        "url": (
            "https://www.nasa.gov/reference/"
            "risk-of-spaceflight-associated-neuro-ocular-syndrome-sans/"
        ),
        "type": "NASA research source",
        "supports": [
            "SANS",
            "fluid shifts",
            "visual changes",
        ],
    },

    "sensorimotor_risk": {
        "name": "NASA — Sensorimotor Risk",
        "url": (
            "https://www.nasa.gov/directorates/esdmd/hhp/"
            "sensorimotor-risk/"
        ),
        "type": "NASA research source",
        "supports": [
            "motion sickness",
            "spatial disorientation",
            "postural control",
            "locomotion",
            "fine motor coordination",
        ],
    },

    "sensorimotor_technical_brief": {
        "name": "NASA — Sensorimotor Overview Technical Brief",
        "url": (
            "https://www.nasa.gov/wp-content/uploads/2023/12/"
            "ochmo-tb-010-sensorimotor.pdf"
        ),
        "type": "NASA technical brief",
        "supports": [
            "sensorimotor adaptation",
            "vestibular changes",
            "balance",
            "coordination",
        ],
    },

    "sleep_risk": {
        "name": "NASA — Risk from Inadequate Sleep and Irregular Schedules",
        "url": (
            "https://www.nasa.gov/reference/"
            "risk-from-inadequate-sleep-and-irregular-schedules/"
        ),
        "type": "NASA research source",
        "supports": [
            "sleep disruption",
            "irregular schedules",
            "circadian changes",
            "reduced alertness",
        ],
    },

    "isolation_confinement": {
        "name": "NASA — Hazard: Isolation and Confinement",
        "url": (
            "https://www.nasa.gov/hrp/"
            "hazard-isolation-and-confinement/"
        ),
        "type": "NASA research source",
        "supports": [
            "isolation",
            "confinement",
            "behavioral health",
            "sleep and workload effects",
        ],
    },

    "risks_of_human_spaceflight": {
        "name": "NASA — Risks of Human Spaceflight",
        "url": "https://www.nasa.gov/hrp/risks/",
        "type": "NASA research overview",
        "supports": [
            "human spaceflight health risks",
            "sensorimotor changes",
            "musculoskeletal changes",
        ],
    },

    "human_system_risks": {
        "name": "NASA — Human System Risks",
        "url": "https://www.nasa.gov/hhp/human-system-risks/",
        "type": "NASA research catalogue",
        "supports": [
            "behavioral health",
            "sleep and circadian changes",
            "musculoskeletal risks",
            "sensorimotor risks",
        ],
    },

    "fundamentals_of_human_health": {
        "name": "NASA — Fundamentals of Human Health",
        "url": (
            "https://www.nasa.gov/reference/"
            "fundamentals-of-human-health/"
        ),
        "type": "NASA research reference",
        "supports": [
            "space adaptation sickness",
            "sensorimotor changes",
            "human physiological adaptation",
        ],
    },

    "spaceflight_review": {
        "name": "Spaceflight and Human Physiology Review",
        "url": (
            "https://pmc.ncbi.nlm.nih.gov/articles/PMC6239149/"
        ),
        "type": "Peer-reviewed secondary source",
        "supports": [
            "general spaceflight physiology",
        ],
    },

    "osdr_information": {
        "name": "NASA — Open Science Data Repository Information",
        "url": (
            "https://science.nasa.gov/biological-physical/data/osdr/"
        ),
        "type": "NASA data resource",
        "supports": [
            "biological and physiological research data discovery",
        ],
    },

    "osdr": {
        "name": "NASA Open Science Data Repository",
        "url": "https://osdr.nasa.gov/bio/repo/",
        "type": "NASA data repository",
        "supports": [
            "research dataset discovery",
        ],
    },

    "life_sciences": {
        "name": "NASA Life Sciences Portal",
        "url": "https://nlsp.nasa.gov/",
        "type": "NASA data resource",
        "supports": [
            "space life sciences research discovery",
        ],
    },
}


# ---------------------------------------------------------
# CONDITION CATALOGUE
# ---------------------------------------------------------

CONDITIONS = {

    # -----------------------------------------------------
    # 1. SPACE ADAPTATION SICKNESS
    # -----------------------------------------------------

    "space_motion_sickness": {

        "name": "Space Adaptation Sickness",
        "category": "Neurological and Vestibular",

        "description": (
            "A collection of symptoms associated with the "
            "body adapting to the altered gravity environment "
            "during spaceflight."
        ),

        "symptoms": [
            "nausea",
            "vomiting",
            "malaise",
            "sluggishness",
            "spatial_disorientation",
            "difficulty_concentrating",
            "stomach_awareness",
            "decreased_appetite",
        ],

        "clinical_observations": [
            "motion_sensitivity",
            "vestibular_adaptation_changes",
        ],

        "research_indicators": [
            "vestibular_testing",
            "sensorimotor_assessment",
        ],

        "sources": [
            "space_adaptation_sickness",
            "fundamentals_of_human_health",
            "sensorimotor_risk",
        ],

        "limitations": (
            "These symptoms are not unique to space adaptation "
            "sickness. Mission context and clinical assessment "
            "are necessary."
        ),
    },


    # -----------------------------------------------------
    # 2. SPACEFLIGHT-ASSOCIATED NEURO-OCULAR SYNDROME
    # -----------------------------------------------------

    "sans": {

        "name": "Spaceflight-Associated Neuro-ocular Syndrome",
        "category": "Ocular and Neurological",

        "description": (
            "A collection of eye and visual changes observed "
            "in some astronauts during and after spaceflight."
        ),

        "symptoms": [
            "blurred_vision",
            "difficulty_focusing",
            "visual_changes",
            "reduced_visual_clarity",
        ],

        "clinical_observations": [
            "optic_disc_edema",
            "globe_flattening",
            "retinal_folds",
            "chorioretinal_folds",
            "refractive_error_changes",
        ],

        "research_indicators": [
            "visual_acuity",
            "ocular_imaging",
            "optical_coherence_tomography",
            "refractive_error_measurements",
        ],

        "sources": [
            "sans_technical_brief",
            "sans_risk",
            "human_body_in_space",
        ],

        "limitations": (
            "Self-reported visual symptoms cannot establish "
            "SANS. Clinical eye examinations and appropriate "
            "imaging are required."
        ),
    },


    # -----------------------------------------------------
    # 3. FLUID REDISTRIBUTION
    # -----------------------------------------------------

    "fluid_redistribution": {

        "name": "Fluid Redistribution",
        "category": "Cardiovascular and Physiological",

        "description": (
            "Microgravity causes body fluids to redistribute "
            "towards the upper body and head."
        ),

        "symptoms": [
            "facial_fullness",
            "nasal_congestion",
            "feeling_of_swelling",
        ],

        "clinical_observations": [
            "facial_puffiness",
            "reduced_lower_body_volume",
        ],

        "research_indicators": [
            "body_fluid_distribution",
            "body_mass",
            "fluid_shift_measurements",
        ],

        "sources": [
            "human_body_in_space",
            "sans_risk",
        ],

        "limitations": (
            "Fluid redistribution is a physiological adaptation "
            "and does not necessarily indicate illness. "
            "Reported symptoms alone cannot establish its extent."
        ),
    },


    # -----------------------------------------------------
    # 4. SPACEFLIGHT-ASSOCIATED HEADACHES
    # -----------------------------------------------------

    "space_headaches": {

        "name": "Spaceflight-Associated Headaches",
        "category": "Neurological",

        "description": (
            "Headaches reported by astronauts during spaceflight."
        ),

        "symptoms": [
            "headache",
            "head_pressure",
            "head_pain",
        ],

        "clinical_observations": [],

        "research_indicators": [
            "headache_frequency",
            "headache_duration",
            "pain_intensity",
        ],

        "sources": [
            "spaceflight_review",
        ],

        "limitations": (
            "Headaches have many possible causes. The presence "
            "of a headache cannot independently establish a "
            "spaceflight-associated condition."
        ),
    },


    # -----------------------------------------------------
    # 5. MUSCULOSKELETAL CHANGES
    # -----------------------------------------------------

    "musculoskeletal_changes": {

        "name": "Musculoskeletal Changes",
        "category": "Musculoskeletal",

        "description": (
            "Changes in muscle and bone associated with reduced "
            "mechanical loading in microgravity."
        ),

        "symptoms": [
            "muscle_weakness",
            "muscle_fatigue",
            "reduced_endurance",
            "muscle_soreness",
            "back_discomfort",
        ],

        "clinical_observations": [
            "reduced_muscle_mass",
            "bone_density_changes",
            "reduced_muscle_strength",
        ],

        "research_indicators": [
            "bone_mineral_density",
            "muscle_mass",
            "muscle_strength",
            "physical_performance",
        ],

        "sources": [
            "human_body_in_space",
            "risks_of_human_spaceflight",
            "human_system_risks",
        ],

        "limitations": (
            "Bone and muscle changes may occur without noticeable "
            "symptoms. Objective measurements are required."
        ),
    },


    # -----------------------------------------------------
    # 6. NEUROVESTIBULAR ADAPTATION
    # -----------------------------------------------------

    "neurovestibular_changes": {

        "name": "Neurovestibular Adaptation",
        "category": "Neurological and Vestibular",

        "description": (
            "Changes in spatial orientation, balance and "
            "coordination associated with altered gravity."
        ),

        "symptoms": [
            "dizziness",
            "balance_difficulties",
            "spatial_disorientation",
            "coordination_difficulties",
            "hand_eye_coordination_difficulties",
        ],

        "clinical_observations": [
            "altered_postural_control",
            "altered_motor_coordination",
            "locomotion_difficulties",
        ],

        "research_indicators": [
            "balance_assessment",
            "coordination_assessment",
            "vestibular_testing",
            "sensorimotor_testing",
        ],

        "sources": [
            "sensorimotor_risk",
            "sensorimotor_technical_brief",
            "fundamentals_of_human_health",
        ],

        "limitations": (
            "These changes may vary between astronauts and "
            "across different mission phases."
        ),
    },


    # -----------------------------------------------------
    # 7. SLEEP AND CIRCADIAN CHANGES
    # -----------------------------------------------------

    "sleep_circadian_changes": {

        "name": "Sleep and Circadian Disruption",
        "category": "Psychological and Behavioural",

        "description": (
            "Changes in sleep patterns and circadian rhythms "
            "associated with spaceflight schedules, lighting "
            "and mission conditions."
        ),

        "symptoms": [
            "difficulty_falling_asleep",
            "frequent_waking",
            "sleep_disruption",
            "daytime_sleepiness",
            "fatigue",
            "reduced_alertness",
        ],

        "clinical_observations": [
            "altered_sleep_duration",
            "altered_sleep_timing",
        ],

        "research_indicators": [
            "sleep_duration",
            "sleep_quality",
            "sleep_timing",
            "activity_patterns",
            "light_exposure",
        ],

        "sources": [
            "sleep_risk",
            "human_system_risks",
            "isolation_confinement",
            "human_body_in_space",
        ],

        "limitations": (
            "Sleep changes may be influenced by schedules, "
            "lighting, workload and mission conditions."
        ),
    },


    # -----------------------------------------------------
    # 8. BEHAVIOURAL HEALTH CHANGES
    # -----------------------------------------------------

    "behavioral_health_changes": {

        "name": "Behavioural Health Changes",
        "category": "Psychological and Behavioural",

        "description": (
            "Behavioural and psychological changes that may "
            "be associated with isolation, confinement and "
            "mission demands."
        ),

        "symptoms": [
            "irritability",
            "difficulty_concentrating",
            "reduced_motivation",
            "mood_changes",
            "social_withdrawal",
        ],

        "clinical_observations": [],

        "research_indicators": [
            "mood_assessments",
            "cognitive_performance",
            "sleep_patterns",
            "behavioural_assessments",
        ],

        "sources": [
            "isolation_confinement",
            "human_system_risks",
        ],

        "limitations": (
            "These observations are nonspecific and should not "
            "be used to assign psychological diagnoses."
        ),
    },
}


# ---------------------------------------------------------
# RADIATION EXPOSURE
# ---------------------------------------------------------

# Radiation is assessed separately.
# Symptoms alone cannot establish radiation exposure.

RADIATION_INDICATORS = [

    "recorded_radiation_dose",
    "exposure_duration",
    "mission_location",
    "exposure_event",

]


# ---------------------------------------------------------
# CATALOGUE FUNCTIONS
# ---------------------------------------------------------

def get_all_conditions():
    """Return the complete condition catalogue."""

    return [
        {
            "id": condition_id,
            **condition,
        }
        for condition_id, condition in CONDITIONS.items()
    ]


def get_condition(condition_id):
    """Retrieve one condition by its identifier."""

    if not isinstance(condition_id, str):
        return None

    condition = CONDITIONS.get(condition_id)

    if condition is None:
        return None

    return {
        "id": condition_id,
        **condition,
    }


def get_all_symptoms():
    """
    Return unique reported symptoms and their associated
    catalogue conditions.
    """

    symptoms = {}

    for condition_id, condition in CONDITIONS.items():

        for symptom in condition["symptoms"]:

            if symptom not in symptoms:

                symptoms[symptom] = {
                    "id": symptom,
                    "name": symptom.replace("_", " ").title(),
                    "conditions": [],
                }

            if condition_id not in symptoms[symptom]["conditions"]:
                symptoms[symptom]["conditions"].append(condition_id)

    return list(symptoms.values())


def get_symptoms_by_condition(condition_id):
    """Return reported symptoms associated with one condition."""

    condition = CONDITIONS.get(condition_id)

    if condition is None:
        return []

    return [
        {
            "id": symptom,
            "name": symptom.replace("_", " ").title(),
        }
        for symptom in condition["symptoms"]
    ]


def search_symptoms(query):
    """Search reported symptoms by their names."""

    if not isinstance(query, str):
        return []

    query = query.strip().lower()

    if not query:
        return get_all_symptoms()

    return [
        symptom
        for symptom in get_all_symptoms()
        if (
            query in symptom["name"].lower()
            or query in symptom["id"].lower()
        )
    ]


def get_source(source_id):
    """Retrieve a research source by its identifier."""

    if not isinstance(source_id, str):
        return None

    return NASA_SOURCES.get(source_id)


def get_all_sources():
    """Return all registered research and data resources."""

    return [
        {
            "id": source_id,
            **source,
        }
        for source_id, source in NASA_SOURCES.items()
    ]


def get_radiation_indicators():
    """Return the separate radiation exposure indicators."""

    return list(RADIATION_INDICATORS)
