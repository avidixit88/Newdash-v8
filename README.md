# NextCure Signal Room v2.0

Backend-ready Streamlit rebuild focused on Michael’s actual target lanes:

- B7-H4 / VTCN1
- CDH6
- Alzheimer's / ApoE4
- Bone / Siglec-15

## What changed in v2.0

- Expanded line-of-therapy extraction beyond simple 1L/2L/3L labels.
- Added prior-therapy / patient-setting context: platinum-resistant, prior platinum, taxane, PARP/DDR, VEGF/bevacizumab, checkpoint/IO, and prior ADC exposure.
- Removed the combination extraction confidence chart from the UI because it was not executive-useful.
- Expanded target-specific biology and patient-selection signals.
- Added named partner-agent / biology-term chart.
- Added a planned/not-yet-recruiting registry mix chart and auditable planned-trials table.
- Cleaned forward catalyst date formatting so hover labels and axes do not show `00:00:00`.
- Moved dense legends to the right side of charts where they were crowding titles or dates.
- Preserved the one-button executive flow: `Run Analysis`.
- Preserved backend-ready structure: ingestion, normalization, analytics, charts, UI, config, tests.

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Architecture

- `app.py` — Streamlit interface
- `src/clinicaltrials_client.py` — ClinicalTrials.gov API ingestion boundary
- `src/normalization.py` — registry parsing, target-lane classification, phase cleanup, modality classification, therapy-signal extraction
- `src/analytics.py` — analysis bundle and rules-based signal feed
- `src/charts.py` — Plotly visual layer
- `src/ui.py` — reusable Streamlit UI components
- `src/config.py` — lane presets, aliases, classifiers, strategy rules
- `tests/` — sanity checks

Streamlit is the interface, not the brain. These layers can later move behind FastAPI/Postgres without rethinking the product logic.

## Interpretation notes

- **B7-H4 and CDH6** are treated as core oncology/ADC target lanes.
- **Alzheimer's/ApoE4 and Bone/Siglec-15** remain side-channel registry watch lanes and are intentionally excluded from the oncology ADC timeline.
- Line-of-therapy and prior-therapy context are derived from registry text because ClinicalTrials.gov does not provide them as universal structured fields.
- Planned trials are shown two ways: all planned/not-yet-recruiting records, and dated future-start events when the registry provides a future start date.
