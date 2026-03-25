"""
PIDS-Cowin - Top-Level Orchestrator
This entrypoint initializes the shared configuration, prepares the
DSO1 Avatar/NLP engines, and mounts them onto the DSO2 FastAPI endpoints.
"""
from shared.logger import get_logger
from shared.config import PROJECT_ROOT

logger = get_logger("PIDS-Main")

def start_application():
    logger.info(f"Starting PIDS-Cowin from Root: {PROJECT_ROOT}")
    logger.info("Initializing DSO1 AI components indirectly...")
    logger.info("Starting DSO2 Server...")
    # Example: uvicorn.run("dso2.src.api.app:app", host="0.0.0.0", port=8000)

if __name__ == "__main__":
    start_application()
