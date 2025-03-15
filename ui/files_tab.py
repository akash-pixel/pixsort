import os
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QListWidget, QListWidgetItem
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QPixmap, QIcon

class FilesTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.initUI()
    
    def initUI(self):
        layout = QVBoxLayout(self)
        self.image_list = QListWidget()
        self.image_list.itemDoubleClicked.connect(self.handle_item_double_click)
        layout.addWidget(self.image_list)
        self.setLayout(layout)
    
    def clear_list(self):
        self.image_list.clear()
    
    def update_folder_list(self, folders):
        self.image_list.clear()
        for folder in folders:
            folder_item = QListWidgetItem(f"Selected Folder: {folder}")
            font = folder_item.font()
            font.setBold(True)
            folder_item.setFont(font)
            self.image_list.addItem(folder_item)
            try:
                self.load_media_from_folder(folder)
            except Exception as e:
                self.image_list.addItem(f"    Error accessing folder: {str(e)}")
    
    def load_media_from_folder(self, folder_path):
        if not os.path.exists(folder_path) or not os.path.isdir(folder_path):
            return
            
        # Define supported formats
        img_extensions = ('.png', '.jpg', '.jpeg', '.gif', '.bmp')
        video_extensions = ('.mp4', '.mov', '.avi')
        
        # Get all media files
        files = []
        for file in os.listdir(folder_path):
            file_path = os.path.join(folder_path, file)
            if os.path.isfile(file_path):
                ext = os.path.splitext(file)[1].lower()
                if ext in img_extensions or ext in video_extensions:
                    files.append(file_path)
        
        # Update status
        if hasattr(self.parent, 'statusBar'):
            self.parent.statusBar.showMessage(f"Loading {len(files)} media files...")
        
        # Display files in list widget with thumbnails
        for file_path in files:
            ext = os.path.splitext(file_path)[1].lower()
            
            item = QListWidgetItem()
            item.setText(os.path.basename(file_path))
            item.setData(Qt.UserRole, file_path)  # Store full path
            
            # Create thumbnail for images
            if ext in img_extensions:
                try:
                    pixmap = QPixmap(file_path)
                    if not pixmap.isNull():
                        pixmap = pixmap.scaled(QSize(64, 64), Qt.KeepAspectRatio, Qt.SmoothTransformation)
                        item.setIcon(QIcon(pixmap))
                        item.setSizeHint(QSize(80, 70))
                except:
                    # Use default icon if thumbnail creation fails
                    item.setIcon(QIcon.fromTheme("image-x-generic"))
            
            # Use icon for videos
            elif ext in video_extensions:
                item.setIcon(QIcon.fromTheme("video-x-generic"))
                item.setSizeHint(QSize(80, 70))
                
            self.image_list.addItem(item)
        
        if hasattr(self.parent, 'statusBar'):
            self.parent.statusBar.showMessage(f"Loaded {len(files)} media files from {os.path.basename(folder_path)}")
    
    def handle_item_double_click(self, item):
        file_path = item.data(Qt.UserRole)
        if file_path and os.path.isfile(file_path):
            # Open file with default application
            import subprocess
            import platform
            
            if platform.system() == 'Windows':
                os.startfile(file_path)
            elif platform.system() == 'Darwin':  # macOS
                subprocess.run(['open', file_path])
            else:  # Linux
                subprocess.run(['xdg-open', file_path])
    
    def show_search_results(self, results, query):
        self.image_list.clear()
        
        result_item = QListWidgetItem(f"Search Results for: '{query}'")
        font = result_item.font()
        font.setBold(True)
        result_item.setFont(font)
        self.image_list.addItem(result_item)
        
        for image in results:
            item = QListWidgetItem()
            item.setText(os.path.basename(image.file_path))
            item.setData(Qt.UserRole, image.file_path)
            
            # Create thumbnail
            try:
                pixmap = QPixmap(image.file_path)
                if not pixmap.isNull():
                    pixmap = pixmap.scaled(QSize(64, 64), Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    item.setIcon(QIcon(pixmap))
                    item.setSizeHint(QSize(80, 70))
            except:
                item.setIcon(QIcon.fromTheme("image-x-generic"))
                
            self.image_list.addItem(item)