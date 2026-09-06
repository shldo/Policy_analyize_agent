# policy-research-agent

## Starting point

This independent repository starts from a working-tree snapshot of Policy in
Action Library. Original Git history is not imported. The snapshot includes
the local compose.yaml changes and the original project documentation.

Source repository: https://github.com/unsw-cse-comp99-3900/capstone-project-26t2-9900-w11c-bread

The original source directory is unchanged. Runtime databases, uploaded files,
secrets, installed dependencies, caches, resumes and course submission bundles
are not copied. proposal.pdf is retained as the original project specification.

## Next steps

1. GitHub repository provided: https://github.com/shldo/Policy_analyize_agent .
   The local folder remains policy-research-agent; origin points to this repository.
2. Inspect remote contents, review the initial snapshot, create its first commit and push.
3. Configure local services using the included environment examples.
4. Install dependencies and validate the application before feature changes.

Application feature code is unchanged. Local Compose configuration and migration
018 wiring have been added. Frontend/backend images now build successfully;
the database and backend are healthy, and the web page and health API return
HTTP 200 at localhost:8080. Full tests and model-backed Q&A remain pending.
