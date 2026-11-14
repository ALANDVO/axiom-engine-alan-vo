# Minimal test for model prober
def test_probe_model_exists():
    from app.services.model_prober import probe_model
    assert callable(probe_model)
