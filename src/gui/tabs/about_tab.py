from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame, QHBoxLayout, QSpacerItem, QSizePolicy
from PyQt6.QtGui import QPainter
from src.gui.assets.csstyle import Style, Palette
from src.gui.assets.theme_manager import ThemeManager
from src.gui.widgets.smaller_toggle import AnimatedToggle

class AboutTab(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.layout.setContentsMargins(20, 20, 20, 20)

        # Main Container
        self.container = QFrame()
        self.container_layout = QVBoxLayout(self.container)
        self.container_layout.setSpacing(20)
        self.layout.addWidget(self.container)

        # Title
        self.lbl_title = QLabel("MIMIC Control System")
        self.lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.container_layout.addWidget(self.lbl_title)


        accent = "#999999"

        description_text = (
            f"<h3 style='text-align: center; font-family: Segoe UI, sans-serif; font-weight: normal;'>"
            f"<span style='font-weight: bold; color: {accent};'>M</span>QTT "
            f"<span style='font-weight: bold; color: {accent};'>I</span>nterface for "
            f"<span style='font-weight: bold; color: {accent};'>M</span>odular "
            f"<span style='font-weight: bold; color: {accent};'>I</span>nstrument "
            f"<span style='font-weight: bold; color: {accent};'>C</span>ontrol"
            f"</h3>"
        )
        self.lbl_desc = QLabel(description_text)
        self.lbl_desc.setWordWrap(True)
        self.lbl_desc.setAlignment(Qt.AlignmentFlag.AlignJustify)
        # self.container_layout.addWidget(self.svg_widget)
        self.container_layout.addWidget(self.lbl_desc)

        self.divider = QFrame()
        self.divider.setFrameShape(QFrame.Shape.HLine)
        self.divider.setFrameShadow(QFrame.Shadow.Sunken)
        self.container_layout.addWidget(self.divider)

        settings_layout = QHBoxLayout()
        self.lbl_theme = QLabel("Dark Mode")
        settings_layout.addWidget(self.lbl_theme)

        self.theme_toggle = AnimatedToggle()
        self.theme_toggle.setObjectName("settings_dark_mode")
        self.theme_toggle.setChecked(ThemeManager.get_theme() == "dark")
        self.theme_toggle.toggled.connect(self._on_theme_toggled)
        settings_layout.addWidget(self.theme_toggle)

        settings_layout.addStretch()
        self.container_layout.addLayout(settings_layout)

        self.container_layout.addStretch()

        self.apply_theme()



    def _on_theme_toggled(self, checked):
        theme = "dark" if checked else "light"
        ThemeManager.set_theme(theme)

    def apply_theme(self):
        theme = ThemeManager.get_theme()
        is_dark = theme == "dark"

        if is_dark:
            self.setStyleSheet(Style.Default.dark)
            self.container.setStyleSheet(Style.Frame.content_dark)
            self.lbl_title.setStyleSheet(Style.Label.title_dark)
            self.lbl_title.setStyleSheet("font-size: 24px; font-weight: bold; color: " + Palette.D_TEXT_MAIN)
            self.lbl_desc.setStyleSheet(Style.Label.frequency_big_dark)
            self.lbl_theme.setStyleSheet(Style.Label.title_dark)
        else:
            self.setStyleSheet(Style.Default.light)
            self.container.setStyleSheet(Style.Frame.container_light)
            self.lbl_title.setStyleSheet("font-size: 24px; font-weight: bold; color: " + Palette.L_TEXT_MAIN)
            self.lbl_desc.setStyleSheet(Style.Label.frequency_big)
            self.lbl_theme.setStyleSheet(Style.Label.title_light)

        self.theme_toggle.blockSignals(True)
        self.theme_toggle.setChecked(is_dark)
        self.theme_toggle.blockSignals(False)
