# AI Quality Gates: SafeBank RAG Bot

An end-to-end quality engineering pipeline for an LLM application: golden datasets,
LLM-as-judge evaluation, retrieval metrics, automated red-teaming, tracing, agent
trajectory checks and a CI quality gate.

The system under test is a small **RAG chatbot** for a fictional bank (SafeBank):
it searches 8 policy documents and answers with Gemini.

## Architecture

```
Question → Search (keyword retrieval, top-2 chunks) → Gemini (answers only from chunks) → Answer
              │                                          │
         RAGAS: context precision/recall          DeepEval: correctness + faithfulness
              └──────────── LangSmith: trace of every step ─────────────┘
```

## What is tested, and how

| Layer | Tool | Checks | API calls |
|---|---|---|---|
| Search | RAGAS (ID-based) | Context precision, context recall vs. labeled chunks | None |
| Answers | DeepEval + Gemini judge | Correctness (custom GEval rubric), faithfulness | Yes |
| Security | Promptfoo red team | Hijacking, hallucination, contracts, excessive agency, overreliance | Yes |
| Agent actions | Python rules on trajectories | Confirmation before risky actions, correct arguments, honest tool-error handling, step limits | None |
| Observability | LangSmith | Per-step traces: retrieved chunks, exact prompt, latency | n/a |
| Release | GitHub Actions | Two-stage gate: free search check first, then the golden set | Stage 2 only |

## Results

| Check | Result |
|---|---|
| Golden set, baseline | 8/10 |
| After one prompt fix | 9/10, no regressions; remaining failure is a tracked known issue |
| Search quality | Precision 0.56, recall 0.89 (the AI compensates for weak search) |
| Red team, run 1 | Reported 20% attack success → triage: all 3 were grader API errors (0 confirmed) |
| Red team, run 2 | 0/15 attacks succeeded, 0 errors |
| Agent trajectories | 4/4 critical failures caught (unconfirmed action, wrong card, claimed action with no tool call, success claimed after tool error) |

## Key findings

1. **Errors ≠ failures.** API 503/429 errors were repeatedly reported as quality failures by
   tools. The CI gate now has three outcomes: **passed**, **failed** (real quality issue)
   and **inconclusive** (infra), and never counts an untested case as a pass.
2. **Rule-based checks break on meaning.** `contains "closed"` failed a correct "No."
   An LLM judge fixed it; deterministic checks are kept for structure and safety rules.
3. **Measure search and generation separately.** 9/10 correct answers hid 56% retrieval
   precision. A better model would only mask this; the fix belongs in the search layer.
4. **Faithfulness alone passes useless answers.** "I don't know" is 100% faithful.
   Correctness and faithfulness are always paired.
5. **Every prompt change needs a full regression run.** One "use common sense" line fixed
   a refusal and introduced small unsupported inferences elsewhere.
6. **Tools find candidates; humans confirm findings.** Manual review of red-team output
   found leaked document IDs and raw markdown that screen readers would read aloud.

## Run it

```bash
pip install -r requirements.txt          # main environment
python safebank_bot.py "Is the branch open on the 2nd Saturday?"
python run_golden.py baseline            # quick rule-based scorecard
deepeval test run test_safebank.py       # LLM-judge evaluation
python eval_agent.py                     # agent trajectory checks
```
RAGAS runs in a separate environment (dependency conflict with DeepEval):
```bash
pip install -r requirements-ragas.txt
python eval_retrieval.py
```
Set `GOOGLE_API_KEY` (and optionally `LANGSMITH_*`) in a `.env` file. Never commit it.

## Known limitations

- The judge uses the same model as the bot (self-grading): a different judge model is planned.
- Free-tier API limits make runs slow and occasionally inconclusive.
- Red team covered 5 plugins with the basic strategy only; injection, PII and jailbreak strategies are not yet covered.
- Agent trajectories are simulated, not recorded from a live agent.
- G10 ("cash machine abroad") fails due to keyword search; tracked as a known issue.