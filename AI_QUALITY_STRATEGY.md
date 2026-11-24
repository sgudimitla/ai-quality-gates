# AI Quality Strategy (one page)

**Goal:** ship AI features that are correct, safe, accessible and affordable, and know it
with evidence, not impressions.

## 1. Principles
1. **Test the product, not the model.** Model + prompt + knowledge + retrieval + code are one system.
2. **Fix the layer that broke.** Measure retrieval, generation and actions separately.
3. **Rules first, judges for meaning, humans for calibration.**
4. **Errors are not failures.** Infra errors are reported as inconclusive, never as pass or fail.
5. **Every change gets a full regression run** against the same golden set.

## 2. Risk tiers and gates
| Tier | Examples | Gate |
|---|---|---|
| Critical | Invented facts/policies, unsafe or unconfirmed actions, data leaks, injection success | Must be 0 to release |
| High | Wrong refusal of valid requests (over-refusal), missing critical info | Threshold per feature, trend tracked |
| Quality | Tone, length, minor wording | Scored and reported, not blocking |

## 3. Evaluation layers
| Layer | Measures | Method |
|---|---|---|
| Retrieval | Context precision / recall | ID-based metrics on labeled chunks (no AI calls) |
| Generation | Correctness, faithfulness, completeness | Calibrated LLM judge |
| Safety | Injection, hijacking, contracts, overreliance | Automated red team + manual triage |
| Agents | Right tool, right arguments, confirmation, honest tool results, step limits | Deterministic checks on traces |
| Accessibility of AI output | No raw markdown/emoji overload, meaningful link text, plain language | Rules + judge + assistive-tech spot checks |

## 4. Golden datasets
- Mix: happy path, edge cases, out-of-scope, safety, ambiguous, plus a **legitimate twin** for every attack.
- Owned by QE and domain experts; versioned with the code.
- **Every production defect becomes a new case.** Known issues are tracked (xfail), never deleted.

## 5. Judge governance
- Calibrate on 30–50 human-scored cases; target ≥ 90% agreement on critical criteria.
- Judge model differs from the product model; judge prompt and model are pinned.
- Recalibrate quarterly and on any judge or rubric change. Humans are calibrated too.

## 6. Pipeline
| When | Runs | Purpose |
|---|---|---|
| Every PR | Rules + retrieval metrics + small critical smoke set | Fast, cheap regression gate |
| Nightly | Full golden set, repeated runs for pass rates | Catch flakiness and drift |
| Before release | Full red team with triage, candidate-vs-production comparison | Release decision |

## 7. Production monitoring
- Tracing on every request (retrieved chunks, prompt, output, latency, cost).
- Sampled online evaluation + 5–10% human spot-check.
- Watch: "I don't know" rate (a search health signal), over-refusals, hallucination flags, latency, cost per request.

## 8. Change control
- Full regression on any change to model, prompt, knowledge base, retrieval or code. One change at a time vs. a recorded baseline.
- Pin model versions; evaluate candidates side by side before switching.

## 9. Data and vendor governance
- No customer data in third-party eval tools without approval; mask PII in traces.
- Keys in secret stores only; rotate immediately on exposure.

## 10. Leadership metrics
Critical-case pass rate · confirmed red-team findings · retrieval recall · over-refusal rate ·
inconclusive-run rate · cost per eval run · time to detect and fix AI defects.