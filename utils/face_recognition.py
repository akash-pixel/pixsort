import os
import json
import numpy as np
from PyQt5.QtWidgets import QApplication
from database.models import Face, Image
from insightface.app import FaceAnalysis 
from retinaface import RetinaFace
import cv2
import logging
from typing import Tuple, Dict, List, Optional
import uuid

from utils.helper import generate_random_number

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('FaceRecognitionProcessor')

class FaceRecognitionProcessor:
    def __init__(self, db_manager, similarity_threshold: float = 0.6, det_size: Tuple[int, int] = (640, 640)):
        """
        Initialize the face recognition processor.
        
        Args:
            db_manager: Database manager instance
            similarity_threshold: Threshold for face matching (lower is stricter)
            det_size: Detection size for face analysis
        """
        self.db_manager = db_manager
        self.known_face_encodings: Dict[str, List[np.ndarray]] = {}
        self.similarity_threshold = similarity_threshold
        self.det_size = det_size
        self.face_analyzer = None
        self.load_known_faces()
        
    def _init_face_analyzer(self):
        """Initialize the face analyzer only when needed to save resources"""
        if self.face_analyzer is None:
            try:
                self.face_analyzer = FaceAnalysis()
                self.face_analyzer.prepare(ctx_id=0, det_size=self.det_size)
                logger.info("Face analyzer initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize face analyzer: {str(e)}")
                raise
    
    def load_known_faces(self):
        """Load known face encodings from database"""
        try:
            faces = self.db_manager.session.query(Face).all()
            face_count = 0
            
            for face in faces:
                if face.person_name and face.face_encoding:
                    try:
                        encoding = np.frombuffer(json.loads(face.face_encoding), dtype=np.float32)
                        if face.person_name not in self.known_face_encodings:
                            self.known_face_encodings[face.person_name] = []
                        self.known_face_encodings[face.person_name].append(encoding)
                        face_count += 1
                    except Exception as e:
                        logger.warning(f"Failed to load face encoding for {face.id}: {str(e)}")
            
            logger.info(f"Loaded {face_count} face encodings for {len(self.known_face_encodings)} unique persons")
        except Exception as e:
            logger.error(f"Error loading known faces: {str(e)}")
            raise
    
    def process_images(self, batch_size: int = 50) -> Tuple[int, int]:
        """
        Process images in the database to detect faces
        
        Args:
            batch_size: Number of images to process before yielding to UI
            
        Returns:
            Tuple of (processed_count, detected_face_count)
        """
        processed = 0
        detected = 0
        
        try:
            # Initialize face analyzer when needed
            self._init_face_analyzer()
            
            # Get all unprocessed images from the database
            images = self.db_manager.session.query(Image).filter(Image.processed == False).all()
            total_images = len(images)
            logger.info(f"Starting to process {total_images} images")
            
            for image in images:
                if not os.path.exists(image.file_path):
                    logger.warning(f"Image file not found: {image.file_path}")
                    continue
                    
                # Only process images (not videos)
                ext = os.path.splitext(image.file_path)[1].lower()
                if ext not in ['.jpg', '.jpeg', '.png']:
                    logger.debug(f"Skipping non-image file: {image.file_path}")
                    continue
                    
                try:
                    img = cv2.imread(image.file_path)
                    if img is None:
                        logger.warning(f"Failed to read image: {image.file_path}")
                        continue
                        
                    # Process faces in the image
                    faces = RetinaFace.detect_faces(img)
                    image_faces_detected = 0
                    
                    if faces:
                        for key in faces:
                            identity = faces[key]
                            facial_area = identity["facial_area"]
                            x1, y1, x2, y2 = facial_area
                            
                            # Validate facial area coordinates
                            if x1 >= x2 or y1 >= y2 or x1 < 0 or y1 < 0 or x2 > img.shape[1] or y2 > img.shape[0]:
                                logger.warning(f"Invalid facial area in {image.file_path}: {facial_area}")
                                continue

                            # Extract face ROI with padding
                            try:
                                # Add padding (5% on each side)
                                height, width = img.shape[:2]
                                pad_x = int((x2 - x1) * 0.05)
                                pad_y = int((y2 - y1) * 0.05)
                                
                                # Ensure padded coordinates are within image bounds
                                x1_pad = max(0, x1 - pad_x)
                                y1_pad = max(0, y1 - pad_y)
                                x2_pad = min(width, x2 + pad_x)
                                y2_pad = min(height, y2 + pad_y)
                                
                                face_roi = img[y1_pad:y2_pad, x1_pad:x2_pad]
                                # Check if ROI is valid
                                if face_roi.size == 0 or face_roi.shape[0] == 0 or face_roi.shape[1] == 0:
                                    logger.warning(f"Empty face ROI in {image.file_path}")
                                    continue
                            except Exception as e:
                                logger.warning(f"Error extracting face ROI: {str(e)}")
                                continue

                            # Get face embedding using InsightFace
                            try:
                                face_data = self.face_analyzer.get(face_roi)
                                
                                if face_data and len(face_data) > 0:
                                    encoding = face_data[0].embedding  # Extract face encoding
                                    if encoding is None or len(encoding) == 0:
                                        logger.warning("Empty face embedding returned")
                                        continue
                                        
                                    matched = False
                                    person_name = None
                                    best_match_score = float('inf')
                                    best_match_name = None

                                    # Compare with known faces
                                    for name, known_encodings in self.known_face_encodings.items():
                                        for known_encoding in known_encodings:
                                            # Ensure compatible shapes for comparison
                                            if known_encoding.shape != encoding.shape:
                                                continue
                                                
                                            # Calculate distance
                                            distance = np.linalg.norm(known_encoding - encoding)
                                            
                                            # Update best match if better
                                            if distance < best_match_score:
                                                best_match_score = distance
                                                best_match_name = name
                                            
                                            # Check if match found
                                            if distance < self.similarity_threshold:
                                                person_name = name
                                                matched = True
                                                break
                                        
                                        if matched:
                                            break

                                    # If no match found but we have a closest match under a relaxed threshold
                                    if not matched:
                                        relaxed_threshold = self.similarity_threshold * 1.2  # 20% more lenient
                                        if best_match_score < relaxed_threshold:
                                            person_name = best_match_name
                                            logger.info(f"Using relaxed threshold match: {person_name} (score: {best_match_score:.3f})")
                                        else:
                                            # Generate unique person identifier
                                            person_name = f"Unknown_{uuid.uuid4().hex[:8]}"
                                            
                                            # Store new face encoding
                                            if person_name not in self.known_face_encodings:
                                                self.known_face_encodings[person_name] = []
                                            self.known_face_encodings[person_name].append(encoding)
                                            logger.info(f"New person detected: {person_name}")

                                    # Save landmarks if available
                                    landmarks = None
                                    if "landmarks" in identity:
                                        landmarks = json.dumps(identity["landmarks"])
                                        
                                    # Save confidence if available
                                    confidence = None
                                    if "score" in identity:
                                        confidence = float(identity["score"])

                                    # Save face to database
                                    encoding_json = json.dumps(encoding.tolist())
                                    facial_area_json = json.dumps(facial_area)
                                    
                                    # Call the updated add_face method with new parameters
                                    self.db_manager.add_face(
                                        image_id=image.id,
                                        person_name=person_name,
                                        face_encoding=encoding_json,
                                        facial_area=facial_area_json,
                                        landmarks=landmarks,
                                        confidence=confidence
                                    )
                                    
                                    detected += 1
                                    image_faces_detected += 1
                                else:
                                    logger.warning(f"No face data returned for detected face in {image.file_path}")
                            except Exception as e:
                                logger.warning(f"Error processing face embedding: {str(e)}")
                    
                    # Mark image as processed and update face count
                    self.db_manager.update_image_processed_status(image.id, True, image_faces_detected)
                    processed += 1
                    
                    # Keep UI responsive by processing events every batch_size images
                    if processed % batch_size == 0:
                        QApplication.processEvents()
                        logger.info(f"Processed {processed}/{total_images} images, detected {detected} faces")
                        
                except Exception as e:
                    logger.error(f"Error processing image {image.file_path}: {str(e)}")
                    # Continue with next image
            
            logger.info(f"Processing complete. Processed {processed} images, detected {detected} faces")
            return processed, detected
            
        except Exception as e:
            logger.error(f"Fatal error in process_images: {str(e)}")
            return processed, detected
            
    def add_person(self, person_name: str, face_image_path: str) -> bool:
        """
        Add a new person with reference face image
        
        Args:
            person_name: Name of the person to add
            face_image_path: Path to a clear face image of the person
            
        Returns:
            bool: Success status
        """
        try:
            # Initialize face analyzer when needed
            self._init_face_analyzer()
            
            # Read the image
            img = cv2.imread(face_image_path)
            if img is None:
                logger.error(f"Failed to read image: {face_image_path}")
                return False
                
            # Detect faces
            faces = RetinaFace.detect_faces(img)
            if not faces:
                logger.error(f"No faces detected in: {face_image_path}")
                return False
                
            # Use the face with highest confidence
            best_face = None
            best_score = -1
            
            for key in faces:
                identity = faces[key]
                if "score" in identity and float(identity["score"]) > best_score:
                    best_score = float(identity["score"])
                    best_face = identity
            
            if best_face is None:
                logger.error("No valid face found")
                return False
                
            # Extract face area
            facial_area = best_face["facial_area"]
            x1, y1, x2, y2 = facial_area
            
            # Add padding
            height, width = img.shape[:2]
            pad_x = int((x2 - x1) * 0.05)
            pad_y = int((y2 - y1) * 0.05)
            
            # Ensure padded coordinates are within image bounds
            x1_pad = max(0, x1 - pad_x)
            y1_pad = max(0, y1 - pad_y)
            x2_pad = min(width, x2 + pad_x)
            y2_pad = min(height, y2 + pad_y)
            
            face_roi = img[y1_pad:y2_pad, x1_pad:x2_pad]
            
            # Get face embedding
            face_data = self.face_analyzer.get(face_roi)
            if not face_data or len(face_data) == 0:
                logger.error("Failed to get face embedding")
                return False
                
            encoding = face_data[0].embedding
            
            # Store the face encoding
            if person_name not in self.known_face_encodings:
                self.known_face_encodings[person_name] = []
            self.known_face_encodings[person_name].append(encoding)
            
            # You might want to save this reference face to the database
            # For now, we'll just keep it in memory
            
            logger.info(f"Added new person: {person_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding person: {str(e)}")
            return False
            
    def set_similarity_threshold(self, threshold: float) -> None:
        """
        Set the similarity threshold for face matching
        
        Args:
            threshold: New threshold (lower is stricter)
        """
        if 0 < threshold < 2.0:  # Reasonable range for cosine/euclidean distance
            self.similarity_threshold = threshold
            logger.info(f"Face similarity threshold set to {threshold}")
        else:
            logger.warning(f"Invalid threshold value: {threshold}. Must be between 0 and 2.0")
            
    def rename_person(self, old_name: str, new_name: str) -> bool:
        """
        Rename a person both in memory and database
        
        Args:
            old_name: Current name of the person
            new_name: New name to assign
            
        Returns:
            bool: Success status
        """
        try:
            # First update in memory
            if old_name in self.known_face_encodings:
                self.known_face_encodings[new_name] = self.known_face_encodings.pop(old_name)
                
            # Then update in database
            count = self.db_manager.update_person_name(old_name, new_name)
            logger.info(f"Renamed person '{old_name}' to '{new_name}' (updated {count} faces)")
            return True
        except Exception as e:
            logger.error(f"Error renaming person: {str(e)}")
            return False
            
    def search_person_by_image(self, image_path: str) -> List[dict]:
        """
        Search for people in an image
        
        Args:
            image_path: Path to the image to search
            
        Returns:
            List of dictionaries with person information
        """
        results = []
        try:
            # Initialize face analyzer when needed
            self._init_face_analyzer()
            
            # Read the image
            img = cv2.imread(image_path)
            if img is None:
                logger.error(f"Failed to read image: {image_path}")
                return results
                
            # Detect faces
            faces = RetinaFace.detect_faces(img)
            if not faces:
                logger.info(f"No faces detected in: {image_path}")
                return results
                
            # Process each face
            for key in faces:
                identity = faces[key]
                facial_area = identity["facial_area"]
                x1, y1, x2, y2 = facial_area
                
                # Extract face ROI with padding
                try:
                    # Add padding (5% on each side)
                    height, width = img.shape[:2]
                    pad_x = int((x2 - x1) * 0.05)
                    pad_y = int((y2 - y1) * 0.05)
                    
                    # Ensure padded coordinates are within image bounds
                    x1_pad = max(0, x1 - pad_x)
                    y1_pad = max(0, y1 - pad_y)
                    x2_pad = min(width, x2 + pad_x)
                    y2_pad = min(height, y2 + pad_y)
                    
                    face_roi = img[y1_pad:y2_pad, x1_pad:x2_pad]
                except Exception as e:
                    logger.warning(f"Error extracting face ROI: {str(e)}")
                    continue
                    
                # Get face embedding
                face_data = self.face_analyzer.get(face_roi)
                if not face_data or len(face_data) == 0:
                    continue
                    
                encoding = face_data[0].embedding
                
                # Find best match
                best_match = {"name": "Unknown", "distance": float('inf'), "confidence": 0.0}
                
                for name, known_encodings in self.known_face_encodings.items():
                    for known_encoding in known_encodings:
                        if known_encoding.shape != encoding.shape:
                            continue
                            
                        distance = np.linalg.norm(known_encoding - encoding)
                        
                        if distance < best_match["distance"]:
                            confidence = max(0, min(100, 100 * (1 - distance / 2)))
                            best_match = {
                                "name": name,
                                "distance": distance,
                                "confidence": confidence
                            }
                
                # Only include matches with reasonable confidence
                if best_match["distance"] < self.similarity_threshold * 1.2:
                    results.append({
                        "name": best_match["name"],
                        "confidence": best_match["confidence"],
                        "facial_area": [int(x1), int(y1), int(x2), int(y2)]
                    })
                else:
                    results.append({
                        "name": "Unknown",
                        "confidence": 0.0,
                        "facial_area": [int(x1), int(y1), int(x2), int(y2)]
                    })
                    
            return results
            
        except Exception as e:
            logger.error(f"Error searching for person: {str(e)}")
            return results