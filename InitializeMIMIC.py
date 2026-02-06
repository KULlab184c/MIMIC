import sys
import os
from pathlib import Path

def setup_path():
    """
    Searches for the project root by looking for 'MIMIC.py' 
    and adds it to sys.path.
    """
    # Start at the file invoking this function
    # We use inspection because __file__ here would be mimic_link.py itself
    import inspect
    try:
        frame = inspect.stack()[1]
        start_path = Path(frame.filename).resolve()
    except:
        start_path = Path.cwd()

    current = start_path
    
    # Walk up until we find the marker file 'MIMIC.py'
    while current != current.parent:
        if (current / "MIMIC.py").exists():
            if str(current) not in sys.path:
                sys.path.insert(0, str(current))
                print(f"MIMIC Root linked: {current}")
            return
        current = current.parent

    print("Error: Could not find MIMIC root directory.")
    
    
def configure_mqtt_environment():
    """
    Detects if the environment requires a Mock MQTT client.
    Patches sys.modules to substitute paho.mqtt with the mock if needed.
    """
    mock_mqtt = None
    
    # 1. Try importing the mock from known locations
    try:
        import tests.mock_paho_mqtt_plugin as mock_mqtt
    except ImportError:
        try:
            import mock_paho_mqtt_plugin as mock_mqtt
        except ImportError:
            pass

    # 2. Apply patch if mock is found
    if mock_mqtt:
        sys.modules["paho"] = mock_mqtt
        sys.modules["paho.mqtt"] = mock_mqtt
        sys.modules["paho.mqtt.client"] = mock_mqtt
        mock_mqtt.client = mock_mqtt
        print(">> [System] WARNING: Running with MOCK MQTT Environment")

setup_path()
