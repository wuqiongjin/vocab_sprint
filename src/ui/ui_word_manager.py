import sys

from PyQt5.QtCore import QSize, pyqtSignal, Qt
from PyQt5.QtGui import QIcon, QResizeEvent, QFont
from PyQt5.QtWidgets import QMainWindow, QApplication, QLabel, QListWidget, QPushButton, QGroupBox, QHBoxLayout, \
    QWidget, QVBoxLayout, QListWidgetItem, QDialog, QLineEdit, QComboBox, QDialogButtonBox, QFormLayout

from src.core.vocabulary_book import VocabularyBookInfo, VocabularyBook
from src.core.vocabulary_book_manager import VocabularyBookManager, logger, InterpretationsMap
from src.core.word_query_service import WordQueryService
from src.ui.ui_utils import MessageBox, FocusLineEdit
from src.core.word_entry import WordEntry, PartOfSpeech


class WordManagerUI(QMainWindow):
    data_ready = pyqtSignal(list)

    def __init__(self, book_manager: VocabularyBookManager, book_name):
        super().__init__()
        self.book_manager = book_manager
        self.book: VocabularyBook = book_manager.get_book(book_name)
        self.query_service = None
        if self.book is None:
            return
        # 标题图标和窗口大小
        self.setFixedSize(600, 850)
        self.setWindowTitle(book_name)
        self.setWindowIcon(QIcon("ico.ico"))
        # 窗口置中
        screen_geometry = QApplication.desktop().screenGeometry()
        x = (screen_geometry.width() - self.width()) // 2
        y = (screen_geometry.height() - self.height()) // 2
        self.move(x, y)

        self.space_label = QLabel()
# 功能---------------------------------------------------------------------------------------------
        self.line_edit_search = FocusLineEdit()
        self.line_edit_search.setMinimumHeight(35)
        self.line_edit_search.focus_in.connect(self.on_search)
        self.line_edit_search.focus_out.connect(self.off_search)
        self.line_edit_search.textChanged.connect(self.search)
        self.data_ready.connect(self.update_word_list)

        self.widget_word_list = QListWidget()

        self.button_add_word = QPushButton("Add")
        self.button_add_word.clicked.connect(self.add_word)
        self.button_delete_word = QPushButton("Delete")
        self.button_delete_word.clicked.connect(self.delete_word)
# 布局---------------------------------------------------------------------------------------------
        # Function
        group_function = QGroupBox()
        layout_function = QHBoxLayout(group_function)
        layout_function.addWidget(self.button_add_word)
        layout_function.addWidget(self.button_delete_word)
        # WordList
        group_book_list = QGroupBox("Word List")
        layout_book_list = QHBoxLayout(group_book_list)
        layout_book_list.addWidget(self.widget_word_list)
        self.init_word_list()
        # Search
        group_search = QGroupBox("Search")
        layout_search = QHBoxLayout(group_search)
        layout_search.addWidget(self.line_edit_search)

        # Global
        widget_global = QWidget()
        layout_global = QVBoxLayout(widget_global)
        layout_global.addWidget(group_search)
        layout_global.addWidget(group_book_list)
        layout_global.addWidget(group_function)
        self.setCentralWidget(widget_global)

    def init_word_list(self):
        word_list = self.book.get_all_words().values()
        self.update_word_list(word_list)

    def add_word_to_ui(self, word: str, definition: str):
        item = QListWidgetItem()
        item_size = QSize(0, 100)
        item.setSizeHint(item_size)

        word_ui = WordUI(word, definition, item_size, self.widget_word_list, item, self.book)
        self.widget_word_list.addItem(item)
        self.widget_word_list.setItemWidget(item, word_ui)

    def add_word(self):
        try:
            dlg = AddWordDialog(self)
            if dlg.exec_() == QDialog.Accepted:
                word_entry = dlg.values()
                if not word_entry:
                    return
            else:
                return
            logger.INFO(f"Get word entry: {word_entry}")
            self.book.add_word(word_entry)
            self.add_word_to_ui(word_entry.word, self.get_first_interpretation(word_entry.interpretations))
        except Exception as e:
            logger.INFO(f"Add word failed, error: {e}")

    def delete_word(self):
        pass

    def on_search(self):
        self.query_service = WordQueryService(self.book.word_entry_manager)
        self.query_service.start_realtime_search(self.get_search_data)

    def off_search(self):
        if self.query_service:
            self.query_service.shutdown()

    def search(self):
        if not self.line_edit_search.text():
            self.init_word_list()
        if self.query_service:
            self.query_service.update_query(self.line_edit_search.text())

    def get_search_data(self, data):
        self.data_ready.emit(data)

    def update_word_list(self, word_entry_list):
        logger.DEBUG("update_word_list in")
        self.widget_word_list.clear()
        for word_entry in word_entry_list:
            dict_word = word_entry.to_dict()
            dict_interpretations = dict_word["Interpretations"]
            self.add_word_to_ui(word_entry.word, self.get_first_interpretation(dict_interpretations))

    @staticmethod
    def get_first_interpretation(dict_interpretations):
        for value in dict_interpretations.values():
            if isinstance(value, str) and value.strip() != "":
                return value

    def resizeEvent(self, event: QResizeEvent):
        # if not self.image_label.pixmap():
        #     return
        #
        # pixmap = self.image_label.pixmap()
        # scaled_pixmap = pixmap.scaled(self.image_label.size(), Qt.AspectRatioMode.KeepAspectRatio)
        # self.image_label.setPixmap(scaled_pixmap)

        super().resizeEvent(event)

