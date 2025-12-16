import logging

from datetime import date
from dataclasses import dataclass

import httpx

from django.conf import settings


logger = logging.getLogger(__name__)


@dataclass
class DGCObservation:
    observation_date: date
    observation_value: float


# TODO MRB: gestation (https://github.com/rcpch/dgc-app-backend/issues/15)
def call_bulk_dgc_api(reference: str, date_of_birth: date, sex_code: int, observation_type_code: int, observations: list[DGCObservation]) -> dict:    
    dgc_api_url = f"{settings.DGC_API_URL}/{reference}/bulk-calculation"
    dgc_api_key = settings.DGC_API_KEY

    headers = {
        "Subscription-Key": dgc_api_key,
        "Content-Type": "application/json"
    }

    match sex_code:
        case 0:
            sex = "male"
        case 1:
            sex = "female"
        case _:
            raise ValueError("Invalid sex code")
    
    match observation_type_code:
        case 1:
            observation_type = "height"
        case 2:
            observation_type = "weight"
        case 3:
            observation_type = "ofc"
        case _:
            raise ValueError("Invalid observation type code")

    observation_params = []
    for obs in observations:
        observation_params.append({
            "observation_date": obs.observation_date.isoformat(),
            "observation_value": obs.observation_value
        })

    params = {
        "birth_date": date_of_birth.isoformat(),
        "sex": sex,
        "measurement_method": observation_type,
        "observations": observation_params
    }

    response = httpx.post(dgc_api_url, headers=headers, json=params)
    response.raise_for_status()

    return response.json()