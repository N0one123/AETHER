
from app.cores import astronaut


def get_astronaut_page_data():

    astronauts = astronaut.get_all_astronauts()
    status = astronaut.get_status()

    return {
        "page_title": "Astronaut Management",
        "page_description": "Manage astronaut profiles and crew records.",
        "core_status": status.get("status", "Unknown"),

        "metrics": [
            {
                "label": "Registered Astronauts",
                "value": len(astronauts),
                "detail": "Total crew records"
            }
        ],

        

        "astronauts": astronauts,
        "content_title": "Registered Crew",
        "content_description": "Astronaut records currently stored in AETHER."
    }
