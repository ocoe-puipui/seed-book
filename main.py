import sys
from PySide6.QtWidgets import QApplication
from app import AIImageViewerApp  # app.pyから本番の画面を読み込む

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # 本番用のメイン画面を起動
    window = AIImageViewerApp()
    window.show()
    
    sys.exit(app.exec())
