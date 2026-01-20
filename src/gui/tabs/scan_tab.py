import time
import json
import os
from datetime import datetime
from collections import defaultdict
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QLineEdit,
    QPushButton, QTextEdit, QFrame, QGridLayout, QGroupBox, QStyle, QScrollArea, QSpacerItem
)
from collections import defaultdict
from src.gui.widgets.qtgraph import Graph
from src.gui.assets.csstyle import Style
from src.gui.assets.theme_manager import ThemeManager
from src.gui.assets.scan_controller import ScanWorker
from src.gui.assets.icon_utils import CustomIcon
from src.gui.widgets.noscrollcombobox import NSCB


SCAN_CONFIG_FILE = os.path.join(os.getcwd(), 'config', 'scan_axes.json')


class ScanTab(QWidget):
    def __init__(self, loaded_instruments=[]):
        super().__init__()
        self.loaded_instruments = loaded_instruments
        self.scan_params = []
        self.scan_params_row = []
        self.worker = None
        self.scan_data = None

        self.loading_config = False

        self.axis_widgets = []

        self.init_ui()
        self.populate_params()
        self.load_scan_axes()

    def init_ui(self):
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        self.main_frame = QFrame()
        root_layout.addWidget(self.main_frame)
        self.layout = QHBoxLayout(self.main_frame)
        self.layout.setContentsMargins(10, 10, 10, 10)
        # self.layout.setSpacing(10)

        self.config_container = QFrame()
        config_layout = QVBoxLayout(self.config_container)
        config_layout.setContentsMargins(0, 0, 0, 0)
        self.config_container.setMinimumWidth(320)

        self.grp_axes = QGroupBox("Scan Axes")
        axes_layout = QVBoxLayout(self.grp_axes)

        self.axes_container = QFrame()
        self.axes_layout = QVBoxLayout(self.axes_container)
        self.axes_layout.setContentsMargins(0,0,0,0)
        axes_layout.addWidget(self.axes_container)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_add_axis = QPushButton("Add Axis")
        btn_add_axis.setStyleSheet(Style.Button.suggested)
        btn_add_axis.clicked.connect(self.add_axis_row)
        btn_layout.addWidget(btn_add_axis)
        axes_layout.addLayout(btn_layout)

        config_layout.addWidget(self.grp_axes)

        self.grp_settings = QGroupBox("Settings")

        settings_layout = QVBoxLayout(self.grp_settings)
        settings_layout.setContentsMargins(15, 15, 15, 15)

        delay_layout = QHBoxLayout()
        delay_layout.addWidget(QLabel("Delay Between Datapoints (s):"))
        self.inp_delay = QLineEdit("0.5")
        self.inp_delay.setObjectName("scan_delay")
        self.inp_delay.setFixedWidth(60)
        delay_layout.addWidget(self.inp_delay)
        settings_layout.addLayout(delay_layout)

        repeat_layout = QHBoxLayout()
        repeat_layout.addWidget(QLabel("Repeats:"))
        self.inp_repeats = QLineEdit("1")
        self.inp_repeats.setObjectName("scan_repeats")
        self.inp_repeats.setFixedWidth(60)
        repeat_layout.addWidget(self.inp_repeats)
        settings_layout.addLayout(repeat_layout)


        settings_layout.addWidget(QLabel("Comments:"))
        self.txt_comments = QTextEdit()
        self.txt_comments.setObjectName("scan_comments")
        self.txt_comments.setFixedHeight(120)
        settings_layout.addWidget(self.txt_comments)

        config_layout.addWidget(self.grp_settings)

        config_layout.addStretch()

        self.grp_controls = QGroupBox("")
        controls_layout = QGridLayout(self.grp_controls)

        self.btn_start = QPushButton("Start Scan")
        self.btn_start.setStyleSheet(Style.Button.start)
        self.btn_start.clicked.connect(self.start_scan)

        self.btn_pause = QPushButton("Pause")
        self.btn_pause.setCheckable(True)
        self.btn_pause.setStyleSheet(Style.Button.reset)
        self.btn_pause.clicked.connect(self.toggle_pause)

        self.btn_abort = QPushButton("Abort")
        self.btn_abort.setStyleSheet(Style.Button.stop)
        self.btn_abort.clicked.connect(self.abort_scan)

        self.btn_save = QPushButton("Auto-Save Active")
        self.btn_save.setStyleSheet(Style.Button.disabled)
        self.btn_save.setEnabled(False)

        controls_layout.addWidget(self.btn_start, 0, 0)
        controls_layout.addWidget(self.btn_pause, 0, 1)
        controls_layout.addWidget(self.btn_abort, 1, 0)
        controls_layout.addWidget(self.btn_save, 1, 1)

        config_layout.addWidget(self.grp_controls)

        self.lbl_status = QLabel("Ready")
        config_layout.addWidget(self.lbl_status)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.config_container)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setFixedWidth(340)

        self.layout.addWidget(self.scroll_area)


        self.graph_widget = QFrame()
        graph_layout = QVBoxLayout(self.graph_widget)
        graph_layout.setContentsMargins(10, 10, 10, 10)

        axis_sel_layout = QHBoxLayout()
        axis_sel_layout.addWidget(QLabel("X-Axis:"))
        self.combo_x = QComboBox()
        self.combo_x.setObjectName("scan_x_axis")
        self.combo_x.currentIndexChanged.connect(self.on_combo_update_graph)
        axis_sel_layout.addWidget(self.combo_x)

        axis_sel_layout.addStretch()

        axis_sel_layout.addWidget(QLabel("Y-Axis:"))
        self.combo_y = QComboBox()
        self.combo_y.setObjectName("scan_y_axis")
        self.combo_y.currentIndexChanged.connect(self.on_combo_update_graph)
        axis_sel_layout.addWidget(self.combo_y)

        graph_layout.addLayout(axis_sel_layout)

        self.graph = Graph()
        graph_layout.addWidget(self.graph)

        self.layout.addWidget(self.graph_widget)

        self.apply_theme()

    def populate_params(self):
        self.scan_params = []
        self.scan_params_row = []
        self.all_params = []

        for inst in self.loaded_instruments:
            for param in inst.get_all_params():
                key = f"{inst.name}: {param.name}"
                shorkey = f"{inst.nickname}: {param.name}"
                self.all_params.append((key, param))
                if 'write' in param._access:
                    self.scan_params.append((key, param))
                    self.scan_params_row.append((shorkey, param))

        self.combo_x.clear()
        self.combo_y.clear()

        self.combo_x.addItem("Step Index", "index")

        for name, param in self.scan_params:
            self.combo_x.addItem(name, param)
        for name, param in self.all_params:
            self.combo_y.addItem(name, param)

        for row in self.axis_widgets:
            self._fill_param_combo(row[0])

    def _fill_param_combo(self, combo):
        combo.clear()
        for name, param in self.scan_params_row:
            combo.addItem(name, param)

    def add_axis_row(self):
        frame = QFrame()
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(6)
        line1 = QHBoxLayout()
        combo = NSCB()
        self._fill_param_combo(combo)
        combo.setFixedWidth(130)
        steps_lbl = QLabel("Steps:")
        steps = QLineEdit("10")
        steps.setPlaceholderText("Steps")
        steps.setFixedWidth(60)
        btn_del = QPushButton("")
        btn_del.setIcon(CustomIcon.trash('#F44336'))
        btn_del.setStyleSheet(Style.Button.stop)
        btn_del.setFixedWidth(25)
        btn_del.clicked.connect(lambda: self.remove_axis_row(frame))
        line1.addWidget(combo)
        line1.addWidget(steps_lbl)
        line1.addWidget(steps)
        line1.addWidget(btn_del)
        line1.addStretch()
        line2 = QHBoxLayout()
        lbl_start = QLabel("Start:")
        start = QLineEdit("")
        start.setFixedWidth(85)
        lbl_stop = QLabel("Stop:")
        stop = QLineEdit("")
        stop.setFixedWidth(85)
        line2.addWidget(lbl_start)
        line2.addWidget(start)
        line2.addWidget(lbl_stop)
        line2.addWidget(stop)
        line2.addStretch()
        layout.addLayout(line1)
        layout.addLayout(line2)

        self.axes_layout.addWidget(frame)

        self.axis_widgets.append((combo, start, stop, steps, frame))

        combo.currentIndexChanged.connect(self.save_scan_axes)
        start.editingFinished.connect(self.save_scan_axes)
        stop.editingFinished.connect(self.save_scan_axes)
        steps.editingFinished.connect(self.save_scan_axes)

        self.save_scan_axes()

        self._apply_theme_to_axis_row(combo, start, stop, steps, frame)

    def remove_axis_row(self, frame):
        for i, row in enumerate(self.axis_widgets):
            if row[4] == frame:
                self.axis_widgets.pop(i)
                break
        frame.deleteLater()
        self.save_scan_axes()

    def save_scan_axes(self):
        if hasattr(self, 'loading_config') and self.loading_config:
            return

        axes_data = []
        for combo, start, stop, steps, frame in self.axis_widgets:
            axes_data.append({
                'param_index': combo.currentIndex(),
                'start': start.text(),
                'stop': stop.text(),
                'steps': steps.text()
            })

        try:
            config_dir = os.path.dirname(SCAN_CONFIG_FILE)
            if not os.path.exists(config_dir):
                os.makedirs(config_dir)

            with open(SCAN_CONFIG_FILE, 'w') as f:
                json.dump(axes_data, f, indent=4)
        except Exception as e:
            print(f"Error saving scan axes: {e}")

    def load_scan_axes(self):
        self.loading_config = True
        try:
            if os.path.exists(SCAN_CONFIG_FILE):
                with open(SCAN_CONFIG_FILE, 'r') as f:
                    axes_data = json.load(f)

                if not axes_data:
                    self.add_axis_row()
                else:
                    for axis in axes_data:
                        self.add_axis_row()
                        combo, start, stop, steps, frame = self.axis_widgets[-1]

                        if 'param_index' in axis:
                            if axis['param_index'] < combo.count():
                                combo.setCurrentIndex(axis['param_index'])
                        if 'start' in axis:
                            start.setText(str(axis['start']))
                        if 'stop' in axis:
                            stop.setText(str(axis['stop']))
                        if 'steps' in axis:
                            steps.setText(str(axis['steps']))
            else:
                self.add_axis_row()

        except Exception as e:
            print(f"Error loading scan axes: {e}")
            if not self.axis_widgets:
                self.add_axis_row()
        finally:
            self.loading_config = False

    def start_scan(self):
        axes_config = []
        for combo, start, stop, steps, frame in self.axis_widgets:
            param = combo.currentData()
            if not param: continue
            try:
                axes_config.append({
                    'param': param,
                    'start': float(start.text()),
                    'stop': float(stop.text()),
                    'steps': int(steps.text())
                })
            except ValueError:
                self.lbl_status.setText("Error: Invalid number format in axes.")
                return

        if not axes_config:
            self.lbl_status.setText("Error: No axes defined.")
            return

        try:
            delay = float(self.inp_delay.text())
            repeats = int(self.inp_repeats.text())
        except ValueError:
             self.lbl_status.setText("Error: Invalid settings.")
             return

        config = {
            'axes': axes_config,
            'delay': delay,
            'repeats': repeats,
            'comments': self.txt_comments.toPlainText()
        }

        self.worker = ScanWorker(self.loaded_instruments, config)
        self.worker.data_point_ready.connect(self.on_data_point)
        self.worker.status_update.connect(self.lbl_status.setText)
        self.worker.scan_finished.connect(self.on_scan_finished)
        self.worker.progress_update.connect(self.on_progress)

        self.worker.start()

        self.scan_data = defaultdict(list)

        self.graph.line_curve.setData([], [])

        self.x_data = []
        self.y_data = []
        self.graph.line_curve.setData([], [])
        self.graph.dot_curve.setData([], [])

        self.btn_start.setEnabled(False)
        self.btn_abort.setEnabled(True)
        self.btn_pause.setChecked(False)

    def toggle_pause(self):
        if self.worker:
            self.worker.pause()
            if self.worker.is_paused:
                self.btn_pause.setText("Resume")
            else:
                self.btn_pause.setText("Pause")

    def abort_scan(self):
        if self.worker:
            self.worker.stop()
            self.worker.wait()
        self.on_scan_finished()

    def on_scan_finished(self):
        self.btn_start.setEnabled(True)
        self.btn_abort.setEnabled(False)
        self.lbl_status.setText("Scan Finished")

    def on_progress(self, current, total):
        self.lbl_status.setText(f"Scanning... {current}/{total}")

    def on_data_point(self, data):
        current_index = len(self.scan_data["__index__"])
        self.scan_data["__index__"].append(current_index)
        for key, value in data.items():
            try:self.scan_data[key].append(float(value))
            except ValueError: self.scan_data[key].append(value)
        self.update_graph()

    def on_combo_update_graph(self):
        datax = self.combo_x.itemData(self.combo_x.currentIndex())
        datay = self.combo_y.itemData(self.combo_y.currentIndex())
        if not datax or not datay:
            return

        # print(datax)


        self.graph.getPlotItem().setLabel('left', datay.label or datay.name, units=datay.unit)
        if self.combo_x.currentIndex() == 0:
            self.graph.getPlotItem().setLabel('bottom', "Step Number")
        else:
            self.graph.getPlotItem().setLabel('bottom', datax.label or datax.name, units=datax.unit)

        self.update_graph()

    def update_graph(self):
        if not hasattr(self, 'scan_data') or not self.scan_data:
            return
        def get_data_key(param):
            if param == "index":
                return "__index__"

            for inst in self.loaded_instruments:
                if param in inst.parameters.values():
                    return f"{inst.name}_{param.name}"
            return None

        x_param = self.combo_x.currentData()
        y_param = self.combo_y.currentData()

        x_key = get_data_key(x_param)
        y_key = get_data_key(y_param)

        x_vals = self.scan_data.get(x_key, [])
        y_vals = self.scan_data.get(y_key, [])

        min_len = min(len(x_vals), len(y_vals))
        if min_len > 0:
            self.graph.line_curve.setData(x_vals[:min_len], y_vals[:min_len])
        else:
            self.graph.line_curve.setData([], [])

    def apply_theme(self):
        theme = ThemeManager.get_theme()
        is_dark = theme == "dark"

        if is_dark:
            self.main_frame.setStyleSheet(Style.Frame.content_dark)
            self.config_container.setStyleSheet(Style.Frame.content_dark)
            self.grp_axes.setStyleSheet(Style.GroupBox.dark_gray)
            self.grp_settings.setStyleSheet(Style.GroupBox.dark)
            self.inp_delay.setStyleSheet(Style.Input.line_edit_dark)
            self.inp_repeats.setStyleSheet(Style.Input.line_edit_dark)
            self.txt_comments.setStyleSheet(Style.Input.text_edit_dark)
            self.grp_controls.setStyleSheet(Style.GroupBox.dark_gray)
            self.lbl_status.setStyleSheet(Style.Label.title_dark)
            self.scroll_area.setStyleSheet(Style.Scroll.combined)
            self.graph_widget.setStyleSheet(Style.Frame.container_dark)
            self.combo_x.setStyleSheet(Style.ComboBox.dark)
            self.combo_y.setStyleSheet(Style.ComboBox.dark)
            self.axes_container.setStyleSheet(Style.Frame.container_dark)
        else:
            self.main_frame.setStyleSheet(Style.Frame.content_light)
            self.config_container.setStyleSheet(Style.Frame.content_light)
            self.grp_axes.setStyleSheet(Style.GroupBox.light_gray)
            self.grp_settings.setStyleSheet(Style.GroupBox.light)
            self.inp_delay.setStyleSheet(Style.Input.line_edit_light)
            self.inp_repeats.setStyleSheet(Style.Input.line_edit_light)
            self.txt_comments.setStyleSheet(Style.Input.text_edit_light)
            self.grp_controls.setStyleSheet(Style.GroupBox.light_gray)
            self.lbl_status.setStyleSheet(Style.Label.title_light)
            self.scroll_area.setStyleSheet(Style.Scroll.combined)
            self.graph_widget.setStyleSheet(Style.Frame.container_light)
            self.combo_x.setStyleSheet(Style.ComboBox.light)
            self.combo_y.setStyleSheet(Style.ComboBox.light)
            self.axes_container.setStyleSheet(Style.Frame.container_light)


        for combo, start, stop, steps, frame in self.axis_widgets:
            self._apply_theme_to_axis_row(combo, start, stop, steps, frame)

    def _apply_theme_to_axis_row(self, combo, start, stop, steps, frame):
        theme = ThemeManager.get_theme()
        is_dark = theme == "dark"

        if is_dark:
            frame.setStyleSheet(Style.Frame.container_dark)
            combo.setStyleSheet(Style.ComboBox.dark)
            start.setStyleSheet(Style.Input.line_edit_dark)
            stop.setStyleSheet(Style.Input.line_edit_dark)
            steps.setStyleSheet(Style.Input.line_edit_dark)
        else:
            frame.setStyleSheet(Style.Frame.container_light)
            combo.setStyleSheet(Style.ComboBox.light)
            start.setStyleSheet(Style.Input.line_edit_light)
            stop.setStyleSheet(Style.Input.line_edit_light)
            steps.setStyleSheet(Style.Input.line_edit_light)