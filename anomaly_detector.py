import logging
from collections import defaultdict, deque
import time
import math

class AnomalyDetector:
    def __init__(self):
        # Track objects across frames
        self.tracked_objects = defaultdict(lambda: {
            'positions': deque(maxlen=30),  # Last 30 positions
            'first_seen': None,
            'last_seen': None,
            'stationary_time': 0,
            'movement_history': deque(maxlen=10),
            'class': None
        })
        
        # Track abandoned objects
        self.potential_abandoned_objects = {}
        
        # Configuration
        self.loitering_threshold = 10.0  # seconds
        self.abandoned_object_threshold = 5.0  # seconds
        self.movement_threshold = 20  # pixels
        self.fps = 30
        
        # Zone definitions (can be configured)
        self.restricted_zones = []
        self.monitoring_zones = []
    
    def initialize(self, width, height, fps):
        """Initialize detector with video properties"""
        self.video_width = width
        self.video_height = height
        self.fps = fps
        
        # Define some default monitoring zones
        self.monitoring_zones = [
            {'name': 'entrance', 'bbox': [0, 0, width//3, height//3]},
            {'name': 'center', 'bbox': [width//3, height//3, width//3, height//3]},
            {'name': 'exit', 'bbox': [2*width//3, 2*height//3, width//3, height//3]}
        ]
    
    def detect_anomalies(self, detections, frame_number, timestamp):
        """Main anomaly detection function"""
        anomalies = []
        
        try:
            # Update object tracking
            self.update_tracking(detections, timestamp)
            
            # Detect loitering
            loitering_anomalies = self.detect_loitering(timestamp)
            anomalies.extend(loitering_anomalies)
            
            # Detect abandoned objects
            abandoned_anomalies = self.detect_abandoned_objects(detections, timestamp)
            anomalies.extend(abandoned_anomalies)
            
            # Detect suspicious movement patterns
            movement_anomalies = self.detect_suspicious_movement(timestamp)
            anomalies.extend(movement_anomalies)
            
            # Detect zone violations
            zone_anomalies = self.detect_zone_violations(detections, timestamp)
            anomalies.extend(zone_anomalies)
            
        except Exception as e:
            logging.error(f"Error in anomaly detection: {str(e)}")
        
        return anomalies
    
    def update_tracking(self, detections, timestamp):
        """Update object tracking information"""
        current_objects = set()
        
        for detection in detections:
            # Generate a simple object ID based on position and class
            center_x = detection['bbox'][0] + detection['bbox'][2] // 2
            center_y = detection['bbox'][1] + detection['bbox'][3] // 2
            
            # Find closest tracked object or create new one
            object_id = self.find_or_create_object_id(detection, center_x, center_y, timestamp)
            current_objects.add(object_id)
            
            # Update tracking info
            track_info = self.tracked_objects[object_id]
            track_info['positions'].append((center_x, center_y, timestamp))
            track_info['last_seen'] = timestamp
            track_info['class'] = detection['class']
            
            if track_info['first_seen'] is None:
                track_info['first_seen'] = timestamp
            
            # Calculate movement
            if len(track_info['positions']) > 1:
                prev_pos = track_info['positions'][-2]
                curr_pos = track_info['positions'][-1]
                distance = math.sqrt((curr_pos[0] - prev_pos[0])**2 + (curr_pos[1] - prev_pos[1])**2)
                track_info['movement_history'].append(distance)
                
                # Update stationary time
                if distance < self.movement_threshold:
                    time_diff = curr_pos[2] - prev_pos[2]
                    track_info['stationary_time'] += time_diff
                else:
                    track_info['stationary_time'] = 0
        
        # Clean up old objects
        self.cleanup_old_objects(timestamp, current_objects)
    
    def find_or_create_object_id(self, detection, center_x, center_y, timestamp):
        """Find existing object or create new ID"""
        min_distance = float('inf')
        best_match = None
        
        # Look for nearby objects of the same class
        for obj_id, track_info in self.tracked_objects.items():
            if track_info['class'] == detection['class'] and track_info['positions']:
                last_pos = track_info['positions'][-1]
                distance = math.sqrt((center_x - last_pos[0])**2 + (center_y - last_pos[1])**2)
                
                # Check if object was seen recently and is close enough
                time_diff = timestamp - last_pos[2]
                if distance < 100 and time_diff < 1.0 and distance < min_distance:
                    min_distance = distance
                    best_match = obj_id
        
        if best_match:
            return best_match
        else:
            # Create new object ID
            return f"{detection['class']}_{int(timestamp*1000)}"
    
    def detect_loitering(self, timestamp):
        """Detect people loitering in areas"""
        anomalies = []
        
        for obj_id, track_info in self.tracked_objects.items():
            if track_info['class'] == 'person' and track_info['stationary_time'] > self.loitering_threshold:
                if track_info['positions']:
                    last_pos = track_info['positions'][-1]
                    
                    anomalies.append({
                        'type': 'loitering',
                        'description': f'Person loitering for {track_info["stationary_time"]:.1f} seconds',
                        'severity': 'medium' if track_info['stationary_time'] < 30 else 'high',
                        'start_frame': 0,  # Would need to calculate from timestamp
                        'start_timestamp': track_info['first_seen'],
                        'bbox': self.get_object_bbox(obj_id),
                        'confidence': 0.8,
                        'object_id': obj_id
                    })
        
        return anomalies
    
    def detect_abandoned_objects(self, detections, timestamp):
        """Detect objects that appear without associated person"""
        anomalies = []
        
        # Look for objects that are not persons
        for detection in detections:
            if detection['class'] not in ['person']:
                center_x = detection['bbox'][0] + detection['bbox'][2] // 2
                center_y = detection['bbox'][1] + detection['bbox'][3] // 2
                
                # Check if there's a person nearby
                person_nearby = False
                for other_detection in detections:
                    if other_detection['class'] == 'person':
                        other_center_x = other_detection['bbox'][0] + other_detection['bbox'][2] // 2
                        other_center_y = other_detection['bbox'][1] + other_detection['bbox'][3] // 2
                        distance = math.sqrt((center_x - other_center_x)**2 + (center_y - other_center_y)**2)
                        
                        if distance < 150:  # Person within 150 pixels
                            person_nearby = True
                            break
                
                if not person_nearby:
                    object_key = f"{detection['class']}_{center_x}_{center_y}"
                    
                    if object_key not in self.potential_abandoned_objects:
                        self.potential_abandoned_objects[object_key] = {
                            'first_seen': timestamp,
                            'detection': detection,
                            'confirmed': False
                        }
                    else:
                        abandoned_info = self.potential_abandoned_objects[object_key]
                        time_abandoned = timestamp - abandoned_info['first_seen']
                        
                        if time_abandoned > self.abandoned_object_threshold and not abandoned_info['confirmed']:
                            anomalies.append({
                                'type': 'abandoned_object',
                                'description': f'Abandoned {detection["class"]} detected for {time_abandoned:.1f} seconds',
                                'severity': 'high',
                                'start_frame': 0,
                                'start_timestamp': abandoned_info['first_seen'],
                                'bbox': detection['bbox'],
                                'confidence': 0.9,
                                'object_id': object_key
                            })
                            abandoned_info['confirmed'] = True
        
        return anomalies
    
    def detect_suspicious_movement(self, timestamp):
        """Detect suspicious movement patterns"""
        anomalies = []
        
        for obj_id, track_info in self.tracked_objects.items():
            if track_info['class'] == 'person' and len(track_info['movement_history']) > 5:
                # Calculate average movement speed
                avg_movement = sum(track_info['movement_history']) / len(track_info['movement_history'])
                
                # Detect erratic movement (high variance in movement)
                if len(track_info['movement_history']) > 8:
                    movement_variance = sum((x - avg_movement)**2 for x in track_info['movement_history']) / len(track_info['movement_history'])
                    
                    if movement_variance > 1000:  # High variance threshold
                        anomalies.append({
                            'type': 'suspicious_movement',
                            'description': f'Erratic movement pattern detected',
                            'severity': 'medium',
                            'start_frame': 0,
                            'start_timestamp': track_info['first_seen'],
                            'bbox': self.get_object_bbox(obj_id),
                            'confidence': 0.7,
                            'object_id': obj_id
                        })
        
        return anomalies
    
    def detect_zone_violations(self, detections, timestamp):
        """Detect violations in restricted zones"""
        anomalies = []
        
        # This would be implemented based on specific zone definitions
        # For now, we'll implement a simple version
        
        return anomalies
    
    def get_object_bbox(self, obj_id):
        """Get current bounding box for tracked object"""
        track_info = self.tracked_objects[obj_id]
        if track_info['positions']:
            last_pos = track_info['positions'][-1]
            # Return a default bbox around the last known position
            return [last_pos[0] - 25, last_pos[1] - 25, 50, 50]
        return [0, 0, 50, 50]
    
    def cleanup_old_objects(self, timestamp, current_objects):
        """Remove objects that haven't been seen recently"""
        to_remove = []
        
        for obj_id, track_info in self.tracked_objects.items():
            if obj_id not in current_objects and track_info['last_seen']:
                time_since_seen = timestamp - track_info['last_seen']
                if time_since_seen > 5.0:  # Remove after 5 seconds
                    to_remove.append(obj_id)
        
        for obj_id in to_remove:
            del self.tracked_objects[obj_id]
        
        # Clean up abandoned objects too
        to_remove_abandoned = []
        for obj_key, info in self.potential_abandoned_objects.items():
            if timestamp - info['first_seen'] > 60:  # Remove after 1 minute
                to_remove_abandoned.append(obj_key)
        
        for obj_key in to_remove_abandoned:
            del self.potential_abandoned_objects[obj_key]
