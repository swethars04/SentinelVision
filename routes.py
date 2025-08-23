import os
import json
import logging
from flask import render_template, request, redirect, url_for, flash, jsonify, send_from_directory
from werkzeug.utils import secure_filename
from app import app, db
from models import VideoAnalysis, DetectedObject, Anomaly, Alert
from video_processor import VideoProcessor
import threading
from datetime import datetime

ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv', 'flv', 'wmv'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    """Main dashboard showing recent analyses and alerts"""
    recent_analyses = VideoAnalysis.query.order_by(VideoAnalysis.upload_time.desc()).limit(5).all()
    recent_alerts = Alert.query.join(Anomaly).join(VideoAnalysis).order_by(Alert.created_time.desc()).limit(10).all()
    
    # Get statistics
    total_videos = VideoAnalysis.query.count()
    total_anomalies = Anomaly.query.count()
    unresolved_anomalies = Anomaly.query.filter_by(is_resolved=False).count()
    active_alerts = Alert.query.filter_by(is_acknowledged=False).count()
    
    stats = {
        'total_videos': total_videos,
        'total_anomalies': total_anomalies,
        'unresolved_anomalies': unresolved_anomalies,
        'active_alerts': active_alerts
    }
    
    return render_template('index.html', 
                         recent_analyses=recent_analyses, 
                         recent_alerts=recent_alerts,
                         stats=stats)

@app.route('/upload')
def upload_page():
    """Video upload page"""
    return render_template('upload.html')

@app.route('/upload', methods=['POST'])
def upload_video():
    """Handle video upload and start processing"""
    if 'video' not in request.files:
        flash('No video file selected', 'error')
        return redirect(request.url)
    
    file = request.files['video']
    if file.filename == '':
        flash('No file selected', 'error')
        return redirect(request.url)
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        # Add timestamp to avoid conflicts
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
        filename = timestamp + filename
        
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Create database entry
        analysis = VideoAnalysis(
            filename=filename,
            file_path=filepath,
            processing_status='pending'
        )
        db.session.add(analysis)
        db.session.commit()
        
        # Start processing in background thread
        processor = VideoProcessor()
        thread = threading.Thread(target=processor.process_video, args=(analysis.id,))
        thread.daemon = True
        thread.start()
        
        flash(f'Video "{file.filename}" uploaded successfully and processing started!', 'success')
        return redirect(url_for('dashboard'))
    else:
        flash('Invalid file type. Please upload MP4, AVI, MOV, MKV, FLV, or WMV files only.', 'error')
        return redirect(request.url)

@app.route('/dashboard')
def dashboard():
    """Main surveillance dashboard"""
    analyses = VideoAnalysis.query.order_by(VideoAnalysis.upload_time.desc()).all()
    return render_template('dashboard.html', analyses=analyses)

@app.route('/analysis/<int:analysis_id>')
def analysis_detail(analysis_id):
    """Detailed analysis view for a specific video"""
    analysis = VideoAnalysis.query.get_or_404(analysis_id)
    anomalies = Anomaly.query.filter_by(video_analysis_id=analysis_id).order_by(Anomaly.start_timestamp).all()
    alerts = Alert.query.join(Anomaly).filter(Anomaly.video_analysis_id == analysis_id).order_by(Alert.created_time.desc()).all()
    
    return render_template('analysis.html', 
                         analysis=analysis, 
                         anomalies=anomalies, 
                         alerts=alerts)

@app.route('/api/analysis/<int:analysis_id>/status')
def get_analysis_status(analysis_id):
    """API endpoint to get analysis status"""
    analysis = VideoAnalysis.query.get_or_404(analysis_id)
    return jsonify({
        'status': analysis.processing_status,
        'processed_frames': analysis.processed_frames,
        'total_frames': analysis.total_frames,
        'progress': (analysis.processed_frames / analysis.total_frames * 100) if analysis.total_frames else 0
    })

@app.route('/api/alerts')
def get_alerts():
    """API endpoint to get recent alerts"""
    alerts = Alert.query.join(Anomaly).join(VideoAnalysis).order_by(Alert.created_time.desc()).limit(20).all()
    
    alert_data = []
    for alert in alerts:
        alert_data.append({
            'id': alert.id,
            'level': alert.alert_level,
            'message': alert.message,
            'created_time': alert.created_time.isoformat(),
            'is_acknowledged': alert.is_acknowledged,
            'anomaly_type': alert.anomaly_id and Anomaly.query.get(alert.anomaly_id).anomaly_type,
            'video_filename': alert.anomaly_id and Anomaly.query.get(alert.anomaly_id).video_analysis_id and VideoAnalysis.query.get(Anomaly.query.get(alert.anomaly_id).video_analysis_id).filename
        })
    
    return jsonify(alert_data)

