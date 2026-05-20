from __future__ import annotations
from typing import Any, Dict, List
import pandas as pd
import requests
from .config import API_URL, PRESET_PAGE_SIZE
from .normalization import parse_study, clean_df
from .sample_data import sample_trials_raw


def fetch_registry_studies(queries: List[str], page_size: int = PRESET_PAGE_SIZE) -> pd.DataFrame:
    """Fetch, de-duplicate, and normalize ClinicalTrials.gov studies.

    Backend-ready boundary: this function is the only place the UI touches the
    public registry. Later this can be replaced by a FastAPI endpoint or a
    scheduled database-backed ingestion job without changing the Streamlit UI.
    """
    rows: List[Dict[str, Any]] = []
    seen = set()
    for query in queries:
        params = {"format": "json", "query.term": query, "pageSize": min(page_size, 100)}
        try:
            res = requests.get(API_URL, params=params, timeout=22)
            res.raise_for_status()
            payload = res.json()
            for study in payload.get("studies", []):
                row = parse_study(study, query)
                nct_id = row.get("nct_id")
                if nct_id and nct_id not in seen:
                    rows.append(row)
                    seen.add(nct_id)
        except Exception:
            continue
    if not rows:
        return clean_df(sample_trials_raw())
    return clean_df(pd.DataFrame(rows))
