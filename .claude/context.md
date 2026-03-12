# AI Politician Accountability — System Design

## Goal

An AI agentic system for **politician accountability** — it scrapes legislation data, finds politician positions on that legislation, neutralizes political rhetoric/bias, and presents factual information to end users. The system targets Canadian politics initially, using the OpenNorth API for representative data.

## Architecture Decisions (Finalized)

- **No supervisor pattern** — the pipeline is sequential; each agent depends on the previous agent's output. A supervisor would be a wasted LLM call since routing is always the same.
- **No planner-executor pattern** — same reasoning. The plan would be identical every run. Just a static LangGraph DAG.
- **Linear sequential chain** — `Agent 1 (ReAct) → Agent 2 (ReAct) → Agent 3 (ReAct) → Redactor (code) → Rhetoric LLM (call) → Judge LLM (call) → Research LLM (call) → Vector DB write (code) → Presentation LLM (call) → Output`
- **Do not over-engineer** — keep things simple and direct for engineering purposes.
- **Minimal agency principle** — only use true ReAct agents where autonomous decision-making is required (search/evaluate/retry loops, code debugging). Everything else is either a single LLM call or pure deterministic code. This was a deliberate reclassification to eliminate wasted LLM reasoning on steps that have no real decisions.

## Pipeline Components

### ReAct Agents (3) — autonomous tool-use loops, real decision-making

1. **Agent 1: Legislation Finder** — searches web for legislation, validates source reliability, retries with different queries if results are poor. Returns URLs + bill metadata. Needs agency because search targets are unpredictable and source reliability evaluation may require re-searching.
2. **Agent 2: Scraper Builder** — generates Python scraping code, executes via REPL, filters by date (last 7 days). Includes a debugging tool to inspect and fix its own code. Needs agency because it scrapes arbitrary URLs with unpredictable HTML structures — LLM-generated code may fail and needs self-correction.
3. **Agent 3: Politician Position Finder** — finds politician statements, press releases, floor speeches, vote records across multiple source types. Needs agency because it makes relevance judgments about results and decides whether to keep searching.

### Single LLM Calls (4) — no tools, no agency, structured input/output

4. **Rhetoric Neutralizer (single LLM call)** — analyzes anonymized statements, extracts claims with source citations, classifies rhetorical devices. Has a hard constraint: **must never attempt to guess the politician's identity**. No agency needed — receives fixed input, produces structured output.
5. **Judge (single LLM call)** — stateless, context-isolated bias screening layer. Uses a **different OpenAI model** than the Rhetoric Neutralizer (same company, different model). Evaluates 4 criteria:
   - Criterion 0: Identity Inference Prohibition (HARD CONSTRAINT)
   - Criterion 1: Grounding Violation
   - Criterion 2: Tonal Bias
   - Criterion 3: Unsupported Inference
   - Returns structured JSON verdict with `pass`/`fail` + `revision_instructions`
   - Retry logic: max 2 retries on soft fail (sends feedback to Rhetoric Neutralizer), identity inference fail routes back to Redactor for stronger anonymization, retries exhausted → quarantine (confidence: low)
   - **The Judge never sees the real politician name and never sees graph state (retry count, etc.)** — this isolation is what makes it an unbiased evaluator
6. **Research Writer (single LLM call)** — compiles research notes, cross-references sources. No agency needed — receives all data, produces structured notes.
7. **Presentation LLM (single LLM call)** — condenses research notes into user-facing output. No agency needed.

### Pure Code Steps (3) — no LLM involved at all

8. **Redactor (pure code)** — NER-based name removal, title/committee stripping, replaces with "Legislator A/B/C" to anonymize before rhetoric analysis. Deterministic, no LLM.
9. **Vector DB Write (pure code)** — publishes embeddings from Research Writer output to Vector DB. Deterministic, no LLM.
10. **Citation Validation (pure code)** — Layer 5 of debiasing strategy. Checks whether quoted text actually exists in source documents. Deterministic, no LLM.

### Downstream Consumer

11. **RAG Chatbot** — downstream consumer of Vector DB, separate from the pipeline.

## Bias/Debiasing Strategy (Layered Defense in Depth)

Based on research papers discussed:

