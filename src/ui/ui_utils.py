from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QDialogButtonBox, QHBoxLayout, QVBoxLayout, QLabel, QDialog


class MessageBox(QDialog):
    def __init__(self, message, message_name = "Massage", parent=None):
        super().__init__(parent)
        self.setWindowTitle(message_name)

        label = QLabel(message)
        font = QFont()
        font.setFamily("Consolas")
        font.setPointSize(10)
        label.setFont(font)
        label.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)

        layout_center_label = QHBoxLayout()
        layout_center_label.addStretch(1)
        layout_center_label.addWidget(label)
        layout_center_label.addStretch(1)

        button = QDialogButtonBox(QDialogButtonBox.Ok)
        button.accepted.connect(self.accept)
        layout_center_button = QHBoxLayout()
        layout_center_button.addStretch(1)
        layout_center_button.addWidget(button)
        layout_center_button.addStretch(1)

        layout = QVBoxLayout(self)
        layout.addStretch()
        layout.addLayout(layout_center_label)
        layout.addStretch()
        layout.addLayout(layout_center_button)
        self.exec_()