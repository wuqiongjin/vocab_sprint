import sys

from PyQt5.QtWidgets import QApplication

from src.core.vocabulary_book_manager import VocabularyBookManager
from src.ui.ui_book_manager import BookManagerUI

if __name__ == '__main__':
    app = QApplication(sys.argv)
    vocabulary_book_manager = VocabularyBookManager("default")
    book_manager_ui = BookManagerUI(vocabulary_book_manager)
    book_manager_ui.show()
    sys.exit(app.exec_())