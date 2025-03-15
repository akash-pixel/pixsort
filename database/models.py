from datetime import datetime
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class Image(Base):
    __tablename__ = 'images'
    id = Column(Integer, primary_key=True)
    file_path = Column(String, unique=True)
    timestamp = Column(DateTime, default=datetime.now)
    location = Column(String)
    has_text = Column(Integer, default=0)
    album_id = Column(Integer, ForeignKey('albums.id'))
    faces = relationship("Face", back_populates="image", cascade="all, delete-orphan")
    
class Face(Base):
    __tablename__ = 'faces'
    id = Column(Integer, primary_key=True)
    image_id = Column(Integer, ForeignKey('images.id'))
    person_name = Column(String)
    face_encoding = Column(String)
    image = relationship("Image", back_populates="faces")
    
class Album(Base):
    __tablename__ = 'albums'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    images = relationship("Image", cascade="all, delete-orphan")