import os

# Provide a dummy API key for tests that import backend.config
# Real API calls are not made in unit tests
os.environ.setdefault("OPENROUTER_API_KEY", "test_key_for_unit_tests")
