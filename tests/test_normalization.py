from src.normalization import extract_indication_hint, clean_df
from src.sample_data import sample_trials_raw


def test_indication_classification():
    assert extract_indication_hint("platinum resistant ovarian cancer") == "Ovarian / Gynecologic"
    assert extract_indication_hint("Alzheimer Disease") == "Alzheimer's"
    assert extract_indication_hint("osteogenesis imperfecta") == "Bone Disease"


def test_sample_data_cleans():
    df = clean_df(sample_trials_raw())
    assert "target_lane" in df.columns
    assert "combo_category" in df.columns
    assert "lane_relevance_score" in df.columns
    assert "lane_specific_readout" in df.columns
    assert "line_of_therapy" in df.columns
    assert "line_of_therapy_evidence" in df.columns
    assert "prior_therapy_context" in df.columns
    assert "biology_signals" in df.columns
    assert len(df) >= 1
    assert df["lane_relevance_score"].between(0, 100).all()


def test_line_of_therapy_detection():
    df = clean_df(sample_trials_raw())
    assert df["line_of_therapy"].astype(str).str.contains("Relapsed|Line not specified|1L|2L|3L|4L", regex=True).any()


def test_modality_classification_present():
    df = clean_df(sample_trials_raw())
    assert "modality_class" in df.columns
    assert "adc_relevance" in df.columns
    assert df["modality_class"].notna().all()


def test_v20_signal_columns_populate():
    df = clean_df(sample_trials_raw())
    assert df["biology_signals"].astype(str).str.len().gt(0).all()
    assert df["prior_therapy_context"].astype(str).str.len().gt(0).all()
