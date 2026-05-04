import sys
import os
import uvicorn

# Ensure the root is in the search path so folders can see each other
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

from app.server import combined_app, PORT

def start():
    print(f"[LAUNCHER] 🚀 Starting Sarah Khalil Neural Avatar from {ROOT_DIR}")
    uvicorn.run(combined_app, host="0.0.0.0", port=PORT)

if __name__ == "__main__":
    start()
