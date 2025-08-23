import cv2
import numpy as np
import logging
import os
import urllib.request

class YOLODetector:
    def __init__(self):
        self.net = None
        self.output_layers = None
        self.classes = []
        self.confidence_threshold = 0.5
        self.nms_threshold = 0.4
        self.load_model()
    
    def load_model(self):
        """Load YOLO model and configuration"""
        try:
            # Use OpenCV's DNN module with pre-trained COCO model
            # Download model files if they don't exist
            weights_path = "yolov3.weights"
            config_path = "yolov3.cfg"
            classes_path = "coco.names"
            
            # Download files if not present
            if not os.path.exists(weights_path):
                logging.info("Downloading YOLOv3 weights...")
                urllib.request.urlretrieve(
                    "https://pjreddie.com/media/files/yolov3.weights",
                    weights_path
                )
            
            if not os.path.exists(config_path):
                logging.info("Downloading YOLOv3 config...")
                urllib.request.urlretrieve(
                    "https://raw.githubusercontent.com/pjreddie/darknet/master/cfg/yolov3.cfg",
                    config_path
                )
            
            if not os.path.exists(classes_path):
                logging.info("Downloading COCO class names...")
                urllib.request.urlretrieve(
                    "https://raw.githubusercontent.com/pjreddie/darknet/master/data/coco.names",
                    classes_path
                )
            
            # Load the network
            self.net = cv2.dnn.readNet(weights_path, config_path)
            
            # Get output layer names
            layer_names = self.net.getLayerNames()
            self.output_layers = [layer_names[i - 1] for i in self.net.getUnconnectedOutLayers()]
            
            # Load class names
            with open(classes_path, 'r') as f:
                self.classes = [line.strip() for line in f.readlines()]
            
            logging.info("YOLO model loaded successfully")
            
        except Exception as e:
            logging.error(f"Failed to load YOLO model: {str(e)}")
            # Fallback to OpenCV's built-in object detection
            self.use_fallback_detection = True
    
    def detect(self, frame):
        """Detect objects in frame"""
        try:
            if self.net is None:
                return self.fallback_detection(frame)
            
            height, width, channels = frame.shape
            
            # Prepare input blob
            blob = cv2.dnn.blobFromImage(frame, 0.00392, (416, 416), (0, 0, 0), True, crop=False)
            self.net.setInput(blob)
            
            # Run inference
            outputs = self.net.forward(self.output_layers)
            
            # Process outputs
            boxes = []
            confidences = []
            class_ids = []
            
            for output in outputs:
                for detection in output:
                    scores = detection[5:]
                    class_id = np.argmax(scores)
                    confidence = scores[class_id]
                    
                    if confidence > self.confidence_threshold:
                        # Object detected
                        center_x = int(detection[0] * width)
                        center_y = int(detection[1] * height)
                        w = int(detection[2] * width)
                        h = int(detection[3] * height)
                        
                        # Rectangle coordinates
                        x = int(center_x - w / 2)
                        y = int(center_y - h / 2)
                        
                        boxes.append([x, y, w, h])
                        confidences.append(float(confidence))
                        class_ids.append(class_id)
            
            # Apply non-maximum suppression
            indexes = cv2.dnn.NMSBoxes(boxes, confidences, self.confidence_threshold, self.nms_threshold)
            
            detections = []
            if len(indexes) > 0:
                for i in indexes.flatten():
                    x, y, w, h = boxes[i]
                    class_name = self.classes[class_ids[i]] if class_ids[i] < len(self.classes) else "unknown"
                    
                    detections.append({
                        'class': class_name,
                        'confidence': confidences[i],
                        'bbox': [x, y, w, h]
                    })
            
            return detections
            
        except Exception as e:
            logging.error(f"Error in YOLO detection: {str(e)}")
            return self.fallback_detection(frame)
    
    def fallback_detection(self, frame):
        """Fallback detection using OpenCV's built-in methods"""
        detections = []
        
        try:
            # Use HOG descriptor for person detection
            hog = cv2.HOGDescriptor()
            hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
            
            # Detect people
            boxes, weights = hog.detectMultiScale(frame, winStride=(8, 8))
            
            for (x, y, w, h) in boxes:
                detections.append({
                    'class': 'person',
                    'confidence': 0.7,  # Default confidence for HOG detection
                    'bbox': [x, y, w, h]
                })
            
            # Use background subtraction for moving objects
            if not hasattr(self, 'bg_subtractor'):
                self.bg_subtractor = cv2.createBackgroundSubtractorMOG2()
            
            fg_mask = self.bg_subtractor.apply(frame)
            contours, _ = cv2.findContours(fg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for contour in contours:
                area = cv2.contourArea(contour)
                if area > 500:  # Filter small objects
                    x, y, w, h = cv2.boundingRect(contour)
                    detections.append({
                        'class': 'moving_object',
                        'confidence': 0.6,
                        'bbox': [x, y, w, h]
                    })
            
        except Exception as e:
            logging.error(f"Error in fallback detection: {str(e)}")
        
        return detections
