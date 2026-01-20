import time
import random
import threading
import numpy as np
import paho.mqtt.client as mqtt
from simple_pid import PID

UPDATE_RATE = .1 #seconds


class InstrumentSimulator:
    def __init__(self, client: mqtt.Client):
        self.client = client

    def tick(self):
        pass

    def on_message(self, topic: str, payload: str):
        pass

class SimulatedSensor(InstrumentSimulator):
    def __init__(self, client):
        super().__init__(client)
        self.topic = "sensor/serial_number"

    def tick(self):
        count_roi = int(random.gauss(500, 50))
        if count_roi < 0: count_roi = 0
        self.client.publish(f"{self.topic}/counts/ROI", str(count_roi))

        count_full = int(random.gauss(2000, 100))
        if count_full < 0: count_full = 0
        self.client.publish(f"{self.topic}/counts/full", str(count_full))


class SimulatedWavemeter(InstrumentSimulator):
    def __init__(self, client, channels=8):
        super().__init__(client)
        self.channels = channels
        self.base_topic = "DWM/serial_number"

        self.current_freqs = {}
        self.pids = {}

        for ch in range(1, channels + 1):
            initial_setpoint = 200.0 + ch * 20 * np.pi
            self.current_freqs[ch] = initial_setpoint
            pid = PID(0.0, 0.015/UPDATE_RATE, 0.0, setpoint=initial_setpoint)
            pid.output_limits = (-10.0, 10.0)  # Slew rate limit
            self.pids[ch] = pid

    def tick(self):
        for ch in range(1, self.channels + 1):
            current_val = self.current_freqs[ch]
            correction = self.pids[ch](current_val)
            noise = (random.random() - 0.9) * 0.000002
            new_freq = correction*100 + noise
            self.current_freqs[ch] = new_freq
            self.client.publish(f"{self.base_topic}/frequency/{ch}", f"{new_freq:.6f}")

    def on_message(self, topic: str, payload: str):
        if not topic.startswith(self.base_topic+"/SET/frequency"):
            return

        chnl = int(topic[-1])
        setpoint = float(payload)

        self.pids[chnl].setpoint = setpoint
        print(f'[WM SETPOINT] channel: {chnl}, setpoint {setpoint}')


class SimulatedPowerSupply(InstrumentSimulator):
    def __init__(self, client, device_id, serial_number, channels=3):
        super().__init__(client)
        self.topic_base = f"{device_id}/{serial_number}"
        self.channels = channels
        self.voltages = {ch: 0.0 for ch in range(1, channels+1)}
        self.currents = {ch: 0.0 for ch in range(1, channels+1)}
        self.enabled = {ch: False for ch in range(1, channels+1)}
        self.enabled[1] = True
        self.voltages[1] = 10.2
        self.currents[1] = 3.5


    def tick(self ):
        for ch in range(1, self.channels + 1):
            self.client.publish(f"{self.topic_base}/voltage/{ch}", str(self.voltages[ch]+(random.random()-random.random())/100))
            self.client.publish(f"{self.topic_base}/current/{ch}", str(self.currents[ch]+(random.random()-random.random())/1000))
            self.client.publish(f"{self.topic_base}/output/{ch}", str(self.enabled[ch]))


    def on_message(self, topic, payload):
        if not topic.startswith(self.topic_base):
            return
        suffix = topic[len(self.topic_base):].strip('/')
        parts = suffix.split('/')
        if len(parts) >= 3 and parts[0] == 'SET':
            cmd = parts[1]
            try:
                ch = int(parts[2])

                if cmd == 'voltage':
                    val = float(payload)
                    self.voltages[ch] = val
                    print(f"[SimBackend] PSU {self.topic_base} Ch{ch} Voltage -> {val}V")

                elif cmd == 'current':
                    val = float(payload)
                    self.currents[ch] = val
                    #self.client.publish(f"{self.topic_base}/current/{ch}", str(val))
                    print(f"[SimBackend] PSU {self.topic_base} Ch{ch} Current -> {val}A")

                elif cmd == 'output':
                    val = payload.lower() in ['true', '1', 'on']
                    self.enabled[ch] = val
                    # self.client.publish(f"{self.topic_base}/output/{ch}", str(val))
                    print(f"[SimBackend] PSU {self.topic_base} Ch{ch} Output -> {val}")

            except Exception as e:
                print(f"[SimBackend] PSU Error: {e}")



class SimulatedShutter(InstrumentSimulator):
    def __init__(self, client):
        super().__init__(client)
        self.topic_base = "shutter/serial_number"
        self.state = False

    def on_message(self, topic, payload):
        if not topic.startswith(self.topic_base):
            return

        suffix = topic[len(self.topic_base):].strip('/')
        if suffix == "SET/out":
             val = payload.lower() in ['true', '1', 'on']
             self.state = val
             self.client.publish(f"{self.topic_base}/out", str(val))
             print(f"[SimBackend] Shutter -> {val}")


class FakeBackend:
    def __init__(self):
        self.client = mqtt.Client(client_id="FakeBackend_Controller")
        self.client.on_message = self.on_message_dispatch

        self.client.connect("localhost")
        self.running = False

        self.simulators = []

        self.simulators.append(SimulatedSensor(self.client))

        wm = SimulatedWavemeter(self.client)
        self.simulators.append(SimulatedWavemeter(self.client))
        self.client.subscribe("DWM/serial_number/SET/frequency/#")

        ps1 = SimulatedPowerSupply(self.client, "PowerSupply", "serial_number")
        self.simulators.append(ps1)
        self.client.subscribe("powersupply/serial_number/SET/#")

        sh = SimulatedShutter(self.client)
        self.simulators.append(sh)
        self.client.subscribe("shutter/serial_number/SET/#")

    def on_message_dispatch(self, client, userdata, msg):
        topic = msg.topic
        payload = msg.payload.decode()

        for sim in self.simulators:
            sim.on_message(topic, payload)

    def run(self):
        self.running = True
        self.client.loop_start()
        print(">> [FakeBackend] Simulation Running...")

        while self.running:
            for sim in self.simulators:
                sim.tick()
            time.sleep(UPDATE_RATE) # Update rate

    def stop(self):
        self.running = False
        self.client.loop_stop()
        print(">> [FakeBackend] Stopped.")
