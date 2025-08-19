import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QDialog, QGroupBox,
    QVBoxLayout, QHBoxLayout, QFormLayout,  QLabel, QLineEdit, QTextEdit,  QListWidget, QListWidgetItem,
    QPushButton, QDialogButtonBox
)
from PyQt5.QtGui import QFont, QPixmap, QResizeEvent,  QIcon
from PyQt5.QtCore import QSize

from src.utils.logger import Logger

logger = Logger("UI")

class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        # 标题图标和窗口大小
        self.setFixedSize(500, 700)
        self.setWindowTitle("Vocabulary")
        self.setWindowIcon(QIcon("ico.ico"))
        # 窗口置中
        screen_geometry = QApplication.desktop().screenGeometry()
        x = (screen_geometry.width() - self.width()) // 2
        y = (screen_geometry.height() - self.height()) // 2
        self.move(x, y)

        self.space_label = QLabel()
# 功能---------------------------------------------------------------------------------------------
        self.widget_book_list = QListWidget()

        self.button_load = QPushButton("Load")
        self.button_export = QPushButton("Export")
        self.button_New = QPushButton("Create")
        self.button_New.clicked.connect(self.add_vocabulary_book)
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

        # 全局
        widget_global = QWidget()
        layout_global = QVBoxLayout(widget_global)
        layout_global.addWidget(group_book_list)
        layout_global.addWidget(group_function)
        self.setCentralWidget(widget_global)

    def add_vocabulary_book(self):
        dlg = NewBookDialog(self)
        if dlg.exec_() == QDialog.Accepted:
            name, desc = dlg.values()
            if not name or not name.strip():
                return
        else:
            return

        item = QListWidgetItem()
        item_size = QSize(0, 100)
        item.setSizeHint(item_size)

        vocabulary_book = VocabularyBookUI(name, desc, item_size, self.widget_book_list, item)
        self.widget_book_list.addItem(item)
        self.widget_book_list.setItemWidget(item, vocabulary_book)

    def resizeEvent(self, event: QResizeEvent):
        # if not self.image_label.pixmap():
        #     return
        #
        # pixmap = self.image_label.pixmap()
        # scaled_pixmap = pixmap.scaled(self.image_label.size(), Qt.AspectRatioMode.KeepAspectRatio)
        # self.image_label.setPixmap(scaled_pixmap)

        super().resizeEvent(event)

class VocabularyBookUI(QWidget):
    def __init__(self, name, desc, size, list_widget, item):
        super().__init__()
        self.list_widget = list_widget
        self.item = item

        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        label_image = QLabel("image")
        label_image.setFixedSize(60, 70)
        label_image.setScaledContents(True)
        label_image.setPixmap(QPixmap(":/image/book.png"))
        layout.addStretch(1)
        layout.addWidget(label_image)
        layout.addStretch(0)

        widget_info = QWidget()
        layout_info = QVBoxLayout(widget_info)
        self.label_name = QLabel(name)
        font_name = QFont()
        font_name.setFamily("Consolas")
        font_name.setPointSize(12)
        font_name.setBold(True)
        self.label_name.setFont(font_name)
        self.label_desc = QLabel(desc)
        self.label_desc.setStyleSheet("color: grey;")
        layout_info.addWidget(self.label_name)
        layout_info.addWidget(self.label_desc)
        layout.addWidget(widget_info, 1)

        self.button_delete = QPushButton("-")
        self.button_delete.clicked.connect(self.remove_self)
        layout.addStretch(10)
        layout.addWidget(self.button_delete)

    def remove_self(self):
        row = self.list_widget.row(self.item)
        self.list_widget.takeItem(row)

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

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())