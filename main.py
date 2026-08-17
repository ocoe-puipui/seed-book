import sys
from PySide6.QtWidgets import QApplication
from app import AIImageViewerApp

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    window = AIImageViewerApp()
    window.show()
    
    sys.exit(app.exec())
