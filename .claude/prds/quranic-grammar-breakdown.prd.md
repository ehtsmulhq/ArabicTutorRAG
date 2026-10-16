# Quranic Grammar Breakdown Assistant (V2)

## Problem
The current system acts as an open-ended Q&A bot, which causes the local 7B model to hallucinate ("invent rules") and take too long to respond. Furthermore, the user's ultimate goal is practical application, but the current prototype does not directly map grammatical rules to actual Quranic verses.

## Evidence
- **Observed behavior:** The local model (`qwen2.5:7b`) takes too much time and invents rules when answering general questions.
- **User intent:** "this project is for my own... i want to shift gear to it will explain quranic verses gramartically."

## Users
- **Primary:** The developer/learner (personal power tool for deep study).
- **Not for:** Commercial SaaS users, or casual conversational Arabic learners.

## Hypothesis
We believe **shifting the system's core capability to explicitly breaking down Quranic verses grammatically (I'rab)** will **solve the hallucination problem (by constraining the output format)** for **the user**.
We'll know we're right when **the local LLM can parse a test verse into its grammatical components without outputting any fabricated rules**.

## Success Metrics
| Metric | Target | How measured |
|---|---|---|
| Hallucination Rate | 0 invented rules | Manual verification against trusted I'rab sources |
| Time to Value | < 10 seconds per verse | Stopwatch / Terminal execution logs |

## Scope
**MVP** — A specialized pipeline where the user inputs a Quranic verse, the system retrieves relevant grammar rules from the local knowledge graph, and the local LLM outputs a strict, structured grammatical breakdown (e.g., identifying the Mubtada, Khabar, Mudaf).

**Out of scope**
- Shifting to Cloud APIs (OpenAI/Anthropic) — remaining 100% local.
- Commercialization, user accounts, and monetization.
- Complete UI rewrites (React/Next.js) — sticking with what works locally.

## Delivery Milestones

| # | Milestone | Outcome | Status | Plan |
|---|---|---|---|---|
| 1 | Anti-Hallucination Prompting | The LLM is locked into a strict "extraction and formatting" mode that refuses to invent rules, reducing response time by stripping conversational filler. | pending | — |
| 2 | Quranic Verse Pipeline | The app accepts a specific verse, retrieves relevant grammatical concepts from the Graph, and outputs the breakdown. | pending | — |

## Open Questions
- [ ] How will we source the "ground truth" grammar (I'rab) of the Quran to verify if the local model is right? (e.g., integrating the open-source Quranic Arabic Corpus data).

## Risks
| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| The 7B local model isn't smart enough to do complex I'rab on its own | High | High | Use the RAG pipeline to pull the exact grammatical tags from an external corpus, so the LLM acts only as a formatter, not a reasoning engine. |
| Still too slow | Medium | Medium | Force the LLM to output small JSON responses instead of long paragraphs. |

---
*Status: DRAFT — requirements only. Implementation planning pending via /plan.*
