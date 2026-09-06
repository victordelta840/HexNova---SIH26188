# SIH Demonstration Mode

These scenarios use fictional, deterministic synthetic documents only. They are not valid for travel or identification and do not represent government records.

Recommended presentation flow:

1. Set `SCREENING_JWT_SECRET_KEY` and a demonstration officer password.
2. Sign in as the configured `demo.officer` account.
3. Open Simulation Lab and run each scenario.
4. Show the actual OCR, validation, metadata, tamper, face, risk, SHA-256, and audit outputs.
5. Open the generated case in Screening History and export its PDF report.
6. Use Reset Demo Data only after confirming the prompt.

All scenarios call the same authenticated screening pipeline as a normal upload. OCR, tamper analysis, and face detection may report unavailable states when their local dependencies or image evidence do not support a conclusion.
