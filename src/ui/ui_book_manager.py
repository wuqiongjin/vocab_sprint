from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QDialog, QGroupBox,
    QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, QLineEdit, QTextEdit, QListWidget, QListWidgetItem,
    QPushButton, QDialogButtonBox, QFileDialog, QComboBox
)
from PyQt5.QtGui import QFont, QPixmap, QResizeEvent,  QIcon
from PyQt5.QtCore import QSize, Qt

from src.core.vocabulary_book import VocabularyBook
from src.ui.ui_utils import MessageBox
from src.ui.ui_word_manager import WordManagerUI
from src.utils.exceptions import BaseError
from src.utils.logger import Logger
from src.core.vocabulary_book_manager import VocabularyBookManager, VocabularyBookInfo, BookType, ExportType

import resource.ui.resources

logger = Logger("ui_ability")

class BookManagerUI(QMainWindow):

    def __init__(self, book_manager: VocabularyBookManager):
        super().__init__()
        self.book_manager = book_manager
        # 标题图标和窗口大小
        self.setFixedSize(500, 700)
        self.setWindowTitle("Vocabulary")
        self.setWindowIcon(QIcon("ico.ico"))
        self.word_manager_ui = None
        # 窗口置中
        screen_geometry = QApplication.desktop().screenGeometry()
        x = (screen_geometry.width() - self.width()) // 2
        y = (screen_geometry.height() - self.height()) // 2
        self.move(x, y)

        self.space_label = QLabel()
# 功能---------------------------------------------------------------------------------------------
        self.widget_book_list = QListWidget()

        self.button_load = QPushButton("Load")
        self.button_load.clicked.connect(self.load_vocabulary_book)
        self.button_export = QPushButton("Export")
        self.button_export.clicked.connect(self.export_vocabulary_book)
        self.button_New = QPushButton("Create")
        self.button_New.clicked.connect(self.create_vocabulary_book)
# 布局---------------------------------------------------------------------------------------------
        # 功能
        group_function = QGroupBox()
        layout_function = QHBoxLayout(group_function)
        layout_function.addWidget(self.button_load)
        layout_function.addWidget(self.button_export)
        layout_function.addWidget(self.button_New)
        # 测试
        group_book_list = QGroupBox("Book List")
        layout_book_list = QHBoxLayout(group_book_list)
        layout_book_list.addWidget(self.widget_book_list)
        self.init_book_list()

        # 全局
        widget_global = QWidget()
        layout_global = QVBoxLayout(widget_global)
        layout_global.addWidget(group_book_list)
        layout_global.addWidget(group_function)
        self.setCentralWidget(widget_global)

    def init_book_list(self):
        for book in self.book_manager.get_all_book().values():
            self.add_book_to_ui(book)

    def add_book_to_ui(self, book):
        item = QListWidgetItem()
        item_size = QSize(0, 100)
        item.setSizeHint(item_size)

        vocabulary_book_ui = VocabularyBookUI(book, self, self.widget_book_list, item)
        self.widget_book_list.addItem(item)
        self.widget_book_list.setItemWidget(item, vocabulary_book_ui)

    def create_vocabulary_book(self):
        dlg = NewBookDialog(self)
        if dlg.exec_() == QDialog.Accepted:
            name, desc = dlg.values()
            if not name or not name.strip():
                return
        else:
            return
        logger.INFO(f"Get create info: name: {name} description: {desc}")

        book_info = VocabularyBookInfo(name, type=BookType.USER, description=desc)
        logger.INFO(f"Create vocabulary book.")
        if self.book_manager.create_vocabulary_book(book_info):
            logger.INFO(f"Create book success, name: {name} description: {desc}.")
            book = self.book_manager.get_book(name)
            self.add_book_to_ui(book)
        else:
            MessageBox(f"\nCreate a new vocabulary book failed! \n\nThere is already a book called:\n\n{name}\n", "Error:")

    def load_vocabulary_book(self):
        dlg = LoadBookDialog(self)
        if dlg.exec_() == QDialog.Accepted:
            name, desc, path = dlg.values()
            if not name or not name.strip():
                return
            if not path or not path.strip():
                return
        else:
            return
        logger.INFO(f"Get load info: name: {name} description: {desc} load path: {path}")

        book_info = VocabularyBookInfo(name, type=BookType.USER, description=desc)
        logger.INFO(f"Load vocabulary book.")

        if self.book_manager.create_vocabulary_book_from_data(book_info, path):
            logger.INFO(f"Load book success, name: {name} description: {desc}.")
            book = self.book_manager.get_book(name)
            self.add_book_to_ui(book)
        else:
            MessageBox(f"\nCreate a new vocabulary book failed! \n\nThere is already a book called:\n\n{name}\n", "Error:")

    def export_vocabulary_book(self):
        dlg = ExportBookDialog(self)
        if dlg.exec_() == QDialog.Accepted:
            name, export_type, path = dlg.values()
            if not name or not name.strip():
                return
            if not path or not path.strip():
                return
        else:
            return
        logger.INFO(f"Get export info: name: {name} export type: {export_type.lower()} output path: {path}")
        try:
            if self.book_manager.export_vocabulary_book(name, path, ExportType[export_type.upper()]):
                logger.INFO(f"Export book success, name: {name} .")
            else:
                MessageBox(f"\nExport vocabulary book failed!", "Error:")
        except Exception as e:
            MessageBox(f"\nExport vocabulary book failed! \n\n{e}", "Error:")

    def resizeEvent(self, event: QResizeEvent):
        # if not self.image_label.pixmap():
        #     return
        #
        # pixmap = self.image_label.pixmap()
        # scaled_pixmap = pixmap.scaled(self.image_label.size(), Qt.AspectRatioMode.KeepAspectRatio)
        # self.image_label.setPixmap(scaled_pixmap)

        super().resizeEvent(event)

