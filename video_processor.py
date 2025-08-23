import cv2
import os
import logging
from app import app, db
from models import VideoAnalysis, DetectedObject, Anomaly, Alert
from yolo_detector import YOLODetector
from anomaly_detector import AnomalyDetector

class VideoProcessor:
    def __init__(self):
        self.yolo = YOLODetector()
        self.anomaly_detector = AnomalyDetector()
        
    def process_video(self, analysis_id):
        """Process video for object detection and anomaly detection"""
        with app.app_context():
            try:
                analysis = VideoAnalysis.query.get(analysis_id)
                if not analysis:
                    logging.error(f"Analysis {analysis_id} not found")
                    return
                
                logging.info(f"Starting processing for video: {analysis.filename}")
                analysis.processing_status = 'processing'
                db.session.commit()
                
                # Open video file
                cap = cv2.VideoCapture(analysis.file_path)
                if not cap.isOpened():
                    raise Exception("Could not open video file")
                
                # Get video properties
                fps = cap.get(cv2.CAP_PROP_FPS)
                total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                duration = total_frames / fps if fps > 0 else 0
                width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                
                analysis.total_frames = total_frames
                analysis.duration = duration
                db.session.commit()
                
                # Setup output video writer for annotated video
                processed_filename = f"processed_{analysis.filename}"
                processed_path = os.path.join(app.config['PROCESSED_FOLDER'], processed_filename)
                fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                out = cv2.VideoWriter(processed_path, fourcc, fps, (width, height))
                
                frame_number = 0
                detected_objects_buffer = []
                
                # Initialize anomaly detector
                self.anomaly_detector.initialize(width, height, fps)
                
                while True:
                    ret, frame = cap.read()
                    if not ret:
                        break
                    
                    timestamp = frame_number / fps
                    
                    # Run YOLO detection
                    detections = self.yolo.detect(frame)
                    
                    # Process detections
                    for detection in detections:
                        # Save to database
                        detected_obj = DetectedObject(
                            video_analysis_id=analysis_id,
                            frame_number=frame_number,
                            timestamp=timestamp,
                            class_name=detection['class'],
                            confidence=detection['confidence'],
                            bbox_x=detection['bbox'][0],
                            bbox_y=detection['bbox'][1],
                            bbox_width=detection['bbox'][2],
                            bbox_height=detection['bbox'][3],
                            object_id=detection.get('track_id', f"{detection['class']}_{frame_number}")
                        )
                        db.session.add(detected_obj)
                        detected_objects_buffer.append(detection)
                    
                    # Run anomaly detection
                    anomalies = self.anomaly_detector.detect_anomalies(detections, frame_number, timestamp)
                    
                    for anomaly_data in anomalies:
                        # Create anomaly record
                        anomaly = Anomaly(
                            video_analysis_id=analysis_id,
                            anomaly_type=anomaly_data['type'],
                            description=anomaly_data['description'],
                            severity=anomaly_data['severity'],
                            start_frame=anomaly_data['start_frame'],
                            start_timestamp=anomaly_data['start_timestamp'],
                            bbox_x=anomaly_data.get('bbox', [0, 0, 0, 0])[0],
                            bbox_y=anomaly_data.get('bbox', [0, 0, 0, 0])[1],
                            bbox_width=anomaly_data.get('bbox', [0, 0, 0, 0])[2],
                            bbox_height=anomaly_data.get('bbox', [0, 0, 0, 0])[3],
                            confidence=anomaly_data['confidence']
                        )
                        db.session.add(anomaly)
                        db.session.flush()  # Get the ID
                        
                        # Create alert for high severity anomalies
                        if anomaly_data['severity'] in ['high', 'critical']:
                            alert_level = 'danger' if anomaly_data['severity'] == 'critical' else 'warning'
                            alert = Alert(
                                anomaly_id=anomaly.id,
                                alert_level=alert_level,
                                message=f"{anomaly_data['type'].replace('_', ' ').title()} detected: {anomaly_data['description']}"
                            )
                            db.session.add(alert)
                    
                    # Draw annotations on frame
                    annotated_frame = self.draw_annotations(frame, detections, anomalies)
                    out.write(annotated_frame)
                    
                    # Update progress
                    frame_number += 1
                    analysis.processed_frames = frame_number
                    
                    # Commit every 30 frames to avoid too many commits
                    if frame_number % 30 == 0:
                        db.session.commit()
                        logging.info(f"Processed {frame_number}/{total_frames} frames ({frame_number/total_frames*100:.1f}%)")
                
                # Final cleanup
                cap.release()
                out.release()
                
                # Update analysis statistics
                total_objects = DetectedObject.query.filter_by(video_analysis_id=analysis_id).count()
                total_persons = DetectedObject.query.filter_by(video_analysis_id=analysis_id, class_name='person').count()
                total_anomalies = Anomaly.query.filter_by(video_analysis_id=analysis_id).count()
                
                analysis.total_objects_detected = total_objects
                analysis.total_persons_detected = total_persons
                analysis.total_anomalies = total_anomalies
                analysis.processed_video_path = processed_path
                analysis.processing_status = 'completed'
                
                db.session.commit()
                logging.info(f"Video processing completed: {analysis.filename}")
                
            except Exception as e:
                logging.error(f"Error processing video {analysis_id}: {str(e)}")
                if analysis:
                    analysis.processing_status = 'failed'
                    db.session.commit()
    
    def draw_annotations(self, frame, detections, anomalies):
        """Draw bounding boxes and annotations on frame"""
        annotated_frame = frame.copy()
        
        # Draw object detections
        for detection in detections:
            bbox = detection['bbox']
            x, y, w, h = int(bbox[0]), int(bbox[1]), int(bbox[2]), int(bbox[3])
            
            # Different colors for different classes
            if detection['class'] == 'person':
                color = (0, 255, 0)  # Green for persons
            else:
                color = (255, 0, 0)  # Blue for other objects
            
            cv2.rectangle(annotated_frame, (x, y), (x + w, y + h), color, 2)
            
            # Add label
            label = f"{detection['class']}: {detection['confidence']:.2f}"
            label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)[0]
            cv2.rectangle(annotated_frame, (x, y - label_size[1] - 10), (x + label_size[0], y), color, -1)
            cv2.putText(annotated_frame, label, (x, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
        
        # Draw anomaly alerts
        for anomaly_data in anomalies:
            if 'bbox' in anomaly_data and anomaly_data['bbox']:
                bbox = anomaly_data['bbox']
                x, y, w, h = int(bbox[0]), int(bbox[1]), int(bbox[2]), int(bbox[3])
                
                # Red color for anomalies
                color = (0, 0, 255)
                cv2.rectangle(annotated_frame, (x, y), (x + w, y + h), color, 3)
                
                # Add anomaly label
                label = f"ANOMALY: {anomaly_data['type']}"
                label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)[0]
                cv2.rectangle(annotated_frame, (x, y - label_size[1] - 15), (x + label_size[0], y), color, -1)
                cv2.putText(annotated_frame, label, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        return annotated_frame
