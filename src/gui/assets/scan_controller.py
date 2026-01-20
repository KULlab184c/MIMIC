import os
import csv
import time
import datetime
import itertools
from PyQt6.QtCore import QThread, pyqtSignal

class DataLogger:
    def __init__(self, directory="data"):
        self.directory = directory
        self._ensure_directory()
        self.filename = self._generate_filename()
        self.headers = []

    def _ensure_directory(self):
        if not os.path.exists(self.directory):
            os.makedirs(self.directory)

    def _generate_filename(self):
        i = 1
        while True:
            fname = os.path.join(self.directory, f"scan__{i:03d}.csv")
            if not os.path.exists(fname):
                return fname
            i += 1

    def init_log(self, headers, comments=""):
        self.headers = headers
        with open(self.filename, 'w', newline='') as f:
            if comments:
                f.write(f"# Comments: {comments}\n")
            writer = csv.DictWriter(f, fieldnames=self.headers)
            writer.writeheader()

    def log(self, data):
        with open(self.filename, 'a', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=self.headers)
            writer.writerow(data)

class ScanWorker(QThread):
    # Signals
    data_point_ready = pyqtSignal(dict)
    scan_finished = pyqtSignal()
    progress_update = pyqtSignal(int, int) # current, total
    status_update = pyqtSignal(str)

    def __init__(self, instruments, scan_config):
        super().__init__()
        self.instruments = instruments
        self.config = scan_config
        self.is_running = True
        self.is_paused = False
        self.logger = None

    def run(self):
        try:
            axes = self.config['axes']
            delay = self.config['delay']
            repeats = self.config['repeats']

            axis_ranges = []
            for axis in axes:
                start = float(axis['start'])
                stop = float(axis['stop'])
                steps = int(axis['steps'])

                if steps <= 1:
                    vals = [start]
                else:
                    step_size = (stop - start) / (steps - 1)
                    vals = [start + i * step_size for i in range(steps)]

                if repeats > 1:
                    base_vals = list(vals)
                    full_vals = list(base_vals)
                    current_dir = 1
                    for r in range(repeats - 1):
                        if current_dir == 1:
                            full_vals.extend(base_vals[-2::-1])
                            current_dir = -1
                        else:
                            full_vals.extend(base_vals[1:])
                            current_dir = 1
                    axis_ranges.append(full_vals)
                else:
                    axis_ranges.append(vals)

            scan_points = list(itertools.product(*axis_ranges))
            total_points = len(scan_points)

            self.status_update.emit(f"Starting scan with {total_points} points...")

            self.logger = DataLogger()
            dummy_data = self.snapshot_instruments()
            self.logger.init_log(list(dummy_data.keys()), self.config.get('comments', ''))
            self.status_update.emit(f"Saving to {self.logger.filename}")

            for idx, point in enumerate(scan_points):
                if not self.is_running: break

                while self.is_paused:
                    self.msleep(100)
                    if not self.is_running: break

                for i, val in enumerate(point):
                    param = axes[i]['param']
                    if param.set_cmd:
                        param.set_cmd(val)
                        param.current_value = val

                if delay > 0:
                    time.sleep(delay)

                for axis in axes:
                    if axis['param'].param_type == 'wm_freq':
                        self.status_update.emit(f"Waiting for stability: {axis['param'].name}")
                        self.wait_for_stability(axis['param'])

                data_row = self.snapshot_instruments()

                self.logger.log(data_row)
                self.data_point_ready.emit(data_row)
                self.progress_update.emit(idx + 1, total_points)

            self.status_update.emit("Scan Finished.")
            self.scan_finished.emit()

        except Exception as e:
            self.status_update.emit(f"Error: {str(e)}")
            print(f"Scan Error: {e}")

    def wait_for_stability(self, param):
        self.msleep(1200)

        timeout = 60 # seconds
        start_t = time.time()
        while time.time() - start_t < timeout:
            if not self.is_running: return
            if param.stable:
                return
            self.msleep(100)
        self.status_update.emit(f"Timeout waiting for {param.name}")

    def snapshot_instruments(self):
        data = {}
        data['timestamp'] = datetime.datetime.now().isoformat()
        for inst in self.instruments:
            for param in inst.get_all_params():
                key = f"{inst.name}_{param.name}"
                data[key] = param.current_value
        return data

    def stop(self):
        self.is_running = False

    def pause(self):
        self.is_paused = not self.is_paused
