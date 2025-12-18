import logging
import json

from datetime import date
from dataclasses import dataclass
from collections import defaultdict

import httpx

from django.conf import settings

from .models import DGCResult, Observation
from .crypto import encrypt_str, decrypt_str


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


def calculate_dgc_results_for_reference(date_of_birth, sex, child_f, reference, observations):
    observations_by_type = defaultdict(list)

    for obs in observations:
        observations_by_type[obs.observation_type].append(obs)
    
    for observation_type_code, obs_list in observations_by_type.items():
        dgc_observations = []
        for obs in obs_list:
            observation_date = date.fromisoformat(decrypt_str(child_f, obs.encrypted_observation_date))
            dgc_observations.append(DGCObservation(
                observation_date=observation_date,
                observation_value=float(obs.observation_value)
            ))

        dgc_results = call_bulk_dgc_api(
            reference=reference,
            date_of_birth=date_of_birth,
            sex_code=sex,
            observation_type_code=observation_type_code,
            observations=dgc_observations
        )

        for (obs, dgc_obs, dgc_result) in zip(obs_list, dgc_observations, dgc_results['results']):
            DGCResult.objects.update_or_create(
                observation=obs,
                reference=reference,
                defaults={
                    'encrypted_dgc_api_result': encrypt_str(child_f, json.dumps(dgc_result)),
                    'corrected_sds': dgc_result['measurement_calculated_values']['corrected_sds'],
                    'corrected_centile': dgc_result['measurement_calculated_values']['corrected_centile'],
                    'chronological_sds': dgc_result['measurement_calculated_values']['chronological_sds'],
                    'chronological_centile': dgc_result['measurement_calculated_values']['chronological_centile']
                }
            )


def recalculate_dgc_results(date_of_birth, child, child_f):
    observations = Observation.objects.filter(
        child=child,
    )

    references = DGCResult.objects.filter(
        observation__in=observations
    ).values_list('reference', flat=True).distinct()

    for reference in references:
        calculate_dgc_results_for_reference(
            date_of_birth=date_of_birth,
            sex=child.sex,
            child_f=child_f,
            reference=reference,
            observations=observations
        )