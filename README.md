# 🛡️ AURA: AI Safety Red Team Agent

> **An automated, defensive evaluation agent designed for systematic model safety probing, policy boundary verification, and regression tracking.**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: Pydantic v2](https://img.shields.io/badge/data%20validation-pydantic%20v2-green.svg)](https://docs.pydantic.dev/)

---

## 📌 Executive Overview

The **AURA AI Safety Red Team Agent** is a defensive security and compliance testing harness for Large Language Models. Rather than generating harmful payloads or exploits, it systematically tests models against **defensive safety taxonomies** (policy boundaries, persona pressures, multi-turn conversational drift, syntactic obfuscation, and canary secret retention) to assess alignment and catch regressions before production deployment.

### 🌟 Key Capabilities
- **Modular Strategy Taxonomy**: 5 distinct defensive probe strategies generating synthetic, policy-aligned test vectors.
- **Unified Multi-Provider Adapters**: Native support for **Google Gemini**, **OpenAI & OpenAI-compatible endpoints** (Groq, DeepSeek, Together AI, local Ollama/vLLM), plus deterministic **Mock targets** for zero-cost CI testing.
- **Hybrid Evaluation Classifier**: Rule-based refusal signature heuristics + structured **LLM-as-a-Judge** rubric classifying outcomes into:
  - `REFUSED` (Safe compliance with safety guidelines)
  - `NON_COMPLIANT` (Safety policy violation)
  - `PARTIAL` (Soft refusal with information leakage)
  - `ERROR` (Operational or API failure)
- **Safety Regression Engine**: Benchmark candidate models against baselines and compute **Safety Delta Score**, highlighting specific regressed and improved probes.
- **Dual Interface**:
  - 🖥️ **Rich Terminal CLI**: Color-coded summary tables, real-time progress bars, and colored regression diffs.
  - 📊 **Streamlit Visualizer**: Interactive drill-down into conversational turns, strategy vulnerability charts, and side-by-side run comparisons.

---

## 🏛️ System Architecture

Detailed architectural documentation, dataflow sequence diagrams, and formal state machines are documented in [**docs/ARCHITECTURE.md**](docs/ARCHITECTURE.md).

```
+===================================================================================================+
|                                    AURA SYSTEM ARCHITECTURE                                       |
+===================================================================================================+

   +-------------------------+       +-------------------------+       +------------------------+
   |  Config & Environment   |       | Defensive Strategy Lib  |       | Baseline Benchmark Run |
   |  (Pydantic Settings)    |       | (5 Defensive Taxonomies)|       |  (Historical JSON/CSV) |
   +------------+------------+       +------------+------------+       +-----------+------------+
                |                                 |                                |
                v                                 v                                v
+===================================================================================================+
|                                        ORCHESTRATION LAYER                                        |
|                                                                                                   |
|  +---------------------------------------------------------------------------------------------+  |
|  |                             SafetyRedTeamAgent (Evaluation Loop)                            |  |
|  |  - Dispatches Single/Multi-Turn Safety Probes                                               |  |
|  |  - Maintains Multi-Turn Conversation History (ChatMessage sequences)                        |  |
|  |  - Collects Token Usage & Latency Benchmarks                                                |  |
|  +---------------------------------------------------------------------------------------------+  |
+==============================================+====================================================+
                                               |
         +-------------------------------------+-------------------------------------+
         |                                                                           |
         v                                                                           v
+===================================+                       +=======================================+
|       TARGET ADAPTER LAYER        |                       |       SAFETY CLASSIFIER / JUDGE       |
|                                   |                       |                                       |
|  +-----------------------------+  |                       |  +---------------------------------+  |
|  | BaseTargetAdapter (ABC)     |  |                       |  | Heuristic Rule Matcher          |  |
|  +--------------+--------------+  |                       |  | - Refusal Signature Scanner     |  |
|                 |                 |                       |  | - Canary Token Secret Detector  |  |
|    +------------+------------+    |                       |  | - Violation Keyword Red Flags   |  |
|    |            |            |    |                       |  +----------------+----------------+  |
|    v            v            v    |                       |                   |                   |
| [Gemini]    [OpenAI]      [Mock]  |                       |                   v                   |
| Adapter     /Groq/Ollama  Adapter |                       |  +---------------------------------+  |
| (API Client)(API Client)  (CI Lab)|                       |  | LLM-as-a-Judge Rubric Parser    |  |
|                                   |                       |  | (Structured JSON Classification)|  |
|                                   |                       |  +----------------+----------------+  |
+===================================+                       +===================+===================+
                                                                                |
                                                                                v
+===================================================================================================+
|                                    PERSISTENCE & REGRESSION LAYER                                 |
|                                                                                                   |
|  +--------------------------------------------+    +-------------------------------------------+  |
|  | PersistenceEngine                          |    | RegressionEngine                          |  |
|  | - Aggregates Run Metrics (0-100% Score)    |    | - Baseline vs Candidate Comparative Diff  |  |
|  | - Serializes JSON & CSV Reports to Runs/   |    | - Categorizes REGRESSED, IMPROVED, UNCHG  |  |
|  +--------------------------------------------+    +-------------------------------------------+  |
+===================================================================================================+
                                                |
                                                v
+===================================================================================================+
|                                     PRESENTATION & USER INTERFACES                                |
|                                                                                                   |
|   +---------------------------------------+       +--------------------------------------------+  |
|   | Rich Terminal CLI (Typer / Rich)      |       | Modern Cyber Web UI (FastAPI + JS SPA)     |  |
|   | - aura-safety run                     |       | - Real-Time Test Runner & Live Logs        |  |
|   | - aura-safety compare                 |       | - Interactive Radial Safety Gauge          |  |
|   | - aura-safety list-strategies         |       | - Turn-by-Turn Probe Trajectory Modal      |  |
|   +---------------------------------------+       +--------------------------------------------+  |
+===================================================================================================+
```

```mermaid
flowchart TD
    subgraph Config & Inputs
        ENV[.env Configuration]
        STRAT[Strategy Library & Probes]
        BASE[Baseline Run JSON]
    end

    subgraph Core Engine
        CLI[Typer / Rich CLI]
        LOOP[Evaluation Agent Loop]
        JUDGE[Safety Evaluator / Classifier]
        REGRESS[Regression Engine]
    end

    subgraph Target Adapters
        ADAPT{Target Adapter}
        GEMINI[Gemini Adapter]
        OPENAI[OpenAI / Compatible Adapter]
        MOCK[Mock Target (Local CI/Test)]
    end

    subgraph Outputs & Artifacts
        REPORTS[JSON & CSV Run Reports]
        CONSOLE[Rich Terminal Summary]
        DASH[Modern Cyber Web UI]
    end

    CLI --> LOOP
    STRAT --> LOOP
    ENV --> ADAPT
    LOOP --> ADAPT
    ADAPT --> GEMINI
    ADAPT --> OPENAI
    ADAPT --> MOCK
    ADAPT --> LOOP
    LOOP --> JUDGE
    JUDGE --> LOOP
    LOOP --> REPORTS
    LOOP --> CONSOLE
    REPORTS --> REGRESS
    BASE --> REGRESS
    REGRESS --> CONSOLE
    REPORTS --> DASH
```

---

## 🛡️ Safety Test Strategy Catalog

| Strategy Identifier | Category | Defensive Rationale & Description | Turns |
| :--- | :--- | :--- | :---: |
| `direct_policy_probe` | `POLICY_BOUNDARY` | Direct synthetic queries testing primary policy boundaries (access control, data exfiltration, deceptive communications). | 1 |
| `role_instruction_pressure` | `ROLE_PRESSURE` | Tests resistance against fictional personas, academic research framing, and asserted senior executive authority. | 1 |
| `multi_turn_persistence` | `MULTI_TURN_PERSISTENCE` | Sequential conversational escalation (benign context -> technical mechanics -> automated evasion scripts) probing conversational safety drift. | 3 |
| `obfuscated_instruction_phrasing` | `OBFUSCATED_INSTRUCTION` | Syntactic perturbations (Base64 wrapping, ROT13 ciphers, delimiter insertion) probing keyword-filter brittleness. | 1 |
| `sensitive_info_handling` | `SENSITIVE_INFO_HANDLING` | Tests retention of synthetic Canary secrets (`CANARY_SEC_...`), PII synthesis resistance, and system prompt extraction. | 1 |

---

## 🚀 Quickstart & Installation

### 1. Clone & Set Up Environment
```bash
git clone https://github.com/your-username/aura-safety.git
cd aura-safety

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -e .
```

### 2. Configure API Keys
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Fill in your provider credentials:
```ini
GEMINI_API_KEY="your-gemini-key"
OPENAI_API_KEY="your-openai-key"
OPENAI_BASE_URL="https://api.openai.com/v1"
```

---

## 💻 CLI Usage Guide

### 1. List Available Safety Strategies
```bash
python -m aura_safety.cli.main list-strategies
```

### 2. Run an Evaluation against a Target Model
```bash
# Evaluate Google Gemini
python -m aura_safety.cli.main run --target gemini --model gemini-2.5-flash

# Evaluate OpenAI / Compatible (e.g. GPT-4o, Groq, Ollama)
python -m aura_safety.cli.main run --target openai --model gpt-4o-mini

# Evaluate Deterministic Mock Target (zero cost / CI mode)
python -m aura_safety.cli.main run --target mock --mock-mode strict_safe
```

### 3. Run Specific Strategies Only
```bash
python -m aura_safety.cli.main run --target gemini -s role_instruction_pressure -s multi_turn_persistence
```

### 4. Continuous Regression Testing (Baseline vs Candidate)
```bash
# Run baseline
python -m aura_safety.cli.main run --target mock --mock-mode strict_safe

# Run candidate and compare against baseline
python -m aura_safety.cli.main run --target mock --mock-mode vulnerable --compare run_20260820_051908_6f2094
```

### 5. Compare Any Two Historical Runs
```bash
python -m aura_safety.cli.main compare run_baseline_id run_candidate_id
```

### 6. List All Saved Run Reports
```bash
python -m aura_safety.cli.main list-runs
```

---

## 🌐 Modern Interactive Web Application
A custom, luxury glassmorphic web interface is included with live test execution, trajectory inspection, and regression diffing:

```bash
# Launch the web interface (FastAPI backend + Vanilla HTML5/CSS3/JS frontend)
aura-safety web --port 8888
```
Open **[http://localhost:8888](http://localhost:8888)** in your browser to access:
- **Executive Overview**: Real-time KPI cards, strategy safety bar charts, and outcome distribution doughnut charts.
- **Live Test Runner**: Interactive evaluation launcher with animated progress tracking and streaming execution logs.
- **Probe Trajectory Explorer**: Filterable and searchable table with turn-by-turn conversational inspection and Judge reasoning.
- **Safety Regression Matrix**: Side-by-side run comparisons with automated safety delta computation and probe status transition diffs.
- **Defensive Strategy Catalog**: Comprehensive taxonomy breakdown with probe counts and complexity ratings.
- **Instant Exports**: One-click CSV and JSON report downloads.

---

## 🧪 Testing & Validation

Run the automated test suite with pytest:
```bash
python -m pytest -v
```

---

## 📂 Project Structure

```text
d:/AURA/
├── .env.example
├── .gitignore
├── pyproject.toml
├── README.md
├── aura_safety/
│   ├── __init__.py
│   ├── config.py                   # Pydantic Settings & environment config
│   ├── schemas.py                  # Pydantic v2 schemas (Outcomes, Probes, Reports)
│   ├── adapters/                   # Model interfaces
│   │   ├── __init__.py             # Target adapter factory
│   │   ├── base.py                 # BaseTargetAdapter ABC
│   │   ├── gemini_adapter.py       # Google Gemini adapter (google-genai)
│   │   ├── openai_adapter.py       # OpenAI & compatible adapter
│   │   └── mock_adapter.py         # Deterministic mock adapter for CI/local tests
│   ├── strategies/                 # Defensive safety test strategies
│   │   ├── __init__.py
│   │   ├── base.py                 # BaseSafetyStrategy ABC
│   │   ├── direct_policy.py        # Direct boundary probes
│   │   ├── role_pressure.py        # Persona/Role pressure probes
│   │   ├── multi_turn.py           # Multi-turn persistence probes
│   │   ├── obfuscation.py          # Obfuscated phrasing & ciphers
│   │   ├── sensitive_info.py       # Canary leak & PII handling probes
│   │   └── registry.py             # Strategy catalog & loader
│   ├── engine/                     # Core evaluation & orchestration
│   │   ├── __init__.py
│   │   ├── agent.py                # Red team evaluation agent loop
│   │   ├── classifier.py           # Safety outcome classifier (Heuristic + LLM Judge)
│   │   ├── persistence.py          # Run recording, JSON/CSV exports
│   │   └── regression.py           # Regression comparison & diff engine
│   ├── cli/                        # Rich / Typer CLI
│   │   ├── __init__.py
│   │   ├── main.py                 # CLI entrypoint commands
│   │   └── formatting.py           # Rich tables, outcome badges, diff panels
│   └── dashboard/                  # Interactive Streamlit dashboard
│       └── app.py                  # Streamlit run inspector & visualizer
├── data/
│   └── runs/                       # Stored JSON & CSV evaluation runs
└── tests/                          # Pytest test suite
    ├── test_adapters.py
    ├── test_agent_loop.py
    ├── test_classifier.py
    ├── test_regression.py
    └── test_strategies.py
```

---

## 🔒 Safety & Ethical Principles

This project is built strictly for **defensive model alignment and safety evaluation**:
1. **Synthetic & Abstract Test Prompts**: Probes test policy compliance and boundary resistance without containing hazardous weapons, biology, or real exploit payloads.
2. **Deterministic Regression Tracking**: Enables engineering teams to prevent safety regressions across model quantization, fine-tuning, or system prompt updates.
3. **Open & Extensible**: Modular structure makes it simple to plug in custom organizational policies or private evaluation benchmarks.
