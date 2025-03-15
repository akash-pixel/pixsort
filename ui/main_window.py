import os
from PyQt5.QtWidgets import (QMainWindow, QFileDialog, QVBoxLayout, QWidget, 
                            QMenuBar, QMenu, QAction, QStatusBar, QHBoxLayout, 
                            QLabel, QTabWidget, QLineEdit, QPushButton)
from PyQt5.QtCore import Qt
from database.db_manager import DatabaseManager
from ui.files_tab import FilesTab
from ui.album_tab import AlbumTab
from ui.people_tab import PeopleTab
from utils.image_processor import ImageProcessor
from utils.face_recognition import FaceRecognitionProcessor
from utils.config_manager import ConfigManager

class PhotoManagerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.selected_folders = []
        self.config_manager = ConfigManager()
        self.db_manager = None
        self.initDatabase()
        # self.db_manager = DatabaseManager()
        self.image_processor = ImageProcessor(self.db_manager)
        self.face_processor = FaceRecognitionProcessor(self.db_manager)
        self.initUI()

    def initDatabase(self):
        try:
            # Get database URL from configuration
            db_url = self.config_manager.get_database_url()
            self.db_manager = DatabaseManager(db_url)
        except Exception: 
            self.statusBar.showMessage(f"Exeption {Exception}")

    def applicationSupportsSecureRestorableState(self):
        return Qt.ApplicationSupportsSecureRestorableState
    
    def initUI(self):
        self.setWindowTitle("PixSort - Photo & Video Manager")
        self.setGeometry(100, 100, 1000, 700)
        
        # Create menu bar
        self.create_menu_bar()
        
        # Create status bar
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("Ready")
        
        # Create main layout
        main_widget = QWidget()
        self.layout = QVBoxLayout(main_widget)
        
        # Create search box
        search_layout = QHBoxLayout()
        search_label = QLabel("Search:")
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search by person name...")
        self.search_button = QPushButton("Search")
        self.search_button.clicked.connect(self.search_images)
        
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_box)
        search_layout.addWidget(self.search_button)
        self.layout.addLayout(search_layout)
        
        # Create folder selection section
        folder_layout = QHBoxLayout()
        self.folder_btn = QPushButton("Select Folder")
        self.folder_btn.clicked.connect(self.select_folders)
        folder_layout.addWidget(self.folder_btn)
        
        self.process_btn = QPushButton("Process Files")
        self.process_btn.clicked.connect(self.process_files)
        self.process_btn.setEnabled(False)
        folder_layout.addWidget(self.process_btn)
        
        # Add face processing button
        self.face_process_btn = QPushButton("Detect Faces")
        self.face_process_btn.clicked.connect(self.process_faces)
        self.face_process_btn.setEnabled(False)
        folder_layout.addWidget(self.face_process_btn)
        
        self.layout.addLayout(folder_layout)
        
        # Create tab widget
        self.tabs = QTabWidget()
        
        # Create tabs
        self.files_tab = FilesTab(self)
        self.albums_tab = AlbumTab(self)
        self.people_tab = PeopleTab(self)
        
        # Add tabs
        self.tabs.addTab(self.files_tab, "Files")
        self.tabs.addTab(self.albums_tab, "Albums")
        self.tabs.addTab(self.people_tab, "People")
        
        self.layout.addWidget(self.tabs)
        
        self.setCentralWidget(main_widget)
        
        # Load data
        self.albums_tab.load_albums()
        self.people_tab.load_people()
    
    def create_menu_bar(self):
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("File")
        
        # Select folder action
        select_folder_action = QAction("Select Folder", self)
        select_folder_action.setShortcut("Ctrl+O")
        select_folder_action.triggered.connect(self.select_folders)
        file_menu.addAction(select_folder_action)
        
        # Process action
        process_action = QAction("Process Files", self)
        process_action.setShortcut("Ctrl+P")
        process_action.triggered.connect(self.process_files)
        file_menu.addAction(process_action)
        
        # Face processing action
        face_action = QAction("Detect Faces", self)
        face_action.setShortcut("Ctrl+F")
        face_action.triggered.connect(self.process_faces)
        file_menu.addAction(face_action)
        
        file_menu.addSeparator()
        
        # Exit action
        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Edit menu
        edit_menu = menubar.addMenu("Edit")
        
        # Clear selection action
        clear_action = QAction("Clear Selection", self)
        clear_action.triggered.connect(self.clear_selection)
        edit_menu.addAction(clear_action)
        
        # Help menu
        help_menu = menubar.addMenu("Help")
        
        # About action
        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def select_folders(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder:
            self.selected_folders.append(folder)
            self.files_tab.update_folder_list(self.selected_folders)
            self.process_btn.setEnabled(True)
            self.face_process_btn.setEnabled(True)
            self.statusBar.showMessage(f"{len(self.selected_folders)} folder(s) selected")
    
    def process_files(self):
        if not self.selected_folders:
            self.statusBar.showMessage("No folders selected")
            return
        
        self.statusBar.showMessage("Processing files...")
        processed, added = self.image_processor.process_folders(self.selected_folders)
        
        # Update UI
        self.albums_tab.load_albums()
        
        self.statusBar.showMessage(f"Processed {processed} files. Added {added} new files to database.")
    
    def process_faces(self):
        if not self.selected_folders:
            self.statusBar.showMessage("No folders selected")
            return
        
        self.statusBar.showMessage("Processing faces...")
        processed, detected = self.face_processor.process_images()
        
        # Update UI
        self.people_tab.load_people()
        
        self.statusBar.showMessage(f"Processed {processed} images. Detected {detected} faces.")
    
    def search_images(self):
        query = self.search_box.text().strip()
        if not query:
            self.statusBar.showMessage("Please enter a search term")
            return
        
        self.statusBar.showMessage(f"Searching for '{query}'...")
        
        # Search in database
        results = self.db_manager.get_images_by_person(query)
        
        # Show results
        self.files_tab.show_search_results(results, query)
        
        self.statusBar.showMessage(f"Found {len(results)} images matching '{query}'")
    
    def clear_selection(self):
        self.selected_folders = []
        self.files_tab.clear_list()
        self.process_btn.setEnabled(False)
        self.face_process_btn.setEnabled(False)
        self.statusBar.showMessage("Selection cleared")
    
    def show_about(self):
        self.statusBar.showMessage("PixSort - Photo & Video Manager v1.0")
    
    def closeEvent(self, event):
        self.db_manager.close()
        event.accept()