@app.route('/api/alerts/<int:alert_id>/acknowledge', methods=['POST'])
def acknowledge_alert(alert_id):
    """API endpoint to acknowledge an alert"""
    alert = Alert.query.get_or_404(alert_id)
    alert.is_acknowledged = True
    alert.acknowledged_time = datetime.utcnow()
    alert.acknowledged_by = request.json.get('acknowledged_by', 'System')
    
    db.session.commit()
    
    return jsonify({'success': True})

@app.route('/api/anomalies/<int:anomaly_id>/resolve', methods=['POST'])
def resolve_anomaly(anomaly_id):
    """API endpoint to mark anomaly as resolved"""
    anomaly = Anomaly.query.get_or_404(anomaly_id)
    anomaly.is_resolved = True
    
    db.session.commit()
    
    return jsonify({'success': True})

@app.route('/video/<path:filename>')
def serve_video(filename):
    """Serve video files"""
    response = send_from_directory(app.config['UPLOAD_FOLDER'], filename)
    response.headers['Accept-Ranges'] = 'bytes'
    return response

@app.route('/processed/<path:filename>')
def serve_processed_video(filename):
    """Serve processed video files with annotations"""
    response = send_from_directory(app.config['PROCESSED_FOLDER'], filename)
    response.headers['Accept-Ranges'] = 'bytes'
    return response

@app.route('/api/analysis/<int:analysis_id>', methods=['DELETE'])
def delete_analysis(analysis_id):
    """API endpoint to delete a video analysis and all related data"""
    try:
        analysis = VideoAnalysis.query.get_or_404(analysis_id)
        
        # First, get all anomaly IDs for this analysis
        anomaly_ids = [anomaly.id for anomaly in Anomaly.query.filter_by(video_analysis_id=analysis_id).all()]
        
        # Delete related alerts using the anomaly IDs
        if anomaly_ids:
            Alert.query.filter(Alert.anomaly_id.in_(anomaly_ids)).delete(synchronize_session=False)
        
        # Delete anomalies
        Anomaly.query.filter_by(video_analysis_id=analysis_id).delete()
        
        # Delete detected objects
        DetectedObject.query.filter_by(video_analysis_id=analysis_id).delete()
        
        # Delete video files from filesystem
        if analysis.file_path and os.path.exists(analysis.file_path):
            try:
                os.remove(analysis.file_path)
            except OSError:
                pass  # File might already be deleted
        
        if analysis.processed_video_path and os.path.exists(analysis.processed_video_path):
            try:
                os.remove(analysis.processed_video_path)
            except OSError:
                pass  # File might already be deleted
        
        # Delete the analysis record
        db.session.delete(analysis)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Analysis deleted successfully'})
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error deleting analysis {analysis_id}: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/statistics')
def get_statistics():
    """API endpoint for dashboard statistics"""
    from sqlalchemy import func, desc
    from datetime import datetime, timedelta
    
    # Basic stats
    stats = {
        'total_videos': VideoAnalysis.query.count(),
        'processing_videos': VideoAnalysis.query.filter_by(processing_status='processing').count(),
        'completed_videos': VideoAnalysis.query.filter_by(processing_status='completed').count(),
        'failed_videos': VideoAnalysis.query.filter_by(processing_status='failed').count(),
        'total_anomalies': Anomaly.query.count(),
        'unresolved_anomalies': Anomaly.query.filter_by(is_resolved=False).count(),
        'total_alerts': Alert.query.count(),
        'unacknowledged_alerts': Alert.query.filter_by(is_acknowledged=False).count(),
        'anomaly_types': {}
    }
    
    # Get anomaly type distribution
    anomaly_counts = db.session.query(
        Anomaly.anomaly_type, 
        func.count(Anomaly.id).label('count')
    ).group_by(Anomaly.anomaly_type).all()
    
    for anomaly_type, count in anomaly_counts:
        stats['anomaly_types'][anomaly_type] = count
    
    # Get daily data for the last 7 days
    end_date = datetime.now()
    start_date = end_date - timedelta(days=6)  # Last 7 days including today
    
    # Initialize daily data
    daily_videos = []
    daily_anomalies = []
    daily_labels = []
    
    for i in range(7):
        current_date = start_date + timedelta(days=i)
        daily_labels.append(current_date.strftime('%a'))  # Mon, Tue, etc.
        
        # Count videos uploaded on this day
        video_count = VideoAnalysis.query.filter(
            func.date(VideoAnalysis.upload_time) == current_date.date()
        ).count()
        daily_videos.append(video_count)
        
        # Count anomalies detected on this day
        anomaly_count = Anomaly.query.filter(
            func.date(Anomaly.detected_time) == current_date.date()
        ).count()
        daily_anomalies.append(anomaly_count)
    
    # Add daily data to stats
    stats['daily_videos'] = daily_videos
    stats['daily_anomalies'] = daily_anomalies
    stats['daily_labels'] = daily_labels
    
    return jsonify(stats)
