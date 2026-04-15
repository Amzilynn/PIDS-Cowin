# AVALIVE | LiveTalking Integration

<div align="center">
  <img src="./assets/LiveTalking-logo.jpg" align="middle" width="300"/>
  <br/>
  <h3>AVALIVE - Powered by LiveTalking</h3>
</div>

<div align="center">
  <a href="./LICENSE"><img src="https://img.shields.io/badge/license-Apache%202-dfd.svg"></a>
  <a href=""><img src="https://img.shields.io/badge/python-3.10+-aff.svg"></a>
  <a href=""><img src="https://img.shields.io/badge/os-linux%2C%20win%2C%20mac-pink.svg"></a>
</div>

---

## 📌 Overview

This project was developed as part of the **PIDS – 4th Year Engineering Program** at **Esprit School of Engineering** (Academic Year 2025–2026).

**AVALIVE** is a full-stack solution built for **VITALE**, a pharmaceutical company in Tunisia. The project integrates **LiveTalking** — a real-time interactive digital human system — to power AI-driven avatars for pharmaceutical applications.

> 🎯 All credit for the real-time streaming and lip-sync technology goes to the [LiveTalking](https://github.com/lipku/LiveTalking) project by lipku.

---

## 🎬 LiveTalking Features

| Feature | Status |
| :--- | :--- |
| Real-time lip-sync (Wav2Lip/MuseTalk/ERNeRF) | ✅ |
| Voice cloning | ✅ |
| Speech interruption support | ✅ |
| WebRTC / RTMP / Virtual camera output | ✅ |
| Idle motion video (action choreography) | ✅ |
| Multi-concurrent sessions | ✅ |
| Custom avatar support | ✅ |

---

## 🛠️ Tech Stack

### Frontend
- React / Next.js
- WebRTC client
- TailwindCSS

### Backend
- Python FastAPI
- LiveTalking engine
- PostgreSQL / Redis

### AI/ML
- LiveTalking (Wav2Lip for lip-sync)
- Qwen LLM
- EdgeTTS / CosyVoice

### Deployment
- Docker with GPU support
- Ubuntu 22.04 / 24.04
- NVIDIA CUDA 12.4

---

## 🚀 Installation (RTX 5070 Laptop Setup)

### Prerequisites
- **OS**: Ubuntu 24.04 (recommended) or Windows 11 + WSL2
- **GPU**: NVIDIA RTX 5070 Laptop (8GB VRAM)
- **RAM**: 32GB DDR5
- **CUDA**: 12.4

### Step 1: Clone Repository

```bash
git clone https://github.com/your-org/avaline
cd avaline
