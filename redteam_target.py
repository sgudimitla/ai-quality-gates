"""Lets Promptfoo send attack messages to the SafeBank bot."""
from safebank_bot import answer


def call_api(prompt, options, context):
    try:
        return {"output": answer(prompt)["answer"]}
    except Exception as e:  # API errors are reported as errors, not as failed tests
        return {"error": f"{type(e).__name__}: {e}"}