from PyQt6.QtCore import pyqtSignal, QObject
from src.gui.devices.frontend.generic_mqtt_device import GenericMqttDevice

class UniversalMqttDevice(GenericMqttDevice):
    """
    A generic MQTT device driver that can handle multiple channels/parameters dynamically.
    It emits a signal (topic, payload) for ANY message received on its subscribed topics.
    """
    message_received_signal = pyqtSignal(str, str)

    def __init__(self, base_topic, broker_address="localhost"):
        super().__init__(base_topic, broker_address)
        self.subscriptions = set()

    def subscribe_param(self, suffix):
        """
        Subscribes to base_topic + "/" + suffix.
        """
        full_topic = f"{self.topic_base}/{suffix}"
        if full_topic not in self.subscriptions:
            self.mqtt.subscribe(full_topic)
            self.subscriptions.add(full_topic)
        try:
             self.mqtt.message_received.disconnect(self._on_global_message)
        except:
             pass
        self.mqtt.message_received.connect(self._on_global_message)

    def publish_param(self, suffix, value):
        """
        Publishes value to base_topic + "/" + suffix.
        """
        full_topic = f"{self.topic_base}/{suffix}"
        self.mqtt.publish(full_topic, str(value))

    def _on_global_message(self, topic, payload):
        """
        Filters messages. If topic starts with base_topic, emit signal with suffix.
        """
        if topic.startswith(self.topic_base):
            if len(topic) > len(self.topic_base):
                suffix = topic[len(self.topic_base):].lstrip('/')
                self.message_received_signal.emit(suffix, payload)
