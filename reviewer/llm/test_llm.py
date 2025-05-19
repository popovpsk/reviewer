import pytest

from . import llm

@pytest.mark.skip("real llm required")
def test_generate():
    response = llm.LLM().generate("test", "write quick sort")
    print(response)

