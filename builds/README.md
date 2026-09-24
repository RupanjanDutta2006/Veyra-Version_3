# Build and Environment Artifacts Directory

This directory is designated for isolated build environments and build artifacts as defined in **Step 1 — Clone both repositories and create the audit workspace.md** of the Veyra SIH Round-2 Integration Roadmap.

## Specifications
- **Workspace Build Isolation:** Accommodates isolated Python virtual environments (`repo_a_venv`, `repo_b_venv`, `integration_venv`) and packaging targets.
- **Current Runtime Environment:** Verified and certified against Python 3.10 with full native C-extensions and pre-installed dependencies for LightGBM, Scikit-learn, FastAPI, PyTest, and React Vite frontend toolchains.
- **Production Package Targets:** Handled via `repos/repo_b/builds/` and root package manifests.
