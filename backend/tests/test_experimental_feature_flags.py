import os
import pytest
from backend.app.core.feature_flags import is_feature_enabled, get_all_flags, DEFAULT_FEATURE_FLAGS

def test_default_feature_flags_all_disabled():
    flags = get_all_flags()
    for flag, enabled in flags.items():
        assert enabled is False, f"Flag {flag} should be disabled by default"

def test_env_var_override(monkeypatch):
    flag_name = "ENABLE_PRECIPITATION_SPECIALIST"
    assert is_feature_enabled(flag_name) is False

    monkeypatch.setenv(flag_name, "true")
    assert is_feature_enabled(flag_name) is True

    monkeypatch.setenv(flag_name, "0")
    assert is_feature_enabled(flag_name) is False

def test_master_experimental_switch(monkeypatch):
    assert is_feature_enabled("ENABLE_CYCLONE_SPECIALIST") is False
    monkeypatch.setenv("ENABLE_EXPERIMENTAL_SPECIALISTS", "true")
    assert is_feature_enabled("ENABLE_CYCLONE_SPECIALIST") is True
    assert is_feature_enabled("ENABLE_HEATWAVE_SPECIALIST") is True
