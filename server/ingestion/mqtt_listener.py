from __future__ import annotations

import argparse
from pathlib import Path

import paho.mqtt.client as mqtt

EVENTS_LOG = Path("data/events/mqtt_events.log")
EVENTS_LOG.parent.mkdir(parents=True, exist_ok=True)


def on_connect(client: mqtt.Client, _userdata, _flags, rc: int):
    if rc != 0:
        print(f"MQTT connect failed: rc={rc}")
        return
    print("MQTT connected")
    client.subscribe("stableguard/+/events")
    client.subscribe("stableguard/+/heartbeat")


def on_message(_client: mqtt.Client, _userdata, msg: mqtt.MQTTMessage):
    line = f"{msg.topic} {msg.payload.decode(errors='replace')}\n"
    EVENTS_LOG.write_text(
        EVENTS_LOG.read_text() + line if EVENTS_LOG.exists() else line
    )
    print(line.strip())


def main() -> None:
    parser = argparse.ArgumentParser(description="StableGuard MQTT listener")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=1883)
    args = parser.parse_args()

    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(args.host, args.port, keepalive=60)
    client.loop_forever()


if __name__ == "__main__":
    main()
