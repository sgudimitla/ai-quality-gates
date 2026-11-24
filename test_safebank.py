"""DeepEval tests for the SafeBank bot: meaning-based correctness + faithfulness."""
import json
import time

import pytest
from deepeval import assert_test
from deepeval.metrics import FaithfulnessMetric, GEval
from deepeval.models import GeminiModel
from deepeval.test_case import LLMTestCase, SingleTurnParams

from safebank_bot import answer

# The JUDGE. Use a DIFFERENT model from the bot if you can (Topic 5: no grading its own homework).
JUDGE_MODEL = "gemini-3.5-flash-lite"
judge = GeminiModel(model=JUDGE_MODEL, temperature=0)

CASES = json.load(open("golden.json", encoding="utf-8"))

# Known issues are tracked, not hidden: they run, but don't block the build.
PARAMS = [
    pytest.param(c, id=c["id"], marks=pytest.mark.xfail(reason=c["known_issue"], strict=False))
    if c.get("known_issue") else pytest.param(c, id=c["id"])
    for c in CASES
]


def correctness_metric():
    return GEval(
        name="Correctness",
        criteria=(
            "Does the actual output give the same facts as the expected output? "
            "Different wording or length is fine. "
            "If the expected output is 'I don't know', the actual output must also decline to answer. "
            "If the expected output has an answer, a refusal like 'I don't know' is incorrect."
        ),
        evaluation_params=[SingleTurnParams.INPUT, SingleTurnParams.ACTUAL_OUTPUT,
                           SingleTurnParams.EXPECTED_OUTPUT],
        model=judge, threshold=0.7, async_mode=False,
    )


def faithfulness_metric():
    return FaithfulnessMetric(model=judge, threshold=0.7, async_mode=False)


@pytest.mark.parametrize("case", PARAMS)
def test_golden(case):
    result = answer(case["question"])
    test_case = LLMTestCase(
        input=case["question"],
        actual_output=result["answer"],
        expected_output=case["expected_output"],
        retrieval_context=result["context"],
    )
    metrics = [correctness_metric()]
    if result["context"]:  # faithfulness needs at least one retrieved chunk
        metrics.append(faithfulness_metric())
    time.sleep(25)  # be gentle with the free tier
    assert_test(test_case, metrics, run_async=False)