- **Layer 1 (Input):** Entity anonymization — strip politician names before the Rhetoric Neutralizer sees them
- **Layer 2 (LLM call design):** Structured output with mandatory source citations
- **Layer 3 (Intra-call):** Self-debiasing via reprompting (two-pass) — based on Gallegos et al., 2024 (arXiv:2402.01981)
- **Layer 4 (Post-call):** LLM-as-Judge bias screen — based on Phute et al., 2023 (arXiv:2308.07308)
- **Layer 5 (Programmatic):** Citation validation — code checks whether quoted text exists in source

## Source Reliability Tool (Design Phase)

A tool inside Agent 1 that ensures only **trustworthy, authoritative sources** pass through (not just HTTP status checks). Cannot be fully deterministic because municipal government URLs vary by city (e.g., `brampton.ca`, `council.nyc.gov`, Legistar portals, etc.).

**Two-layer design:**

- **Layer 1: Domain Heuristic Check (deterministic code)** — pass `.gov`/`.gc.ca`/known legislative platforms (Legistar, eScribe, Granicus), fail social media/blogs/opinion sites, uncertain goes to Layer 2
- **Layer 2: LLM Source Evaluation (single LLM call, not agent)** — for uncertain URLs only, classifies as `official`, `likely_official`, `news`, `unreliable`, or `unknown`. Only `official` and `likely_official` pass.

This is a **tool inside Agent 1** (not a separate graph node) so the agent can self-correct and search again if too many links are filtered out.

**Open question:** How to treat news articles (CBC, local newspapers) — undecided on whether to allow them as secondary sources or exclude entirely. This needs to be resolved before implementation.

## Discoveries

- LLMs **can** detect rhetoric and bias effectively when given the task explicitly — the key is architectural isolation (anonymization, structured output, dedicated evaluation criteria)
- The LLM-as-Judge paper (Phute et al.) explicitly specifies the judge should be a **single LLM call, not an agent** — no tools, no memory, no iterative output generation. Its effectiveness comes from its narrow, isolated scope.
- Keeping the Judge stateless (no access to retry count or graph state) prevents it from reasoning about consequences of its verdict, which would introduce bias
- The `langgraph-supervisor` package was removed from requirements as it's no longer needed
- The codebase was initially broken scaffolding from ChatGPT — `llm` and `tools` were undefined in `agent.py`, `supervisor` was undefined in `main.py`
- LangGraph version is 1.0.10, langchain-openai is 1.1.11
- `create_react_agent` uses `model=` parameter (not `llm=`) in current LangGraph version
- Agent 2 (Scraper Builder) must remain a ReAct agent because it generates scraping code for arbitrary, unpredictable URLs — a debugging tool is needed so the system doesn't break when LLM-generated code fails against unfamiliar HTML structures

## Accomplished

### Completed
- Architectural decision: sequential pipeline, no supervisor, no planner
- Full pipeline design — 3 ReAct agents, 4 single LLM calls, 3 pure code steps
- Reclassification: stripped agency from components that don't make real decisions (Rhetoric Neutralizer, Research Writer became single LLM calls; Citation Validation, Vector DB write became pure code)
- Debiasing strategy designed (5 layers)
- Judge design specified (4 criteria, structured output schema, retry logic, isolation constraints)
- Mermaid diagram updated in `diagrams/ai-politician-accountability.mmd` — clean, engineering-focused, no excessive styling
- `requirements.txt` updated (removed `langgraph-supervisor`, added `python-dotenv`)
- `utils/tools.py` implemented with stub tools for Agent 1 and Agent 2
- `utils/agent.py` rewritten with factory functions `build_agent_1(llm)` and `build_agent_2(llm)`
- `main.py` rewritten with LangGraph `StateGraph` — linear chain of Agent 1 → Agent 2, compiles and runs successfully
- Source reliability tool designed (two-layer: domain heuristic + LLM evaluation)

### In Progress
- Source reliability tool implementation — design is done, needs to be built as a tool inside Agent 1
- Decision needed on news article policy (allow as secondary source vs. exclude)

### Not Started
- Agent 3 (Politician Position Finder) — not built
- Redactor (pure code, NER-based) — not built
- Rhetoric Neutralizer (single LLM call) — not built
- Judge (single LLM call) — not built
- Research Writer (single LLM call) — not built
- Presentation LLM (single LLM call) — not built
- Vector DB integration (pure code) — not built
- Citation Validation (pure code) — not built
- RAG Chatbot — not built
- OpenNorth API integration — not built
- Real tool implementations (replace stubs with actual web search, scraping, etc.)
- Tavily integration for Agent 1's web search
- Debugging tool for Agent 2 — not built
