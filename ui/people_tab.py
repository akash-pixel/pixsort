from PyQt5.QtWidgets import QWidget, QVBoxLayout, QListWidget, QListWidgetItem
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QPixmap, QIcon
import os

class PeopleTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.initUI()
    
    def initUI(self):
        layout = QVBoxLayout(self)
        self.people_list = QListWidget()
        self.people_list.itemDoubleClicked.connect(self.handle_person_double_click)
        layout.addWidget(self.people_list)
        self.setLayout(layout)
    
    def load_people(self):
        self.people_list.clear()
        self.people_list.setIconSize(QSize(512, 512))
        if hasattr(self.parent, 'db_manager'):
            people = self.parent.db_manager.get_people()
            for person in people:
                person_name = person[0]  # Since we're using .distinct() which returns tuples
                
                if person_name:  # Ignore empty names
                    item = QListWidgetItem(person_name)
                    item.setData(Qt.UserRole, person_name)
                    image = self.parent.db_manager.get_images_by_person(person_name, limit=1)
                    if image:
                        pixmap = QPixmap(image[0].file_path)
                        pixmap = pixmap.scaled(QSize(200, 200), Qt.KeepAspectRatio, Qt.SmoothTransformation)
                        item.setIcon(QIcon(pixmap))
                        item.setSizeHint(QSize(180, 180))
                    self.people_list.addItem(item)
                    
    
    def handle_person_double_click(self, item):
        person_name = item.data(Qt.UserRole)
        if person_name and person_name != "back":
            self.show_person_images(person_name)
        elif person_name == "back":
            self.load_people()
    
    def show_person_images(self, person_name):
        self.people_list.clear()
        
        # Add back button
        back_item = QListWidgetItem("← Back to People")
        font = back_item.font()
        font.setBold(True)
        back_item.setFont(font)
        back_item.setData(Qt.UserRole, "back")
        self.people_list.addItem(back_item)
        self.people_list.setIconSize(QSize(512, 512))
        
        # Add person title
        title_item = QListWidgetItem(f"Person: {person_name}")
        font = title_item.font()
        font.setBold(True)
        title_item.setFont(font)
        self.people_list.addItem(title_item)
        
        # Get images for this person
        images = self.parent.db_manager.get_images_by_person(person_name)
        
        # Add images
        for image in images:
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
                
            self.people_list.addItem(item)