# SentinelVision

*An AI-powered surveillance application detecting behavioral anomalies in video.*

## Table of Contents
1. [Project Overview](#project-overview)  
2. [Features](#features)  
3. [Architecture](#architecture)  
4. [Getting Started](#getting-started)  
   - [Prerequisites](#prerequisites)  
   - [Installation](#installation)  
   - [Running the Project](#running-the-project)  
5. [Usage](#usage)  
6. [Future Development](#future-development)  
7. [Contributing](#contributing)  
8. [License](#license)  

---

## Project Overview

SentinelVision is designed to monitor real-time video feeds for unusual human behaviors—such as loitering, object abandonment, or irregular motions—and raise alerts to enhance safety.

---

## Features

- Object/person detection via YOLO models  
- Behavioral anomaly recognition (e.g., loitering, abandonment, erratic movement)  
- Flask-based web dashboard showing live alerts  
- Easily deployable on local systems for CCTV or simulated feeds

---

## Architecture

The project is organized into modules that handle:

- **yolo_detector.py** – Object and person detection using YOLO  
- **`anomaly_detector.py`** – Behavioral analysis logic  
- **`video_processor.py`** – Video frame capture and processing  
- **`app.py` / `routes.py` / `main.py`** – Flask application for dashboard  
- **`models.py`** – Machine learning models or data definitions  
- **Static files & templates** – UI components (HTML, CSS, JS)  
- **`extensions.py`** – Flask extensions setup  
- **`pyproject.toml`** – Project dependencies and metadata

---

## Getting Started

### Prerequisites
- **Python 3.8+**  
- Required packages listed in `pyproject.toml` or `replit.md`

### Installation

git clone https://github.com/swethars04/SentinelVision.git
cd SentinelVision
pip install -r requirements.txt  # or use the appropriate dependency command
Running the Project
python main.py  # or python app.py
# Then visit http://localhost:5000 (or your configured port)

### Usage

Load your video source (e.g., file, live camera feed)

The system displays real-time anomalies on the dashboard

Alerts include type of anomaly, timestamp, and captured frame

Useful in settings like campuses, banks, or parking lots

### Future Development

Emergency Alerts: Automate calls to police or hospitals when a serious incident is detected.

Public Alarms: Trigger audible sirens or public address systems to alert people nearby.

IoT Integration: Link with devices like smart lights, emergency beacons, or drones for rapid response.

Predictive AI: Advance from detection to predictive modeling of potential threats.

Contributing

Contributions are welcome! Please fork the repo, create a feature branch, and raise a Pull Request. For suggestions and bugs, open an Issue in the GitHub portal.

### License

[Specify license here, e.g., MIT, Apache 2.0, etc.]

### Next Steps

1. Copy this template into a new file named `README.md` at the root of your project.
2. Adjust details—like running instructions, project structure, and license—to match your setup.
3. Commit and push the new README:

git add README.md
git commit -m "Add project README"
git push
