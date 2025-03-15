import os
import face_recognition
import numpy as np
import cv2
from PyQt5.QtWidgets import QApplication
from ui.dialogs import NameInputDialog
import json
from database.models import Face, Image

class FaceRecognitionProcessor:
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.known_face_encodings = {}
        self.load_known_faces()
    
    def load_known_faces(self):
        """Load known face encodings from database"""
        # This is a simple approach - in a real app, you'd want a more sophisticated way to
        # manage face encodings, possibly using a separate table or specialized storage
        faces = self.db_manager.session.query(Face).all()
        for face in faces:
            if face.person_name and face.face_encoding:
                try:
                    encoding = np.frombuffer(json.loads(face.face_encoding), dtype=np.float64)
                    if face.person_name not in self.known_face_encodings:
                        self.known_face_encodings[face.person_name] = []
                    self.known_face_encodings[face.person_name].append(encoding)
                except:
                    pass
    
    def process_images(self):
        """Process images in the database to detect faces"""
        processed = 0
        detected = 0
        
        # Get all images in the database
        images = self.db_manager.session.query(Image).all()
        
        for image in images:
            if not os.path.exists(image.file_path):
                continue
                
            # Only process images (not videos)
            ext = os.path.splitext(image.file_path)[1].lower()
            if ext not in ['.jpg', '.jpeg', '.png']:
                continue
                
            try:
                # Load image
                img = face_recognition.load_image_file(image.file_path)
                
                # Find faces
                face_locations = face_recognition.face_locations(img)
                
                if face_locations:
                    # Get face encodings
                    face_encodings = face_recognition.face_encodings(img, face_locations)
                    
                    for encoding in face_encodings:
                        # Try to match with known faces
                        matched = False
                        for name, known_encodings in self.known_face_encodings.items():
                            matches = face_recognition.compare_faces(known_encodings, encoding, tolerance=0.6)
                            if any(matches):
                                # Found a match
                                person_name = name
                                matched = True
                                break
                        
                        if not matched:
                            # No match found, ask for name
                            # In a real app, you'd want to batch this or use a more elegant solution
                            # dialog = NameInputDialog()
                            # if dialog.exec_():
                            #     person_name = dialog.get_name()
                            #     if not person_name:
                            #         continue
                                
                            #     # Add to known faces
                            #     if person_name not in self.known_face_encodings:
                            #         self.known_face_encodings[person_name] = []
                            #     self.known_face_encodings[person_name].append(encoding)
                            # else:
                            #     continue
                            person_name = "Name"
                        
                        # Save face to database
                        encoding_json = json.dumps(encoding.tolist())
                        self.db_manager.add_face(image.id, person_name, encoding_json)
                        detected += 1
                
                processed += 1
                
                # Keep UI responsive
                if processed % 10 == 0:
                    QApplication.processEvents()
                    
            except Exception as e:
                print(f"Error processing image {image.file_path}: {str(e)}")
        
        return processed, detected