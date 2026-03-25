#  PIDS-Cowin Architecture Guide

 This document explains the rigid, modular structure of the project.

## Root Directory
* `main.py`: The single orchestrator that starts the entire application (stitching DSO2's API with DSO1's AI).
* `.env`: Your private secrets. Never committed. Read by the shared components.

## The `shared/` Directory (The Common Toolbox)
Think of `shared/` as the central hub where Team DSO1 and Team DSO2 agree on how the app works. Anything placed here is used by **everybody**. If you change a file here, you must ensure both teams approve it, because it affects the whole app!
* `config.py`: The universal settings menu. It holds important app-wide settings (like where the `data/` folder is) so no one ever gets lost.
* `interfaces.py`: The agreed-upon dictionary. When DSO1 sends "Avatar Data," `interfaces.py` guarantees it is formatted the exact way that DSO2 expects it. It prevents missing data bugs.
* `utils.py`: The shared toolbox. It holds basic, everyday tools (like formatting text or generating numbers) that everyone uses, so no one has to write the same copy-pasted code twice.

##  The `dso1/` Directory (Core AI / Engine)
Owned exclusively by **Team DSO1**. This is where heavy ML lifting happens.
* `src/avatar/`: 3D avatar engine code, model loading, vertex manipulation.
* `src/nlp/`: The deeply-integrated NLP models processing conversational AI text.
* `src/evaluation/`: Scoring algorithms determining performance.
* `data/` & `notebooks/`: Exploratory sandboxes strictly segregated from `src/` so Jupyter metadata never pollutes production execution.
* `tests/`: Specifically written for testing only DSO1 engines implicitly.

##  The `dso2/` Directory (Product & Presentation)
Owned exclusively by **Team DSO2**. This team relies completely on DSO1 outputs (ingested via `shared/interfaces.py`).
* `src/assistant/`: Higher-level orchestration logic for the end-user product layer.
* `src/api/`: The FastAPI (or similar) layer defining REST endpoints facing the front-end or client apps.
* `data/` & `notebooks/`: Sandbox and test fixtures for the API layer.
* `tests/`: Specifically tests the API routes and Assistant layer logic.

##  `dso3/` & `dso4/`
Reserved expansion slots for Phase 3 and Phase 4 features.

