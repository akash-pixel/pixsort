from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QLineEdit, QDialogButtonBox

class NameInputDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Enter Name")
        self.layout = QVBoxLayout(self)
        
        self.label = QLabel("Enter the person's name:")
        self.layout.addWidget(self.label)
        
        self.name_input = QLineEdit()
        self.layout.addWidget(self.name_input)
        
        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        self.layout.addWidget(self.buttons)
    
    def get_name(self):
        return self.name_input.text()