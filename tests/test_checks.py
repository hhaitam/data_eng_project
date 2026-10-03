import pytest

from dvf_elt.quality.checks import run_all_checks

pytestmark = pytest.mark.integration

def test_silver_data_passes_all_quality_checks():
    results = run_all_checks()
    failed = [r for r in results if not r.passed]
    assert not failed, f"Quality checks failed: {failed}"