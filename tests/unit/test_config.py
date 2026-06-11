"""Unit tests for config/enum parsing (P0.2 regressions)."""

import pytest

from app.core.enums import Environment


@pytest.mark.unit
class TestEnvironmentFromString:
    """Regression tests for P0.2 — Environment.from_string alias mapping."""

    @pytest.mark.parametrize(
        "value, expected",
        [
            ("local", Environment.LOCAL),
            ("LOCAL", Environment.LOCAL),
            ("dev", Environment.DEV),
            ("development", Environment.DEV),
            ("DEVELOPMENT", Environment.DEV),
            ("stage", Environment.STAGE),
            ("staging", Environment.STAGE),
            ("STAGING", Environment.STAGE),
            ("prod", Environment.PROD),
            ("production", Environment.PROD),
            ("PRODUCTION", Environment.PROD),
        ],
    )
    def test_valid_aliases(self, value: str, expected: Environment):
        assert Environment.from_string(value) == expected

    def test_invalid_value_raises(self):
        with pytest.raises(ValueError, match="Invalid environment"):
            Environment.from_string("unknown")

    def test_production_alias_does_not_crash(self):
        """Regression: k8s ConfigMap ENV=production must not CrashLoop the app."""
        result = Environment.from_string("production")
        assert result == Environment.PROD
