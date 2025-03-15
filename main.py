import sys
from PyQt5.QtWidgets import QApplication
from ui.main_window import PhotoManagerApp

def main():
    app = QApplication(sys.argv)
    window = PhotoManagerApp()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()