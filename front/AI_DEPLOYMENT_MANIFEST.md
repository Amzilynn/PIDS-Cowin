# Avalive AI Deployment Manifest

Follow these exact steps to activate the **Functional AI Models** in Admin (Ava Business) and Delegate (Ava Train/Assistant).

### 1. Visual Models (Face Mesh & Emotion)
**Target Directory**: `public/models/`
**Files Required**:
- `ssd_mobilenet_v1_model-weights_manifest.json`
- `face_landmark_68_model-weights_manifest.json`
- `face_expression_model-weights_manifest.json`
*(And all associated .bin Shard files)*

### 2. Large AI Engines (LLM, STT, TTS)
**Target Directory**: `server/ai_models/models/`
**Models to Move/Link here**:
- `BioMistral-7B` (Place the folder from Hugging Face here)
- `whisper-base` (Place the folder from Hugging Face here)
- `wav2vec2-lg-xlsr-en-speech-emotion-recognition` (Place the folder from Hugging Face here)

### 3. Activation
Once the files are in place:
1. Open a terminal in `server/ai_models`.
2. Run: `& "C:\Program Files\nodejs\node.exe" main.py` (or use your Python interpreted).
3. The platform will automatically detect these local models and activate the "Functional" mode.

---
**Status**: 
- **Admin AI (Ava Business)**: [READY - Waiting for Weights]
- **Delegate AI (Ava Train)**: [READY - Waiting for Weights]
- **Multimodal Fusion**: [READY - Waiting for Weights]
