# SmartCushion-Rasp

This repository contains the codebase for the SmartCushion project implemented on a Raspberry Pi. This project uses Docker containers for InfluxDB and Node-RED, a Python Flask backend, and an Expo client for frontend interaction.

## Getting Started

These instructions will guide you through the setup process to get the project running on your Raspberry Pi for development and testing purposes.

### Prerequisites

- Docker
- Conda environment manager

1. **Activate the Conda environment:**

```bash
 conda activate cushion
```

2. **Execute the Python scripts for data handling:**

```bash
cd fsr
python ENV_DATA.py
python sedentary.py
python posture.py
```

3. **Start the Flask backend server:**

```bash
cd ../backend
python app.py
```
