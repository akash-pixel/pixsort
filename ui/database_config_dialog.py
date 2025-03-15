from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                            QLineEdit, QComboBox, QPushButton, QFormLayout,
                            QDialogButtonBox, QGroupBox, QFileDialog)
from PyQt5.QtCore import Qt
from utils.config_manager import ConfigManager

class DatabaseConfigDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Database Configuration")
        self.config = ConfigManager()
        self.initUI()
        self.loadCurrentConfig()
    
    def initUI(self):
        layout = QVBoxLayout(self)
        
        # Database type selection
        type_layout = QHBoxLayout()
        type_label = QLabel("Database Type:")
        self.db_type_combo = QComboBox()
        self.db_type_combo.addItems(["SQLite", "MySQL", "PostgreSQL"])
        self.db_type_combo.currentTextChanged.connect(self.onDatabaseTypeChanged)
        type_layout.addWidget(type_label)
        type_layout.addWidget(self.db_type_combo)
        layout.addLayout(type_layout)
        
        # SQLite configuration
        self.sqlite_group = QGroupBox("SQLite Configuration")
        sqlite_layout = QFormLayout()
        sqlite_layout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        
        self.sqlite_path = QLineEdit()
        browse_button = QPushButton("Browse...")
        browse_button.clicked.connect(self.browseSqliteFile)
        
        sqlite_path_layout = QHBoxLayout()
        sqlite_path_layout.addWidget(self.sqlite_path)
        sqlite_path_layout.addWidget(browse_button)
        
        sqlite_layout.addRow("Database File:", sqlite_path_layout)
        self.sqlite_group.setLayout(sqlite_layout)
        layout.addWidget(self.sqlite_group)
        
        # SQL Server configuration (MySQL/PostgreSQL)
        self.server_group = QGroupBox("Server Configuration")
        server_layout = QFormLayout()
        
        self.db_host = QLineEdit()
        self.db_port = QLineEdit()
        self.db_name = QLineEdit()
        self.db_user = QLineEdit()
        self.db_password = QLineEdit()
        self.db_password.setEchoMode(QLineEdit.Password)
        
        server_layout.addRow("Host:", self.db_host)
        server_layout.addRow("Port:", self.db_port)
        server_layout.addRow("Database Name:", self.db_name)
        server_layout.addRow("Username:", self.db_user)
        server_layout.addRow("Password:", self.db_password)
        
        self.server_group.setLayout(server_layout)
        layout.addWidget(self.server_group)
        
        # Buttons
        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttons.accepted.connect(self.saveConfig)
        self.buttons.rejected.connect(self.reject)
        layout.addWidget(self.buttons)
        
        # Test button
        test_button = QPushButton("Test Connection")
        test_button.clicked.connect(self.testConnection)
        layout.addWidget(test_button)
        
        # Set initial state
        self.onDatabaseTypeChanged(self.db_type_combo.currentText())
    
    def loadCurrentConfig(self):
        """Load current configuration values"""
        db_type = self.config.config.get('DATABASE', 'Type', fallback='sqlite').lower()
        
        # Set database type
        index = self.db_type_combo.findText(db_type.capitalize(), Qt.MatchFixedString)
        if index >= 0:
            self.db_type_combo.setCurrentIndex(index)
        
        # Load SQLite config
        self.sqlite_path.setText(self.config.config.get('DATABASE', 'Path', fallback='photo_manager.db'))
        
        # Load server config
        self.db_host.setText(self.config.config.get('DATABASE', 'Host', fallback='localhost'))
        self.db_port.setText(self.config.config.get('DATABASE', 'Port', fallback='3306'))
        self.db_name.setText(self.config.config.get('DATABASE', 'Name', fallback='photo_manager'))
        self.db_user.setText(self.config.config.get('DATABASE', 'User', fallback='user'))
        self.db_password.setText(self.config.config.get('DATABASE', 'Password', fallback='password'))
    
    def browseSqliteFile(self):
        """Browse for SQLite database file"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, 
            "Select Database File", 
            "", 
            "SQLite Database (*.db);;All Files (*.*)"
        )
        
        if file_path:
            self.sqlite_path.setText(file_path)
    
    def onDatabaseTypeChanged(self, db_type):
        """Show/hide appropriate configuration sections based on database type"""
        if db_type.lower() == "sqlite":
            self.sqlite_group.setVisible(True)
            self.server_group.setVisible(False)
        else:
            self.sqlite_group.setVisible(False)
            self.server_group.setVisible(True)
            
            # Set default port based on database type
            if db_type.lower() == "mysql":
                self.db_port.setText("3306")
            elif db_type.lower() == "postgresql":
                self.db_port.setText("5432")
    
    def saveConfig(self):
        """Save configuration and close dialog"""
        db_type = self.db_type_combo.currentText().lower()
        self.config.config['DATABASE']['Type'] = db_type
        
        if db_type == "sqlite":
            self.config.config['DATABASE']['Path'] = self.sqlite_path.text()
        else:
            self.config.config['DATABASE']['Host'] = self.db_host.text()
            self.config.config['DATABASE']['Port'] = self.db_port.text()
            self.config.config['DATABASE']['Name'] = self.db_name.text()
            self.config.config['DATABASE']['User'] = self.db_user.text()
            self.config.config['DATABASE']['Password'] = self.db_password.text()
        
        self.config.save_config()
        self.accept()
    
    def testConnection(self):
        """Test database connection"""
        from PyQt5.QtWidgets import QMessageBox
        from sqlalchemy import create_engine
        
        try:
            # Get current configuration
            db_type = self.db_type_combo.currentText().lower()
            
            if db_type == "sqlite":
                db_url = f"sqlite:///{self.sqlite_path.text()}"
            elif db_type == "mysql":
                db_url = f"mysql+pymysql://{self.db_user.text()}:{self.db_password.text()}@{self.db_host.text()}:{self.db_port.text()}/{self.db_name.text()}"
            elif db_type == "postgresql":
                db_url = f"postgresql://{self.db_user.text()}:{self.db_password.text()}@{self.db_host.text()}:{self.db_port.text()}/{self.db_name.text()}"
            
            # Test connection
            engine = create_engine(db_url)
            connection = engine.connect()
            connection.close()
            
            QMessageBox.information(self, "Connection Test", "Connection successful!")
        except Exception as e:
            QMessageBox.critical(self, "Connection Test", f"Connection failed:\n{str(e)}")