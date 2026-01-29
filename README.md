# Murphy: Strategic Stress-Testing System

Murphy is an analytical platform designed to stress-test strategic plans by simulating failure scenarios. Utilizing a predictive "Time Traveler" persona, the system identifies systemic vulnerabilities to help users develop more resilient execution frameworks.

## Core Features

**Failure Simulation:** Generates 10 specific failure points derived from initial strategic inputs.

**Scenario Maze:** Interactive evaluation of operational obstacles using Stress, Deviation, and Feasibility metrics.

**Severity Calibration:** Adjustable risk environments ranging from Optimistic to Total Chaos.

**Vector Memory:** Pinecone integration to retrieve historical lessons and prevent repetitive strategic errors.

**Iterative Refinement:** Binary feedback loop for optimizing strategies based on identified risks.

**Execution Roadmap:** Actionable task checklists and expert guidance for finalized strategies.

## Project Structure

`server.py`: Flask application routing and session management.

`llm_logic.py`: AI integration, embedding generation, and Pinecone logic.

`db_logic.py`: Supabase database operations and plan persistence.

`prompts.py`: AI persona definitions and system instructions.

`templates/`: Structured UI components and interactive dashboards.

## Quick Start

### 1. Installation

```bash
pip install -r requirements.txt
```


### 2. Configuration

Create a `.env` file with the following credentials:

`GEMINI_API_KEY`

`PINECONE_API_KEY`

`SUPABASE_URL` & `SUPABASE_KEY`

`SECRET_KEY`

### 3. Execution

```bash
python server.py
```
