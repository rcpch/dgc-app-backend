def call_dgc_api(observation_date: date) -> dict:
    dgc_api_url = settings.DGC_API_URL
    dgc_api_key = settings.DGC_API_KEY

    headers = {
        "Subscription-Key": dgc_api_key",
        "Content-Type": "application/json"
    }