class VocabularyBookUI(QWidget):
    def __init__(self, book: VocabularyBook, book_manager_ui, list_widget, item):
        super().__init__()
        self.book = book
        book_info = self.book.get_book_info()
        self.name = book_info.name
        self.desc = book_info.description
        self.book_manager_ui = book_manager_ui
        self.book_manager = book_manager_ui.book_manager
        self.list_widget = list_widget
        self.item = item

        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        label_image = QLabel("image")
        label_image.setFixedSize(60, 70)
        label_image.setScaledContents(True)
        label_image.setPixmap(QPixmap(":/image/book.png"))
        layout.addStretch(0)
        layout.addWidget(label_image)
        layout.addStretch(0)

        widget_info = QWidget()
        widget_info.setFixedWidth(300)
        layout_info = QVBoxLayout(widget_info)
        self.label_name = QLabel(self.name)
        font_name = QFont()
        font_name.setFamily("Consolas")
        font_name.setPointSize(12)
        font_name.setBold(True)
        self.label_name.setFont(font_name)
        self.label_desc = QLabel(self.desc)
        self.label_desc.setStyleSheet("color: grey;")
        layout_info.addWidget(self.label_name)
        layout_info.addWidget(self.label_desc)
        layout.addWidget(widget_info, 1)

        widget_button_field = QWidget()
        widget_button_field.setFixedWidth(200)
        layout_button = QHBoxLayout(widget_button_field)

        self.button_select = QPushButton("select")
        self.button_select.clicked.connect(self.selected)
        layout_button.addWidget(self.button_select)

        self.button_delete = QPushButton("delete")
        self.button_delete.clicked.connect(self.remove_self)
        layout_button.addWidget(self.button_delete)

        layout.addStretch(10)
        layout.addWidget(widget_button_field)

    def selected(self):
        self.book_manager_ui.hide()
        self.book_manager_ui.word_manager_ui = WordManagerUI(self.book_manager_ui, self.book)
        self.book_manager_ui.word_manager_ui.show()

    def remove_self(self):
        if self.book_manager.delete_vocabulary_book(self.name):
            row = self.list_widget.row(self.item)
            self.list_widget.takeItem(row)
        else:
            MessageBox("Delete vocabulary book failed.")

class NewBookDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("New VocabularyBook")
        self.name_edit = QLineEdit()
        self.desc_edit = QTextEdit()
        self.desc_edit.setMinimumHeight(60)

        form = QFormLayout(self)
        form.addRow("Book name:", self.name_edit)
        form.addRow("Book description:", self.desc_edit)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)

    def values(self):
        return self.name_edit.text().strip(), self.desc_edit.toPlainText().strip()

class LoadBookDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Load VocabularyBook")
        self.name_edit = QLineEdit()
        self.desc_edit = QTextEdit()
        self.desc_edit.setMinimumHeight(60)

        self.path_edit = QLineEdit()
        button_select_path = QPushButton("select")
        button_select_path.clicked.connect(self.open_path)
        widget_path = QWidget()
        layout_path = QHBoxLayout(widget_path)
        layout_path.setContentsMargins(0, 0, 0, 0)
        layout_path.addWidget(self.path_edit)
        layout_path.addWidget(button_select_path)

        form = QFormLayout(self)
        form.addRow("Book name:", self.name_edit)
        form.addRow("Book description:", self.desc_edit)
        form.addRow("File path:", widget_path)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)

    def values(self):
        return self.name_edit.text().strip(), self.desc_edit.toPlainText().strip(), self.path_edit.text().strip()

    def open_path(self):
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(self, "Select file", "", "Text Files (*.csv);")
        if file_path:
            self.path_edit.setText(file_path)

class ExportBookDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Export VocabularyBook")
        self.combobox_book = QComboBox(self)
        list_books = parent.book_manager.get_all_book()
        self.combobox_book.addItems(list_books)
        self.combobox_book.setCurrentIndex(0)

        self.combobox_export_type = QComboBox(self)
        self.combobox_export_type.addItems(ExportType.get_all_name())
        self.combobox_export_type.setCurrentIndex(0)

        self.path_edit = QLineEdit()
        button_select_path = QPushButton("select")
        button_select_path.clicked.connect(self.open_path)
        widget_path = QWidget()
        layout_path = QHBoxLayout(widget_path)
        layout_path.setContentsMargins(0, 0, 0, 0)
        layout_path.addWidget(self.path_edit)
        layout_path.addWidget(button_select_path)

        form = QFormLayout(self)
        form.addRow("Select book:", self.combobox_book)
        form.addRow("Export type:", self.combobox_export_type)
        form.addRow("Output path:", widget_path)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)

    def values(self):
        return self.combobox_book.currentText().strip(), self.combobox_export_type.currentText().strip(), self.path_edit.text().strip()

    def open_path(self):
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getSaveFileName(self, "select save file", "", "Text Files (*.csv);")
        if file_path:
            self.path_edit.setText(file_path)