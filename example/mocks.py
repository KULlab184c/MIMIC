import sys
from collections import defaultdict
import threading
import time


class MockMQTTMessage:
    def __init__(self, topic, payload):
        self.topic = topic
        self.payload = payload.encode('utf-8') if isinstance(payload, str) else payload



class MockBroker:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(MockBroker, cls).__new__(cls)
                cls._instance.subscribers = defaultdict(list)
                cls._instance.retained_messages = {}
        return cls._instance

    def subscribe(self, topic, client):

        if client not in self.subscribers[topic]:
            self.subscribers[topic].append(client)

    def unsubscribe(self, topic, client):
        if topic in self.subscribers:
            if client in self.subscribers[topic]:
                self.subscribers[topic].remove(client)

    def publish(self, topic, payload, retain=False):
        if retain:
            self.retained_messages[topic] = payload

        for sub_pattern, clients in list(self.subscribers.items()):
            match = False
            if sub_pattern == topic:
                match = True
            elif sub_pattern.endswith('#'):
                prefix = sub_pattern[:-1]
                if topic.startswith(prefix):
                    match = True
            elif sub_pattern.endswith('+'):
                 prefix = sub_pattern[:-1]
                 if topic.startswith(prefix) and '/' not in topic[len(prefix):]:
                     match = True

            if match:
                msg = MockMQTTMessage(topic, payload)
                for client in clients:
                    if client.on_message:
                        try:
                            client.on_message(client, client._userdata, msg)
                        except Exception as e:
                            print(f"[MockBroker] Error in callback: {e}")


class MockMQTTClient:
    def __init__(self, client_id="", clean_session=True, userdata=None, protocol=4, transport="tcp"):
        self.client_id = client_id
        self._userdata = userdata
        self.broker = MockBroker()

        self.on_connect = None
        self.on_message = None
        self.on_disconnect = None

        self.connected = False
        self._loop_thread = None
        self._loop_running = False

    def connect(self, host, port=1883, keepalive=60):
        self.connected = True
        if self.on_connect:

            self.on_connect(self, self._userdata, {}, 0)
        return 0

    def disconnect(self):
        self.connected = False
        if self.on_disconnect:
            self.on_disconnect(self, self._userdata, 0)

    def subscribe(self, topic, qos=0):
        self.broker.subscribe(topic, self)

        for retained_topic, payload in self.broker.retained_messages.items():
            if retained_topic == topic:
                 msg = MockMQTTMessage(retained_topic, payload)
                 if self.on_message:
                     self.on_message(self, self._userdata, msg)
        return (0, 1)

    def unsubscribe(self, topic):
        self.broker.unsubscribe(topic, self)
        return (0, 1)

    def publish(self, topic, payload=None, qos=0, retain=False):
        self.broker.publish(topic, payload, retain)
        return None

    def loop_start(self):
        self._loop_running = True
        pass

    def loop_stop(self, force=False):
        self._loop_running = False
        pass

    def loop_forever(self):
        self.loop_start()
        while self._loop_running:
            time.sleep(0.1)

Client = MockMQTTClient

if "sys" in locals():
    this_module = sys.modules[__name__]
    client = this_module
    mqtt = this_module
