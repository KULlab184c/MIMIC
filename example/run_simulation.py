import sys
import os
import threading
import InitializeMIMIC
from PyQt6.QtWidgets import QApplication
import example.mocks as mocks
import types
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)
sys.modules["paho"] = mocks
sys.modules["paho.mqtt"] = mocks
sys.modules["paho.mqtt.client"] = mocks
from example.simulation_backend import FakeBackend
from src.gui.main_window import MainWindow

def main():
    os.environ["MIMIC_MODE"] = "MOCK"

    app = QApplication(sys.argv)

    print(">> [Simulation] Starting Fake Backend...")
    backend = FakeBackend()
    sim_thread = threading.Thread(target=backend.run, daemon=True)
    sim_thread.start()

    print(">> [Simulation] Launching Main Window...")
    window = MainWindow()
    window.setWindowTitle("MIMIC [Simulation Mode]")
    window.show()

    print(">> [Simulation] System Ready.")

    try:
        sys.exit(app.exec())
    except Exception as e:
        print(f"Error: {e}")
    finally:
        print(">> [Simulation] Stopping Backend...")
        backend.stop()

if __name__ == "__main__":
    main()
