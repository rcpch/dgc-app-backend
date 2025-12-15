import logging

from datetime import date

import httpx

from django.conf import settings


logger = logging.getLogger(__name__)


# TODO MRB: gestation and reference (https://github.com/rcpch/dgc-app-backend/issues/15)
def call_dgc_api(date_of_birth: date, observation_date: date, sex_code: int, observation_type_code: int, observation_value: float) -> dict:    
    dgc_api_url = f"{settings.DGC_API_URL}/uk-who/calculation"
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

    params = {
        "birth_date": date_of_birth.isoformat(),
        "observation_date": observation_date.isoformat(),
        "sex": sex,
        "measurement_method": observation_type,
        "observation_value": observation_value
    }

    response = httpx.post(dgc_api_url, headers=headers, json=params)
    response.raise_for_status()

    return response.json()