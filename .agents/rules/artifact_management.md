# Artifact and Material Management Rule

All generated markdown process artifacts, operational inputs, practical outputs, scripts, and RAG databases must be preserved under their respective 5 numbered directories:

1. **Process Artifacts (`00_artifacts/`)**:
   - Exclusively for Antigravity agent process outputs (.md only).
   - Plans: `00_artifacts/plans/plan_([topic])_[YYMMDD]_rev[NN].md`
   - Walkthroughs: `00_artifacts/walkthroughs/walkthrough_([topic])_[YYMMDD]_rev[NN].md`
   - Reports: `00_artifacts/reports/report_([topic])_[YYMMDD]_rev[NN].md`
   - Designs: `00_artifacts/designs/design_([topic])_[YYMMDD]_rev[NN].md`

2. **Input Materials (`01_input_data/`)**:
   - Received (`00_received/`): External provenance materials (spec sheets, CAD, raw data, test telemetry). Raw filenames preserved if required.
   - References (`01_references/`):
     - Agent task instructions, user guidelines, prompt context notes.
     - Engineering standards, solver manuals, user-researched papers.
     - Standard template: `[format]_[seq]_([topic])_[YYMMDD]_rev[NN].[ext]`

3. **Practical Outputs (`02_output_data/`)**:
   - Data (`00_data/`): `excel_[seq]_([topic])_[YYMMDD]_rev[NN].xlsx`, `csv_[seq]_([topic])_[YYMMDD]_rev[NN].csv`
   - Figure & Logs (`01_figure/`): `plot_[seq]_([topic])_[YYMMDD]_rev[NN].png`, `image_[seq]_([topic])_[YYMMDD]_rev[NN].png`, `log_[seq]_([topic])_[YYMMDD]_rev[NN].trn`
   - Reports & Slides (`02_reports/`): `doc_[seq]_([topic])_[YYMMDD]_rev[NN].docx`, `ppt_[seq]_([topic])_[YYMMDD]_rev[NN].pptx`, `pdf_[seq]_([topic])_[YYMMDD]_rev[NN].pdf`

4. **Automation Scripts (`03_scripts/`)**:
   - Pre/post processing Python: `py_[seq]_([topic])_[YYMMDD]_rev[NN].py`
   - Solver batch journal: `jou_[seq]_([topic])_[YYMMDD]_rev[NN].jou`

5. **RAG Knowledge Base (`04_rag_database/`)**:
   - Dedicated storage for RAG indexes and vector databases.
   - Targets, .gitignore, and catalog are dynamically managed on-demand by `rag-builder`.

- Underscores only (`_`), no hyphens (`-`).
- Topic enclosed in parentheses `(` `)`.
- Sequence: 3-digit serial number (`001`, `002`, ... `999`).
- Versioning: `rev00` default on creation; increment (`rev01`, `rev02`) on modification.
- Always update index tables in the respective `README.md` files.
