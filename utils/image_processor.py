import os
import datetime
import exifread
from PyQt5.QtWidgets import QApplication

class ImageProcessor:
    def __init__(self, db_manager):
        self.db_manager = db_manager
    
    def process_folders(self, folders):
        """Process all files in given folders and add to database"""
        # Define supported formats
        img_extensions = ('.png', '.jpg', '.jpeg', '.gif', '.bmp')
        video_extensions = ('.mp4', '.mov', '.avi')
        total_files = 0
        added_files = 0
        
        # Get default album ID
        default_album_id = self.db_manager.get_default_album_id()
        if not default_album_id:
            return 0, 0
        
        for folder in folders:
            try:
                if os.path.exists(folder) and os.path.isdir(folder):
                    files = []
                    for file in os.listdir(folder):
                        file_path = os.path.join(folder, file)
                        if os.path.isfile(file_path):
                            ext = os.path.splitext(file)[1].lower()
                            if ext in img_extensions or ext in video_extensions:
                                files.append(file_path)
                    
                    total_files += len(files)
                    
                    for file_path in files:
                        # Get timestamp
                        timestamp = datetime.datetime.fromtimestamp(os.path.getmtime(file_path))
                        location = ""
                        has_text = 0
                        
                        # Try to extract EXIF data for images
                        ext = os.path.splitext(file_path)[1].lower()
                        if ext in img_extensions:
                            try:
                                with open(file_path, 'rb') as f:
                                    tags = exifread.process_file(f)
                                    if 'GPS GPSLatitude' in tags and 'GPS GPSLongitude' in tags:
                                        lat = tags['GPS GPSLatitude'].values
                                        lon = tags['GPS GPSLongitude'].values
                                        location = f"{lat[0]:.6f},{lon[0]:.6f}"
                                    if 'EXIF DateTimeOriginal' in tags:
                                        date_str = str(tags['EXIF DateTimeOriginal'])
                                        try:
                                            timestamp = datetime.datetime.strptime(date_str, '%Y:%m:%d %H:%M:%S')
                                        except:
                                            pass
                            except:
                                pass
                        
                        # Add to database
                        image = self.db_manager.add_image(
                            file_path=file_path,
                            timestamp=timestamp,
                            location=location,
                            has_text=has_text,
                            album_id=default_album_id
                        )
                        
                        if image.id:  # If image was added (not already in DB)
                            added_files += 1
                        
                        # Keep UI responsive
                        if added_files % 20 == 0:
                            QApplication.processEvents()
                            
            except Exception as e:
                print(f"Error processing folder {folder}: {str(e)}")
                
        return total_files, added_files