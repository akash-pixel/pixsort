from PyQt5.QtWidgets import QWidget, QVBoxLayout, QListWidget, QListWidgetItem, QPushButton
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QPixmap, QIcon
import os

class AlbumTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.initUI()
    
    def initUI(self):
        layout = QVBoxLayout(self)
        self.albums_list = QListWidget()
        self.albums_list.itemDoubleClicked.connect(self.handle_album_double_click)
        layout.addWidget(self.albums_list)
        self.setLayout(layout)
    
    def load_albums(self):
        self.albums_list.clear()
        self.albums_list.setIconSize(QSize(512, 512))
        if hasattr(self.parent, 'db_manager'):
            albums = self.parent.db_manager.get_albums()
            for album in albums:
                item = QListWidgetItem(f"{album.name} ({len(album.images)} images)")
                item.setData(Qt.UserRole, album.id)
                image = self.parent.db_manager.get_images_by_album(album.id, limit=1)
                if image:
                    try:
                        pixmap = QPixmap(image[0].file_path)
                        if not pixmap.isNull():
                            pixmap = pixmap.scaled(QSize(200, 200), Qt.KeepAspectRatio, Qt.SmoothTransformation)
                            item.setIcon(QIcon(pixmap))
                            item.setSizeHint(QSize(180, 180))
                    except:
                        item.setIcon(QIcon.fromTheme("image-x-generic"))

                self.albums_list.addItem(item)
    
    def handle_album_double_click(self, item):
        album_id = item.data(Qt.UserRole)
        if album_id is not None:
            self.show_album_contents(album_id)
    
    def show_album_contents(self, album_id):
        self.albums_list.clear()
        
        # Get album info
        albums = self.parent.db_manager.get_albums()
        album = next((a for a in albums if a.id == album_id), None)
        
        if not album:
            return
        
        # Add back button
        back_item = QListWidgetItem("← Back to Albums")
        font = back_item.font()
        font.setBold(True)
        back_item.setFont(font)
        back_item.setData(Qt.UserRole, "back")
        self.albums_list.addItem(back_item)
        self.albums_list.setIconSize(QSize(512, 512))
        
        # Add album title
        title_item = QListWidgetItem(f"Album: {album.name}")
        font = title_item.font()
        font.setBold(True)
        title_item.setFont(font)
        self.albums_list.addItem(title_item)
        
        # Add images
        for image in album.images:
            item = QListWidgetItem()
            # item.setText(os.path.basename(image.file_path))
            item.setData(Qt.UserRole, image.file_path)
            
            # Try to create thumbnail
            try:
                pixmap = QPixmap(image.file_path)
                if not pixmap.isNull():
                    pixmap = pixmap.scaled(QSize(200, 200), Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    item.setIcon(QIcon(pixmap))
                    item.setSizeHint(QSize(180, 180))
            except:
                item.setIcon(QIcon.fromTheme("image-x-generic"))
                
            self.albums_list.addItem(item)
            