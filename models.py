from extensions import db
from datetime import datetime
from sqlalchemy import Text, DateTime, Float, Integer, String, Boolean

class VideoAnalysis(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    upload_time = db.Column(db.DateTime, default=datetime.utcnow)
    processing_status = db.Column(db.String(50), default='pending')  # pending, processing, completed, failed
    total_frames = db.Column(db.Integer)
    processed_frames = db.Column(db.Integer, default=0)
    duration = db.Column(db.Float)
    file_path = db.Column(db.String(500))
    processed_video_path = db.Column(db.String(500))
    
    # Analysis results
    total_objects_detected = db.Column(db.Integer, default=0)
    total_persons_detected = db.Column(db.Integer, default=0)
    total_anomalies = db.Column(db.Integer, default=0)
    
    def __repr__(self):
        return f'<VideoAnalysis {self.filename}>'
    pass

class DetectedObject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    video_analysis_id = db.Column(db.Integer, db.ForeignKey('video_analysis.id'), nullable=False)
    frame_number = db.Column(db.Integer, nullable=False)
    timestamp = db.Column(db.Float, nullable=False)  # Time in seconds from start
    class_name = db.Column(db.String(100), nullable=False)
    confidence = db.Column(db.Float, nullable=False)
    bbox_x = db.Column(db.Float, nullable=False)
    bbox_y = db.Column(db.Float, nullable=False)
    bbox_width = db.Column(db.Float, nullable=False)
    bbox_height = db.Column(db.Float, nullable=False)
    object_id = db.Column(db.String(100))  # For tracking across frames
    
    def __repr__(self):
        return f'<DetectedObject {self.class_name} at frame {self.frame_number}>'
    pass
class Anomaly(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    video_analysis_id = db.Column(db.Integer, db.ForeignKey('video_analysis.id'), nullable=False)
    anomaly_type = db.Column(db.String(100), nullable=False)  # loitering, abandoned_object, suspicious_movement
    description = db.Column(db.Text)
    severity = db.Column(db.String(20), default='medium')  # low, medium, high, critical
    start_frame = db.Column(db.Integer, nullable=False)
    end_frame = db.Column(db.Integer)
    start_timestamp = db.Column(db.Float, nullable=False)
    end_timestamp = db.Column(db.Float)
    bbox_x = db.Column(db.Float)
    bbox_y = db.Column(db.Float)
    bbox_width = db.Column(db.Float)
    bbox_height = db.Column(db.Float)
    confidence = db.Column(db.Float, default=0.5)
    detected_time = db.Column(db.DateTime, default=datetime.utcnow)
    is_resolved = db.Column(db.Boolean, default=False)
    
    def __repr__(self):
        return f'<Anomaly {self.anomaly_type} at {self.start_timestamp}s>'
    pass
class Alert(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    anomaly_id = db.Column(db.Integer, db.ForeignKey('anomaly.id'), nullable=False)
    alert_level = db.Column(db.String(20), default='warning')  # info, warning, danger, critical
    message = db.Column(db.Text, nullable=False)
    created_time = db.Column(db.DateTime, default=datetime.utcnow)
    is_acknowledged = db.Column(db.Boolean, default=False)
    acknowledged_by = db.Column(db.String(100))
    acknowledged_time = db.Column(db.DateTime)
    
    def __repr__(self):
        return f'<Alert {self.alert_level} - {self.message[:50]}>'
    pass
