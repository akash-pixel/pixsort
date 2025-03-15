from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.models import Base, Album, Image, Face
from utils.config_manager import ConfigManager

class DatabaseManager:
    def __init__(self, db_url=None):
        # Get database URL from config if not provided
        if not db_url:
            config = ConfigManager()
            db_url = config.get_database_url()
        
        self.engine = create_engine(db_url)
        Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
        
        # Create default album if it doesn't exist
        self._create_default_album()
    
    def _create_default_album(self):
        default_album = self.session.query(Album).filter(Album.name == "Default").first()
        if not default_album:
            default_album = Album(name="Default")
            self.session.add(default_album)
            self.session.commit()
    
    def get_albums(self):
        return self.session.query(Album).all()
    
    def add_image(self, file_path, timestamp, location, has_text, album_id):
        # Check if image already exists
        existing = self.session.query(Image).filter(Image.file_path == file_path).first()
        if existing:
            return existing
        
        # Create new image
        new_image = Image(
            file_path=file_path,
            timestamp=timestamp,
            location=location,
            has_text=has_text,
            album_id=album_id
        )
        self.session.add(new_image)
        self.session.commit()
        return new_image
    
    def get_images_by_album(self, album_id, limit=50):
        return self.session.query(Image).filter(Image.album_id == album_id).limit(limit).all()
    
    def get_people(self):
        return self.session.query(Face.person_name).distinct().all()
    
    def get_images_by_person(self, person_name, limit=50):
        return self.session.query(Image).join(Face).filter(Face.person_name == person_name).limit(limit).all()
    
    def add_face(self, image_id, person_name, face_encoding):
        face = Face(
            image_id=image_id,
            person_name=person_name,
            face_encoding=face_encoding
        )
        self.session.add(face)
        self.session.commit()
        return face
    
    def get_default_album_id(self):
        default_album = self.session.query(Album).filter(Album.name == "Default").first()
        return default_album.id if default_album else None
    
    def close(self):
        self.session.close()
    
    def add_face(self, image_id, person_name, face_encoding, facial_area=None, landmarks=None, confidence=None):
        """
        Add a face to the database with enhanced metadata.
        
        Args:
            image_id: ID of the image where the face was detected
            person_name: Name of the person
            face_encoding: JSON string of face encoding
            facial_area: JSON string of facial area coordinates
            landmarks: JSON string of facial landmarks
            confidence: Detection confidence score
            
        Returns:
            The newly created Face object
        """
        face = Face(
            image_id=image_id,
            person_name=person_name,
            face_encoding=face_encoding,
            facial_area=facial_area,
            landmarks=landmarks,
            confidence=confidence
        )
        self.session.add(face)
        self.session.commit()
        return face

    def update_image_processed_status(self, image_id, processed=True, face_count=0):
        """
        Update the processed status and face count of an image.
        
        Args:
            image_id: ID of the image to update
            processed: Whether the image has been processed
            face_count: Number of faces detected in the image
            
        Returns:
            The updated Image object
        """
        image = self.session.query(Image).filter(Image.id == image_id).first()
        if image:
            image.processed = processed
            image.face_count = face_count
            self.session.commit()
        return image

    def get_unprocessed_images(self, limit=100):
        """
        Get images that haven't been processed yet.
        
        Args:
            limit: Maximum number of images to return
            
        Returns:
            List of Image objects
        """
        return self.session.query(Image).filter(Image.processed == False).limit(limit).all()

    def update_person_name(self, old_name, new_name):
        """
        Update a person's name across all faces.
        
        Args:
            old_name: Current name
            new_name: New name
            
        Returns:
            Number of faces updated
        """
        faces = self.session.query(Face).filter(Face.person_name == old_name).all()
        for face in faces:
            face.person_name = new_name
        self.session.commit()
        return len(faces)

    def merge_persons(self, source_name, target_name):
        """
        Merge two person identities.
        
        Args:
            source_name: Person to merge from
            target_name: Person to merge into
            
        Returns:
            Number of faces updated
        """
        return self.update_person_name(source_name, target_name)

    def get_face_count_by_person(self):
        """
        Get the number of faces for each person.
        
        Returns:
            Dictionary mapping person names to face counts
        """
        from sqlalchemy import func
        results = self.session.query(
            Face.person_name, 
            func.count(Face.id).label('face_count')
        ).group_by(Face.person_name).all()
        
        return {person: count for person, count in results}