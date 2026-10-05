"""VistaFlow desktop composition. Processing and recognition stay in workers."""

from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from queue import Empty
from time import perf_counter

import cv2
import numpy as np
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QImage, QKeySequence, QPixmap, QShortcut
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QScrollArea,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from core.config import Config
from core.control import GESTURE_HELP, FilterController, gesture_command
from core.models import Command
from core.runtime import VisionRuntime
from ui.components import GlassPanel, ModernButton, PreviewLabel, SectionHeader, StatusChip
from ui.fonts import ensure_font
from ui.theme import STYLE, friendly
from vision.live_filters import FILTERS, apply_filter, load_image
from vision.operations import synthetic_image


class MainWindow(QMainWindow):
    def __init__(self, config=None):
        super().__init__()
        ensure_font()
        self.config = config or Config()
        self.controller = FilterController()
        self.runtime = VisionRuntime(self.config)
        self.pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix="vistaflow-sample")
        self.future = None
        self.load_future = None
        self.requested = True
        self.sample = synthetic_image()
        self.source_name = "Generated sample"
        self.closing = False
        self.setWindowTitle("VistaFlow | Real-Time Image & Video Processing")
        self.resize(1380, 860)
        self.setMinimumSize(1080, 720)
        root = QWidget()
        root.setObjectName("shell")
        self.setCentralWidget(root)
        self.setStyleSheet(STYLE)
        layout = QVBoxLayout(root)
        layout.setContentsMargins(24, 20, 24, 18)
        layout.setSpacing(16)
        header = QHBoxLayout()
        layout.addLayout(header)
        title = QLabel("VISTAFLOW")
        title.setObjectName("brand")
        header.addWidget(title)
        subtitle = QLabel("REAL-TIME IMAGE & VIDEO PROCESSING")
        subtitle.setObjectName("section")
        header.addWidget(subtitle)
        header.addStretch()
        self.camera_chip = StatusChip("Camera off")
        header.addWidget(self.camera_chip)
        self.start = ModernButton("Start camera", True)
        self.start.clicked.connect(self.toggle_camera)
        header.addWidget(self.start)
        toolbar = QHBoxLayout()
        layout.addLayout(toolbar)
        toolbar.addWidget(QLabel("Camera"))
        self.device = QSpinBox()
        self.device.setRange(0, 10)
        self.device.setValue(self.config.camera_index)
        toolbar.addWidget(self.device)
        self.resolution = QComboBox()
        self.resolution.addItem("640 × 480", (640, 480))
        self.resolution.addItem("1280 × 720", (1280, 720))
        configured = (self.config.width, self.config.height)
        index = self.resolution.findData(configured)
        if index < 0:
            self.resolution.addItem(f"{configured[0]} × {configured[1]}", configured)
            index = self.resolution.count() - 1
        self.resolution.setCurrentIndex(index)
        toolbar.addWidget(self.resolution)
        self.tracking = QCheckBox("Hand gestures")
        self.tracking.toggled.connect(self.set_tracking)
        toolbar.addWidget(self.tracking)
        self.compare = QCheckBox("Before / after")
        self.compare.setChecked(True)
        self.compare.clicked.connect(lambda: self.dispatch("COMPARE"))
        toolbar.addWidget(self.compare)
        self.freeze = ModernButton("Freeze preview")
        self.freeze.clicked.connect(lambda: self.dispatch("FREEZE"))
        toolbar.addWidget(self.freeze)
        for label, callback in (("Open image", self.open_image), ("Sample", self.use_sample)):
            button = ModernButton(label)
            button.clicked.connect(callback)
            toolbar.addWidget(button)
        toolbar.addStretch()
        body = QHBoxLayout()
        body.setSpacing(16)
        layout.addLayout(body, 1)
        controls = GlassPanel()
        controls.content.addWidget(SectionHeader("Filter studio"))
        self.operation = QComboBox()
        for name in FILTERS:
            self.operation.addItem(friendly(name), name)
        self.operation.currentIndexChanged.connect(
            lambda: self.dispatch("SET_FILTER", {"operation": self.operation.currentData()})
        )
        controls.content.addWidget(self.operation)
        self.controls = {}
        for name, label, low, high, step in (
            ("brightness", "Brightness · all filters", -100, 100, 5),
            ("contrast", "Contrast · all filters", 0.2, 3, 0.1),
            ("kernel", "Kernel · smoothing / sharpen", 3, 15, 2),
            ("canny_low", "Canny lower threshold", 0, 254, 5),
            ("canny_high", "Canny upper threshold", 1, 255, 5),
            ("strength", "Strength · CLAHE / bilateral / sharpen", 0.1, 8, 0.1),
        ):
            caption = QLabel(label)
            caption.setWordWrap(True)
            caption.setObjectName("subtitle")
            controls.content.addWidget(caption)
            control = QDoubleSpinBox() if name in ("contrast", "strength") else QSpinBox()
            control.setRange(low, high)
            control.setSingleStep(step)
            control.setValue(getattr(self.controller.settings, name))
            self.controls[name] = control
            control.valueChanged.connect(
                lambda value, n=name: self.dispatch("PARAMETERS", {n: value})
            )
            controls.content.addWidget(control)
        reset = ModernButton("Reset filters")
        reset.clicked.connect(lambda: self.dispatch("RESET"))
        controls.content.addWidget(reset)
        note = QLabel(
            "Brightness and contrast are applied first. Kernel and strength affect the named filters. Original uses neutral parameters after Reset."
        )
        note.setWordWrap(True)
        note.setObjectName("subtitle")
        controls.content.addWidget(note)
        controls.content.addStretch()
        body.addWidget(self.scroll(controls, 245))
        center = GlassPanel()
        body.addWidget(center, 1)
        self.caption = QLabel("Generated sample / Original")
        self.caption.setObjectName("cardTitle")
        center.content.addWidget(self.caption)
        previews = QHBoxLayout()
        center.content.addLayout(previews, 1)
        self.original_box = QWidget()
        col = QVBoxLayout(self.original_box)
        col.setContentsMargins(0, 0, 0, 0)
        col.addWidget(SectionHeader("Original"))
        self.original = PreviewLabel()
        col.addWidget(self.original, 1)
        previews.addWidget(self.original_box, 1)
        box = QWidget()
        col = QVBoxLayout(box)
        col.setContentsMargins(0, 0, 0, 0)
        col.addWidget(SectionHeader("Processed"))
        self.processed = PreviewLabel()
        col.addWidget(self.processed, 1)
        previews.addWidget(box, 1)
        self.metrics = QLabel("Camera inactive · Processing the sample in a background worker")
        self.metrics.setWordWrap(True)
        self.metrics.setObjectName("subtitle")
        center.content.addWidget(self.metrics)
        guide = GlassPanel()
        guide.content.addWidget(SectionHeader("Gesture control"))
        self.gesture = QLabel("Awaiting hand")
        self.gesture.setObjectName("cardTitle")
        self.gesture.setWordWrap(True)
        guide.content.addWidget(self.gesture)
        hint = QLabel(
            "Hold a pose, then release before repeating. Camera and Hand gestures must be enabled."
        )
        hint.setWordWrap(True)
        hint.setObjectName("subtitle")
        guide.content.addWidget(hint)
        for name, action in GESTURE_HELP.items():
            label = QLabel(f"{friendly(name)}\n{action}")
            label.setWordWrap(True)
            label.setObjectName("subtitle")
            guide.content.addWidget(label)
        self.debug = QCheckBox("Diagnostics")
        guide.content.addWidget(self.debug)
        self.diagnostics = QLabel()
        self.diagnostics.setWordWrap(True)
        guide.content.addWidget(self.diagnostics)
        guide.content.addStretch()
        body.addWidget(self.scroll(guide, 225))
        self.feedback = QLabel(
            "Local processing. No recordings. Choose a filter or start the camera."
        )
        self.feedback.setObjectName("subtitle")
        self.feedback.setWordWrap(True)
        layout.addWidget(self.feedback)
        for key, intent, params in (
            ("Space", "FREEZE", {}),
            ("Right", "STEP", {"step": 1}),
            ("Left", "STEP", {"step": -1}),
            ("R", "RESET", {}),
        ):
            shortcut = QShortcut(QKeySequence(key), self)
            shortcut.activated.connect(lambda i=intent, p=params: self.dispatch(i, p))
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.poll)
        self.timer.start(30)
        self.sync()

    @staticmethod
    def scroll(widget, width):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(widget)
        scroll.setFixedWidth(width)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        return scroll

    def dispatch(self, intent, params=None):
        return self.execute(Command(intent, "ui", params or {}))

    def execute(self, command):
        try:
            self.controller.dispatch(command)
        except (ValueError, TypeError, KeyError) as error:
            self.feedback.setText(str(error))
            self.sync()
            return False
        self.sync()
        self.requested = True
        self.feedback.setText(
            "Preview frozen; tracking continues."
            if self.controller.frozen
            else "Filter controls updated."
        )
        return True

    def sync(self):
        self.runtime.settings = self.controller.settings
        self.runtime.compare = self.controller.compare
        self.operation.blockSignals(True)
        self.operation.setCurrentIndex(self.operation.findData(self.controller.settings.operation))
        self.operation.blockSignals(False)
        for name, control in self.controls.items():
            control.blockSignals(True)
            control.setValue(getattr(self.controller.settings, name))
            control.blockSignals(False)
        self.compare.setChecked(self.controller.compare)
        self.original_box.setVisible(self.controller.compare)
        self.freeze.setText("Resume preview" if self.controller.frozen else "Freeze preview")

    def set_tracking(self, enabled):
        self.runtime.tracking = enabled
        if not enabled:
            self.gesture.setText("Tracking off")

    def toggle_camera(self):
        if self.runtime.thread and self.runtime.thread.is_alive():
            self.runtime.stop()
            self.start.setText("Stopping…")
        else:
            width, height = self.resolution.currentData()
            self.runtime.config = replace(
                self.config, camera_index=self.device.value(), width=width, height=height
            )
            self.runtime.start(self.tracking.isChecked())
            self.start.setText("Stop camera")
            self.feedback.setText("Opening camera. Initialization may take a few seconds.")

    def open_image(self):
        if self.runtime.thread and self.runtime.thread.is_alive():
            self.feedback.setText("Stop the camera before loading an image.")
            return
        path, _ = QFileDialog.getOpenFileName(
            self, "Open image", "", "Images (*.png *.jpg *.jpeg *.bmp)"
        )
        if path:
            if self.load_future is not None:
                self.feedback.setText("Wait for the current image to finish loading.")
                return
            self.load_future = self.pool.submit(load_image, path)
            self.feedback.setText("Loading image…")

    def use_sample(self):
        if self.load_future is not None:
            self.feedback.setText("Wait for the current image to finish loading.")
            return
        if self.runtime.thread and self.runtime.thread.is_alive():
            self.feedback.setText("Stop the camera to use the sample.")
            return
        self.sample = synthetic_image()
        self.source_name = "Generated sample"
        self.requested = True

    @staticmethod
    def pixmap(image):
        rgb = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB if image.ndim == 2 else cv2.COLOR_BGR2RGB)
        rgb = np.ascontiguousarray(rgb)
        h, w = rgb.shape[:2]
        return QPixmap.fromImage(
            QImage(rgb.data, w, h, rgb.strides[0], QImage.Format_RGB888).copy()
        )

    def render(self, original, processed, source):
        if self.controller.frozen:
            return
        self.original.setPixmap(self.pixmap(original))
        self.processed.setPixmap(self.pixmap(processed))
        self.caption.setText(source + " / " + friendly(self.controller.settings.operation))

    def poll(self):
        if self.closing:
            return
        alive = bool(self.runtime.thread and self.runtime.thread.is_alive())
        active = alive and not self.runtime.stop_event.is_set()
        self.device.setEnabled(not alive)
        self.resolution.setEnabled(not alive)
        self.camera_chip.update_status(
            "Camera active"
            if active and self.runtime.metrics
            else "Camera starting"
            if active
            else "Camera off",
            active and bool(self.runtime.metrics),
        )
        self.runtime.debug = self.debug.isChecked()
        if not alive:
            self.start.setText("Start camera")
        if self.load_future is not None and self.load_future.done():
            future = self.load_future
            self.load_future = None
            try:
                self.sample = future.result()
                self.source_name = "Loaded image"
                self.requested = True
            except (OSError, ValueError, cv2.error):
                self.feedback.setText("Could not open this image. Check the file and try again.")
        if self.future is not None and self.future.done():
            settings, image, future = self.job_settings, self.job_image, self.future
            self.future = None
            try:
                result = future.result()
                if not alive and settings == self.controller.settings and image is self.sample:
                    self.render(image, result, self.source_name)
            except Exception as error:
                self.feedback.setText(f"Image processing unavailable ({type(error).__name__}).")
        if not alive and self.future is None and self.requested:
            self.requested = False
            self.job_settings = self.controller.settings
            self.job_image = self.sample
            self.future = self.pool.submit(apply_filter, self.job_image, self.job_settings)
            self.metrics.setText("Still image · Motion needs a live camera · No image is saved")
        try:
            packet = self.runtime.frames.get_nowait()
            if active and packet.settings == self.controller.settings:
                self.render(
                    packet.original if packet.original is not None else packet.image,
                    packet.image,
                    "Live camera",
                )
        except Empty:
            pass
        try:
            while True:
                event = self.runtime.commands.get_nowait()
                if active and self.runtime.tracking and perf_counter() - event.timestamp < 0.5:
                    command = gesture_command(event)
                    if command and self.execute(command):
                        self.feedback.setText(
                            f"{friendly(event.name)} → {GESTURE_HELP[event.name]}"
                        )
        except Empty:
            pass
        try:
            while True:
                message = self.runtime.messages.get_nowait()
                if message == "CAMERA INACTIVE":
                    self.requested = True
                else:
                    self.feedback.setText(message)
        except Empty:
            pass
        d = self.runtime.diagnostics
        self.gesture.setText(
            friendly(d.get("current", "Awaiting hand"))
            if active and self.runtime.tracking
            else "Tracking inactive"
        )
        self.diagnostics.setVisible(self.debug.isChecked())
        self.diagnostics.setText(
            f"Candidate: {d.get('candidate', '—')}\nScore: {d.get('confidence', 0):.2f}\nHold: {d.get('hold_ms', 0):.0f} ms\nCooldown: {d.get('cooldown_ms', 0):.0f} ms\n{d.get('state', 'IDLE')}\n{d.get('handedness', '')}\nScore is geometry, not accuracy."
        )
        if active and self.runtime.metrics:
            m = self.runtime.metrics
            self.metrics.setText(
                f"Capture {m['capture_fps']:.1f} FPS · Processed {m['processed_fps']:.1f} FPS · {m['processing_ms']:.1f} ms processing"
                + (" · Preview frozen" if self.controller.frozen else "")
            )

    def closeEvent(self, event):
        self.closing = True
        if not self.runtime.close(timeout=0) or any(
            future is not None and not future.done() for future in (self.future, self.load_future)
        ):
            self.feedback.setText("Releasing camera and finishing processing…")
            event.ignore()
            QTimer.singleShot(100, self.close)
            return
        self.timer.stop()
        self.pool.shutdown(wait=False, cancel_futures=True)
        event.accept()
