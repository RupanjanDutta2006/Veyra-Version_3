"""Tests for Failure Memory episode builder and store (Gate 2 / Phase C)."""

from pathlib import Path
import pytest
from backend.app.builder2.failure_memory import FailureEpisode, FailureMemoryStore
from backend.app.contracts.hazard_contracts import HazardFamily


@pytest.fixture
def sample_episodes() -> list[FailureEpisode]:
    return [
        FailureEpisode(
            episode_id="EP_CYCLONE_01",
            hazard_family=HazardFamily.CYCLONE,
            issue_time="2023-06-10T00:00:00Z",
            location="Gujarat Coast",
            lead_hours=72,
            forecast_state_vector=[0.2, 0.5, 0.8, 0.9],
            observed_error=140.0,
            bust_label=1,
            severity="SEVERE",
            motif_id="MOTIF-TC-RECURVATURE",
        ),
        FailureEpisode(
            episode_id="EP_CYCLONE_02",
            hazard_family=HazardFamily.CYCLONE,
            issue_time="2024-05-24T00:00:00Z",
            location="Bengal Coast",
            lead_hours=72,
            forecast_state_vector=[0.25, 0.55, 0.82, 0.88],
            observed_error=115.0,
            bust_label=1,
            severity="MODERATE",
            motif_id="MOTIF-TC-RECURVATURE",
        ),
    ]


def test_failure_episode_creation_and_fields(sample_episodes: list[FailureEpisode]):
    """Verify episode schema correctly holds physical error and motif."""
    ep = sample_episodes[0]
    assert ep.episode_id == "EP_CYCLONE_01"
    assert ep.hazard_family == HazardFamily.CYCLONE
    assert ep.observed_error == 140.0
    assert ep.bust_label == 1
    assert ep.motif_id == "MOTIF-TC-RECURVATURE"


def test_store_disk_persistence(tmp_path: Path, sample_episodes: list[FailureEpisode]):
    """Verify saving and reloading episodes from disk preserves data."""
    store_file = tmp_path / "test_episodes.json"
    store = FailureMemoryStore(persistence_path=store_file)
    store.add_episodes(sample_episodes)
    store.save()

    assert store_file.is_file()

    # Load into new store instance
    loaded_store = FailureMemoryStore(persistence_path=store_file)
    assert loaded_store.count() == 2
    res = loaded_store.retrieve_analogs(
        query_vector=[0.22, 0.52, 0.81, 0.89],
        hazard=HazardFamily.CYCLONE,
        lead_hours=72,
    )
    assert res.sample_support_count == 2
    assert res.historical_failure_frequency == 1.0


def test_lead_window_filtering(sample_episodes: list[FailureEpisode]):
    """Verify lead_window_hours correctly filters out distant lead horizons."""
    store = FailureMemoryStore()
    store.add_episodes(sample_episodes)

    # Lead 72 vs Query 24 with window 24 -> diff is 48 > 24 -> 0 candidates
    res = store.retrieve_analogs(
        query_vector=[0.2, 0.5, 0.8, 0.9],
        hazard=HazardFamily.CYCLONE,
        lead_hours=24,
        lead_window_hours=24,
    )
    assert res.sample_support_count == 0
    assert res.historical_failure_frequency is None
    assert res.analog_uncertainty_score == 1.0
