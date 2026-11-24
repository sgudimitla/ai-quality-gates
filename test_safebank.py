"""DeepEval tests for the SafeBank bot: meaning-based correctness + faithfulness."""
import json
import time

import pytest
from deepeval import assert_test
from deepeval.metrics import FaithfulnessMetric, GEval
from deepeval.models import GeminiModel
from deepeval.test_case import LLMTestCase, SingleTurnParams
from google.genai import errors as genai_errors

from safebank_bot import answer

# The JUDGE. Use a DIFFERENT model from the bot if you can (Topic 5: no grading its own homework).
JUDGE_MODEL = "gemini-3.5-flash-lite"
judge = GeminiModel(model=JUDGE_MODEL, temperature=0)

PAUSE_SECONDS = 25        # free tier: 15 requests/minute per model
INFRA_RETRIES = 3         # tries before giving up on a busy API
INFRA_WAIT_SECONDS = 60   # wait between tries
INFRA_CODES = {429, 500, 502, 503, 504}

CASES = json.load(open("golden.json", encoding="utf-8"))

# Known issues are tracked, not hidden: they run, but don't block the build.
PARAMS = [
    pytest.param(c, id=c["id"], marks=pytest.mark.xfail(reason=c["known_issue"], strict=False))
    if c.get("known_issue") else pytest.param(c, id=c["id"])
    for c in CASES
]


def is_infra_error(e):
    """Busy/limited API or timeout: an ERROR, not a quality FAILURE."""
    if isinstance(e, genai_errors.APIError):
        return e.code in INFRA_CODES
    return isinstance(e, TimeoutError)


def with_infra_retry(fn, *args, **kwargs):
    """Retry busy-API errors; if they persist, mark the case INCONCLUSIVE (skipped), never PASS."""
    for attempt in range(1, INFRA_RETRIES + 1):
        try:
            return fn(*args, **kwargs)
        except Exception as e:
            if not is_infra_error(e):
                raise  # real failures (e.g. a low score) are reported as FAILED
            if attempt == INFRA_RETRIES:
                pytest.skip(f"INCONCLUSIVE (infra): {type(e).__name__} {getattr(e, 'code', '')}")
            time.sleep(INFRA_WAIT_SECONDS)


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
    result = with_infra_retry(answer, case["question"])
    test_case = LLMTestCase(
        input=case["question"],
        actual_output=result["answer"],
        expected_output=case["expected_output"],
        retrieval_context=result["context"],
    )
    metrics = [correctness_metric()]
    if result["context"]:  # faithfulness needs at least one retrieved chunk
        metrics.append(faithfulness_metric())
    time.sleep(PAUSE_SECONDS)
    with_infra_retry(assert_test, test_case, metrics, run_async=False)