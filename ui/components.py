"""Reusable lightweight Qt presentation components."""

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QComboBox, QFrame, QLabel, QPushButton, QVBoxLayout


class GlassPanel(QFrame):
    def __init__(self):
        super().__init__()
        self.setObjectName("glass")
        self.content = QVBoxLayout(self)
        self.content.setContentsMargins(20, 20, 20, 20)
        self.content.setSpacing(12)


class SectionHeader(QLabel):
    def __init__(self, text):
        super().__init__(text.upper())
        self.setObjectName("section")


class ModernButton(QPushButton):
    def __init__(self, text, primary=False):
        super().__init__(text)
        self.setMinimumHeight(36)
        if primary:
            self.setObjectName("primary")


class StatusChip(QLabel):
    def __init__(self, text):
        super().__init__()
        self.setObjectName("chip")
        self.setMaximumHeight(32)
        self.pulse = QTimer(self)
        self.pulse.setInterval(850)
        self.pulse.timeout.connect(self.animate)
        self.phase = True
        self.label = text
        self.update_status(text, False)

    def update_status(self, text, active=False):
        self.label = text
        self.setText(("●  " if active and self.phase else "○  ") + text)
        if self.property("active") != active:
            self.setProperty("active", active)
            self.pulse.start() if active else self.pulse.stop()
            self.style().unpolish(self)
            self.style().polish(self)

    def animate(self):
        self.phase = not self.phase
        self.setText(("●  " if self.phase else "○  ") + self.label)


class Notification(QLabel):
    def __init__(self):
        super().__init__("Ready")
        self.setObjectName("subtitle")
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(lambda: self.setText("Ready"))

    def show_message(self, text):
        self.setText(text)
        self.timer.start(2200)


class ValueCombo(QComboBox):
    """Human labels with stable internal values, including legacy setter support."""

    def setCurrentText(self, text):
        index = self.findData(text)
        if index >= 0:
            self.setCurrentIndex(index)
        else:
            super().setCurrentText(text)


class PreviewLabel(QLabel):
    """Aspect-correct paint at any layout size without pixmap size-hint expansion."""

    def __init__(self):
        from PySide6.QtWidgets import QSizePolicy

        super().__init__()
        self.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)

    def paintEvent(self, event):
        from PySide6.QtCore import QRect, Qt
        from PySide6.QtGui import QColor, QPainter

        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor("#090f17"))
        pixmap = self.pixmap()
        if pixmap and not pixmap.isNull():
            size = pixmap.size().scaled(self.size(), Qt.KeepAspectRatio)
            target = QRect(
                (self.width() - size.width()) // 2,
                (self.height() - size.height()) // 2,
                size.width(),
                size.height(),
            )
            painter.setRenderHint(QPainter.SmoothPixmapTransform)
            painter.drawPixmap(target, pixmap)
