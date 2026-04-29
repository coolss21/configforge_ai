# Loom Script (ConfigForge AI)

**[0:00-1:00] Problem Overview & "Why a Compiler?"**
"Hi, I'm the creator of ConfigForge AI. Generating entire applications from a single prompt is inherently flawed because LLMs struggle to maintain strict schema contracts across databases, APIs, UIs, and Auth simultaneously. ConfigForge treats natural language like high-level source code, running it through a multi-stage compiler pipeline with strict intermediate representations, validation, and targeted repair."

**[1:00-3:00] Pipeline Walkthrough & Contracts**
"Here is the pipeline... We start with Intent Extraction. Notice how the vague prompt 'Build a CRM with payments' produces a deterministic `IntentIR`. Then, we move to the System Designer to get `ArchitectureIR`. From there, we generate 5 independent schemas: DB, API, UI, Auth, and Logic. Each schema is strictly validated against a Pydantic contract."

**[3:00-5:00] Validation Engine & Targeted Repair**
"But what happens when the LLM hallucinates an API endpoint that doesn't exist in the UI schema? Our Cross-Layer Validator catches it. Instead of blindly regenerating everything—which is expensive and unstable—our Targeted Repair Engine sends ONLY the broken layer and the specific error back to the LLM to fix. Watch as it resolves an `API_ENTITY_MISSING` error in round 1."

**[5:00-7:00] Runtime Simulation Proof**
"To prove the config isn't just theoretical JSON, our Runtime Executor spins up an in-memory SQLite database, executes the generated SQL `CREATE TABLE` statements, and simulates API calls against the schema. If it fails, it feeds the SQL error back to the Repair Engine."

**[7:00-8:30] Evaluation Metrics & Tradeoffs**
"We also built an evaluation framework with 20 edge-case and normal prompts. The dashboard tracks our success rate, average repair attempts, and execution rate. We offer a 'Fast Mode' for quick drafts and a 'Quality Mode' which maxes out the repair loops for production-ready config."

**[8:30-10:00] Conclusion & Future**
"ConfigForge proves that building reliable AI dev tools requires systems engineering, not just prompt engineering. Thank you."
