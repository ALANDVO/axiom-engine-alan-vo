# Minimal test for probe scheduler
def test_run_probes_exists():
    from app.services.probe_scheduler import run_probes
    assert callable(run_probes)
