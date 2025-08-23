# AI-Powered Surveillance System

## Overview

This is a comprehensive AI-powered surveillance system designed to analyze video feeds and detect behavioral anomalies. The system processes uploaded video files to identify objects, track movement patterns, and automatically detect suspicious activities such as loitering, abandoned objects, and unusual movements. Built with Flask as the web framework, it provides a dashboard for monitoring video analyses, managing alerts, and viewing detection results in real-time.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Web Framework
- **Flask Application**: Core web server using Flask with SQLAlchemy for database operations
- **Template Engine**: Jinja2 templates with Bootstrap dark theme for responsive UI
- **Static Assets**: CSS and JavaScript for enhanced user experience and real-time dashboard updates

### Database Layer
- **SQLAlchemy ORM**: Database abstraction with support for SQLite (default) and PostgreSQL
- **Data Models**: Four main entities - VideoAnalysis (processing metadata), DetectedObject (object detection results), Anomaly (behavioral anomalies), and Alert (notification system)
- **Relationships**: Foreign key relationships linking video analyses to their detected objects and anomalies

### AI/ML Processing Pipeline
- **YOLO Object Detection**: YOLOv3 model using OpenCV's DNN module for real-time object detection
- **Anomaly Detection**: Custom behavioral analysis system tracking object movement patterns, loitering detection, and abandoned object identification
- **Video Processing**: Frame-by-frame analysis with object tracking across temporal sequences

### File Management
- **Upload System**: Secure file upload with validation for video formats (MP4, AVI, MOV, etc.)
- **Processing Pipeline**: Background video processing with status tracking and progress monitoring
- **Storage Structure**: Separate directories for uploaded and processed videos with annotated output

### Detection Capabilities
- **Object Classes**: COCO dataset classes with focus on person detection
- **Behavioral Analysis**: Loitering detection (configurable time thresholds), abandoned object detection, suspicious movement patterns
- **Tracking System**: Multi-object tracking across frames with position history and movement analysis

### User Interface
- **Dashboard**: Real-time statistics, recent analyses, and active alerts overview
- **Analysis Views**: Detailed video analysis results with object detection timelines
- **Alert Management**: Alert acknowledgment and resolution tracking system
- **Upload Interface**: Drag-and-drop video upload with processing options

## External Dependencies

### AI/ML Libraries
- **OpenCV**: Core computer vision library for video processing and YOLO model inference
- **NumPy**: Numerical computing for array operations and mathematical functions
- **YOLOv3**: Pre-trained object detection model downloaded from official sources

### Web Technologies
- **Flask**: Lightweight WSGI web application framework
- **SQLAlchemy**: Python SQL toolkit and Object-Relational Mapping library
- **Bootstrap**: Frontend framework for responsive web design
- **Font Awesome**: Icon library for user interface elements

### Infrastructure
- **Werkzeug**: WSGI utility library for handling HTTP requests and file uploads
- **Threading**: Python threading for background video processing
- **Logging**: Built-in Python logging for system monitoring and debugging

### External Resources
- **COCO Dataset**: Class names and model configuration files
- **YOLOv3 Weights**: Pre-trained model weights downloaded from official repository
- **CDN Resources**: Bootstrap CSS, Font Awesome icons served from content delivery networks