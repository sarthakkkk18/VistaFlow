"""Shared restrained laboratory palette. Qt logical pixels are DPI-aware."""

BACKGROUND = "#0b131c"
PANEL = "#121f2b"
ACCENT = "#68d9c4"
TEXT = "#e4edf3"
MUTED = "#8fa6b8"
STYLE = """
QMainWindow, QWidget#shell { background: #0b131c; }
QWidget { color: #e4edf3; font-family: 'Segoe UI'; font-size: 13px; }
QFrame#glass { background: rgba(20, 34, 47, 235); border: 1px solid #293c4a; border-radius: 16px; }
QLabel { background: transparent; border: none; }
QLabel#brand { font-size: 30px; font-weight: 600; letter-spacing: 4px; }
QLabel#hero { font-size: 25px; font-weight: 600; color: #e4f0fa; }
QLabel#cardTitle { font-size: 19px; font-weight: 600; color: #d4edf6; }
QLabel#subtitle { color: #8fa6b8; font-size: 12px; }
QLabel#section { color: #8fa6b8; font-size: 11px; font-weight: 600; letter-spacing: 2px; }
QLabel#metric { font-size: 24px; font-weight: 600; color: #c5e9e4; }
QLabel#chip { background: #1c303d; color: #9fb7c5; padding: 6px 10px; border-radius: 10px; }
QLabel#chip[active="true"] { background: #193d3b; color: #86e6cf; }
QPushButton { background: #1b2b39; border: 1px solid #304554; border-radius: 8px; padding: 9px 13px; }
QPushButton:hover { background: #294252; border-color: #50757e; }
QPushButton:pressed, QPushButton:checked { background: #244b4b; border-color: #68d9c4; color: #a5f4df; }
QPushButton:disabled { color: #617585; border-color: #253441; }
QPushButton#primary { background: #68d9c4; border-color: #68d9c4; color: #10272b; font-weight: 600; }
QPushButton#primary:hover { background: #91e7d5; }
QComboBox, QLineEdit, QSpinBox, QDoubleSpinBox { background: #0e1a25; border: 1px solid #304554; border-radius: 8px; padding: 9px; selection-background-color: #305d61; }
QComboBox QAbstractItemView { background: #172b3b; selection-background-color: #305d61; }
QComboBox::drop-down { border: none; width: 24px; }
QLineEdit:focus { border-color: #68d9c4; }
QCheckBox { spacing: 9px; padding: 6px 0; color: #b4c8d6; }
QCheckBox::indicator { width: 28px; height: 15px; border-radius: 7px; background: #2a3a49; border: 1px solid #4a6070; }
QCheckBox::indicator:checked { background: #68d9c4; border-color: #68d9c4; }
QSlider::groove:horizontal { height: 4px; background: #304554; border-radius: 2px; }
QSlider::sub-page:horizontal { background: #68d9c4; border-radius: 2px; }
QSlider::handle:horizontal { width: 12px; margin: -4px 0; background: #d4eee7; border-radius: 6px; }
QScrollArea { background: transparent; border: none; }
QScrollBar:vertical { background: #0b131c; width: 6px; }
QScrollBar::handle:vertical { background: #304554; border-radius: 3px; min-height: 24px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
QToolTip { color: #e4edf3; background: #233c4b; border: 1px solid #4a6978; padding: 6px; }
"""


def friendly(value):
    return str(value).replace("_", " ").strip().capitalize()
