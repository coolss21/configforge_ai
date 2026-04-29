# Architecture

ConfigForge AI works as a multi-stage compilation pipeline.

1. **Intent Extractor**: Converts natural language into `IntentIR`. It normalizes ambiguities and infers standard architectural components (e.g., if a CRM is asked for, it infers Contacts and Dashboards).
2. **System Designer**: Uses `IntentIR` to design modules, data flows, and role models, generating `ArchitectureIR`.
3. **Schema Generator**: Generates Database, API, UI, Auth, and Business Logic schemas strictly using Pydantic contracts.
4. **Refinement Layer**: Normalizes the output, enforces sorting and naming conventions, and prepares the hash.
5. **Validation Engine**: Performs cross-layer and logical validation.
6. **Repair Engine**: Receives validation failures, subsets the schemas, and targeted repairs them (max 3 rounds).
7. **Runtime Executor**: Converts schemas to actual SQLite memory databases and tests API/UI bindings.
