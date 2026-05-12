from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout

from app.ui.feedback import future_action
from app.ui.theme import COLORS


class OpenSourcePanel(QFrame):
    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("Panel")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(12)
        header = QHBoxLayout()
        mark = QLabel("<>")
        mark.setFixedSize(34, 34)
        mark.setAlignment(Qt.AlignmentFlag.AlignCenter)
        mark.setStyleSheet(
            f"background: rgba(124, 58, 237, 0.18); color: {COLORS['purple_soft']}; "
            "border-radius: 10px; font-weight: 900;"
        )
        title = QLabel("Feito com codigo aberto")
        title.setObjectName("SmallTitle")
        header.addWidget(mark)
        header.addWidget(title, 1)
        body = QLabel("LearnKit e aberto, local e feito para a comunidade.")
        body.setObjectName("Muted")
        body.setWordWrap(True)
        button = QPushButton("Ver no GitHub")
        button.setObjectName("GhostButton")
        button.setToolTip("Repositorio publico ainda nao configurado.")
        button.clicked.connect(lambda: future_action(self, "Link do repositorio GitHub"))
        layout.addLayout(header)
        layout.addWidget(body)
        layout.addWidget(button)
