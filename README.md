# AVALIVE 

## Overview
This project was developed as part of the PIDS – 4th Year Engineering Program at **Esprit School of Engineering** (Academic Year 2025–2026).
VITALE is a comprehensive full-stack solution designed for the pharmaceutical industry in Tunisia. 

## Features
- **BO1: Avatar Training Analysis**: Data-driven insights into delegate performance and training effectiveness.
- **BO2: Product Presentation Optimization**: Statistically identifying treatment lines and complexity for better marketing.
- **BO3: Recommendation Engine**: Intelligent medical product recommendations based on historical data.
- **BO4: Visit Scheduling Optimization**: Geospatial and temporal analysis to maximize the efficiency of medical representative visits.

## Tech Stack
### Frontend
### Backend

## Architecture

## Contributors
- El Jazi Amal
- Guirat Eya
- Touil Samar
- Moalla Ines
- Jeribi Aziz
- Kaddechi Rayen

## Academic Context
Developed at **Esprit School of Engineering – Tunisia**
PIDS – 4DS10 | 2025–2026

## Getting Started

### Prerequisites
- Python 3.10+
- NVIDIA GPU (RTX 3080Ti or better recommended for MuseTalk)
- PyTorch 2.5.0 with CUDA 12.4

### Installation & Execution

1. **Install Dependencies**:
   ```bash
   # Install LiveTalking dependencies (includes MuseTalk support)
   cd dso1/src/avatar/LiveTalking
   pip install -r requirements.txt
   ```

2. **Download Models**:
   - See [MUSETALK_SETUP.md](MUSETALK_SETUP.md) for detailed MuseTalk setup
   - Download MuseTalk models and generate avatar data

3. **Run the Application**:
   ```bash
   # From project root (automatically starts MuseTalk engine)
   python shared/main.py
   ```

4. **Access the Interface**:
   - Dashboard: `http://localhost:8010/dashboard.html`
   - API: `http://localhost:8010/webrtcapi.html`

### Model Configuration

The project currently uses **MuseTalk** for high-quality lip-sync. The configuration is set in `shared/main.py`:
- Model: `musetalk`
- Avatar ID: `musetalk_avatar`

To switch to other models (wav2lip, ultralight), modify the parameters in `shared/main.py`.
