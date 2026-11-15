# **AETHER — Astronaut Evaluation Tracking Health and Emergency Response**

### **About the Project**

AETHER (Astronaut Evaluation Tracking Health and Emergency Response) is a web-based astronaut health-monitoring and mission-support platform developed by Team Apogee for the NASA International Space Apps Challenge.

The platform aims to help astronauts and researchers monitor astronaut health, evaluate reported symptoms, analyse historical measurements, and manage potential health-related emergencies through a unified mission-control interface.

AETHER is designed around five independent core systems:

**1. Astronaut Core**

Manages astronaut profiles, crew information, mission assignments, and astronaut records.

**2. Evaluation Core**

Evaluates astronaut-reported symptoms against a research-informed catalogue of spaceflight-related health conditions. It identifies possible associations, provides supporting research sources, and displays relevant clinical observations and limitations. Its results are informational and do not constitute medical diagnoses.

**3. Tracking Core**

Records and analyses historical astronaut measurements to help identify patterns and changes over time. It is designed to work with recorded, non-simulated measurements.

**4. Health Core**

Monitors astronaut health measurements, identifies abnormal readings using monitoring rules, and supports both real/manual and simulated demonstration data. Simulated data is clearly distinguished from actual measurements.

**5. Emergency Response Core**

Manages emergency alerts, tracks their severity and status, and maintains incident records. It allows active alerts to be monitored and resolved incidents to remain available for historical reference.

### **Website Features**

AETHER provides a central Mission Control dashboard with an overview of registered astronauts, active alerts, recorded measurements, and core-system statuses.

Its dark mission-control interface provides access to the individual core systems through a navigation sidebar.

The website includes:

- Astronaut profile management.
- Symptom evaluation with research references.
- Historical measurement tracking.
- Health monitoring and measurement history.
- Emergency alert creation and management.
- Simulated data for demonstrations.
- Core-system status monitoring.

### **Technology Used**

AETHER is developed primarily using Python.

- **Python:** Application logic and backend processing.
- **FastAPI:** Web framework and application routing.
- **Uvicorn:** ASGI server.
- **Jinja2:** Dynamic HTML rendering.
- **Starlette:** Web application toolkit.
- **Pydantic:** Data validation.
- **python-multipart:** Form submission handling.
- **SQLite:** Persistent data storage.
- **HTML and CSS:** Website structure and styling.

### **Installation and Execution**

**Requirements:** Python 3.10 or newer and pip.

Clone the repo:

```
git clone https://github.com/N0one123/AETHER.git

```
Please ensure that git is installed: https://git-scm.com/install/

Enter the repo:

```
cd AETHER
```

Install the required dependencies:

```
pip install fastapi uvicorn jinja2 starlette pydantic python-multipart
```

Start the application:

```
python -m uvicorn app.main:app --reload
```

Once the server starts, open the following address in a web browser:

`http://127.0.0.1:8000`


### **Research and Scientific References**

AETHER's health-monitoring and evaluation concepts are informed by NASA research resources, including:

1. NASA — [The Human Body in Space](https://www.nasa.gov/humans-in-space/the-human-body-in-space/)
2. NASA — [Space Adaptation Sickness: NASA-STD-3001 Medical Technical Brief](https://www.nasa.gov/wp-content/uploads/2025/09/ochmo-mtb-004-space-adaptation-sickness-sas.pdf)
3. NASA — [Open Science Data Repository](https://osdr.nasa.gov/bio/repo/)

These resources provide scientific context for understanding physiological changes, health concerns, and biological research associated with human spaceflight.

### **Important Disclaimer**

AETHER is an independent student-developed prototype intended for educational, research, and demonstration purposes. It is not a certified medical device and does not replace professional medical assessment or official spacecraft health-monitoring systems.

Simulated measurements are intended exclusively for demonstrations and must not be interpreted as actual astronaut health data.

### **Acknowledgements**

Developed by **Team Apogeee** for the NASA International Space Apps Challenge.

NASA research resources and the open-source software packages used in the project are acknowledged for their respective contributions.

NASA is not affiliated with, sponsoring, or endorsing AETHER.
Future Sim Lab integrations should set both `simulated=1` and
`source="sim_lab"`.