class WordUI(QWidget):
    def __init__(self, word, definition, size, list_widget, item, book):
        super().__init__()
        self.word = word
        self.list_widget = list_widget
        self.item = item
        self.book = book

        layout = QHBoxLayout(self)
        widget_info = QWidget()
        layout_info = QVBoxLayout(widget_info)
        self.label_word = QLabel(word)
        font_word = QFont()
        font_word.setFamily("Consolas")
        font_word.setPointSize(12)
        font_word.setBold(True)
        self.label_word.setFont(font_word)
        self.label_definition = QLabel(definition)
        self.label_definition.setStyleSheet("color: grey;")
        layout_info.addWidget(self.label_word)
        layout_info.addWidget(self.label_definition)
        layout.addWidget(widget_info, 1)

    def remove_self(self):
        if self.book.delete_vocabulary_book(self.word):
            row = self.list_widget.row(self.item)
            self.list_widget.takeItem(row)
        else:
            MessageBox("Delete vocabulary book failed.")

class AddWordDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add new word")
        self.setFixedSize(500,500)
        self.word_label = QLabel("Word:")
        self.word_label.setMinimumHeight(50)
        self.word_line_edit = QLineEdit()
        self.word_line_edit.setMinimumHeight(50)
        self.phonetic_uk_line_edit = QLineEdit()
        self.phonetic_us_line_edit = QLineEdit()
        self.interpretation_list = QListWidget()
        self.interpretation_list.setMinimumHeight(500)
        self.add_add_button()

        form = QFormLayout(self)
        form.addRow(self.word_label, self.word_line_edit)
        form.addRow("Phonetic_UK:", self.phonetic_uk_line_edit)
        form.addRow("Phonetic_US:", self.phonetic_us_line_edit)
        form.addRow(self.interpretation_list)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)

    def values(self):
        definition = self.get_definition_dict()
        definition["Word"] = self.word_line_edit.text()
        definition["Phonetic_UK"] = self.phonetic_uk_line_edit.text()
        definition["Phonetic_US"] = self.phonetic_us_line_edit.text()
        word_entry = WordEntry.from_flat_dict(definition)
        return word_entry

    def add_add_button(self):
        item = QListWidgetItem()
        item_size = QSize(0, 50)
        item.setSizeHint(item_size)

        button_add = QPushButton("+")
        button_add.clicked.connect(self.add_definition_to_ui)
        self.interpretation_list.addItem(item)
        self.interpretation_list.setItemWidget(item, button_add)

    def add_definition_to_ui(self):
        item = QListWidgetItem()
        item_size = QSize(0, 50)
        item.setSizeHint(item_size)
        try:
            definition_ui = self.WordDefinitionEntry(self.interpretation_list, item)
        except Exception as e:
            logger.ERROR(f"Add word definition failed. error: {e}")
            return
        item.setData(Qt.UserRole, definition_ui)
        self.interpretation_list.addItem(item)
        self.interpretation_list.setItemWidget(item, definition_ui)

    def get_definition_dict(self):
        definition_dict = {}
        for i in range(self.interpretation_list.count()):
            list_item = self.interpretation_list.item(i)
            definition_entry = self.interpretation_list.itemWidget(list_item)
            if isinstance(definition_entry, self.WordDefinitionEntry):
                dict_value, value = definition_entry.value()
                dict_key = InterpretationsMap[dict_value]
                if dict_key not in definition_dict:
                    definition_dict[dict_key] = f"{dict_value}. "
                definition_dict[dict_key] += value + "；"
        return definition_dict

    class WordDefinitionEntry(QWidget):
        def __init__(self, list_widget, item, parent=None):
            super().__init__(parent)
            self.list_widget = list_widget
            self.item = item
            self.combobox_interpretation = QComboBox(self)
            list_interpretations = InterpretationsMap.keys()
            self.combobox_interpretation.addItems(list_interpretations)
            self.combobox_interpretation.setCurrentIndex(0)
            self.line_edit_definition = QLineEdit()
            self.button_remove = QPushButton("-")
            self.button_remove.clicked.connect(self.remove_self)

            layout = QHBoxLayout(self)
            layout.addWidget(self.combobox_interpretation)
            layout.addWidget(self.line_edit_definition)
            layout.addWidget(self.button_remove)

        def value(self):
            return self.combobox_interpretation.currentText(), self.line_edit_definition.text()

        def remove_self(self):
            try:
                row = self.list_widget.row(self.item)
                self.list_widget.takeItem(row)
            except Exception as e:
                logger.ERROR(f"Add word definition failed. error: {e}")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    vocabulary_book_manager = VocabularyBookManager("default")
    book_manager_ui = WordManagerUI(vocabulary_book_manager, "50_A")
    book_manager_ui.show()
    sys.exit(app.exec_())