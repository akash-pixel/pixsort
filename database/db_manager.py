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