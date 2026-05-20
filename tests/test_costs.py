from backend.pipeline.openrouter import compute_cost

def test_mistral_cost():
    cost = compute_cost("mistralai/mistral-7b-instruct", input_tokens=1000, output_tokens=500)
    assert cost > 0
    assert cost < 0.01

def test_haiku_cost():
    cost = compute_cost("anthropic/claude-3-haiku-20240307", input_tokens=1000, output_tokens=500)
    assert cost > 0
    assert cost < 0.05

def test_unknown_model_cost():
    cost = compute_cost("unknown/model", input_tokens=1000, output_tokens=500)
    assert cost == 0.0

def test_zero_tokens():
    cost = compute_cost("mistralai/mistral-7b-instruct", input_tokens=0, output_tokens=0)
    assert cost == 0.0
