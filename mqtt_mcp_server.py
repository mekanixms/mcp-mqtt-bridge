#!python

from mcp.server.fastmcp import FastMCP, Context
import paho.mqtt.client as mqtt
import json
from typing import Optional, Dict, Any
import sys
import os
import time
import asyncio

# Create an MCP server with explicit dependencies
mcp = FastMCP(
    "MQTT Bridge",
    dependencies=["paho-mqtt>=1.6.1"]
)

# Check if running on Windows or macOS
if sys.platform == "win32":
    MESSAGES_LOG_PATH = 'R:\inMessages.txt'
elif sys.platform == "darwin":
    MESSAGES_LOG_PATH = '/Volumes/hgst4T/ClaudeMCP-FS-Folder/inMessages.txt'
else:
    MESSAGES_LOG_PATH = '/tmp/inMessages.txt'

# MQTT client setup
mqtt_client = None
is_connected = False
message_stack_by_topic = {}
message_stack_by_timestamp = {}
last_message_timestamp = 0
user_topics = [
    "claude/commands",
    "claude/status", 
    "devices/#",
    "mqdevcmds",
    "mqperipheralcmds",
    "statusupdate",
    "DEVCONF",
    "PRESENCE", 
    "DEVLASTWILL",
    "DEVONLINE",
    "mqhomeintercom",
    "DISPLAY",
    "SETMIN",
    "SETMAX"
]
subscribed_topics = []
# REPLACE WITH YOUR OWN VALUES
broker = "192.168.88.243"
port = 1883
username = "mqhome"
password = "ipaq2490b"

def get_connection_credentials()->list:
    global broker, port, username, password
    return [broker, port, username, password]

@mcp.tool("messagesByTopic")
def get_messages_by_topic(topic) -> list:
    global message_stack_by_topic
    return message_stack_by_topic[topic]

@mcp.tool("allMessages")
def get_messages_by_timestamp() -> list:
    global message_stack_by_timestamp
    return message_stack_by_timestamp


def new_message(topic, payload)->str:
    global message_stack_by_timestamp, message_stack_by_topic,last_message_timestamp,MESSAGES_LOG_PATH
    last_message_timestamp = int(time.time())
    
    if topic in message_stack_by_topic.keys():
        message_stack_by_topic[topic].append(f"{topic}: {payload}")
    else:
        message_stack_by_topic[topic] = [f"{topic}: {payload}",]

    message_stack_by_timestamp[last_message_timestamp] = message_stack_by_topic[topic][-1]

    with open(MESSAGES_LOG_PATH, 'a') as f:
        f.write(f"{last_message_timestamp}\t{topic}:\t{payload}\n")
        f.close()    

    return f"New message received for topic {topic}: {payload}"

@mcp.tool()
def setup_mqtt(broker="localhost", port=1883, username=None, password=None, topics=None):
    """Setup MQTT client with custom configuration"""
    global mqtt_client, is_connected, subscribed_topics
    topicsToSubscribe = []
    if topics:
        topicsToSubscribe = topics
    
    mqtt_client = mqtt.Client()
    
    # Set username and password if provided
    if username and password:
        mqtt_client.username_pw_set(username, password)
    
    def on_connect(client, userdata, flags, rc):
        global is_connected
        if rc == 0:
            is_connected = True
            # Subscribe to all configured topics
            for topic in topicsToSubscribe:
                client.subscribe(topic)
                subscribed_topics.append(topic)
                
            return {"status": "connected"}
        else:
            is_connected = False
            error_messages = {
                1: "Connection refused - incorrect protocol version",
                2: "Connection refused - invalid client identifier",
                3: "Connection refused - server unavailable",
                4: "Connection refused - bad username or password",
                5: "Connection refused - not authorized"
            }
            return {"status": "failed", "error": error_messages.get(rc, f"Unknown error {rc}")}
    
    def on_message(client, userdata, msg):
        global message_stack_by_topic
        topic = msg.topic
        try:
            payload = json.loads(msg.payload.decode())
        except:
            payload = msg.payload.decode()

        new_message(str(topic), str(payload))

    def on_disconnect(client, userdata, rc):
        global is_connected
        is_connected = False
        if rc != 0:
            print(f"Unexpected disconnection. Reason: {rc}")
    
    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message
    mqtt_client.on_disconnect = on_disconnect
    
    try:
        mqtt_client.connect(broker, port)
        mqtt_client.loop_start()
        
        # Wait for connection to be established
        retry_count = 0
        while not is_connected and retry_count < 10:
            time.sleep(1)
            retry_count += 1
            
        return is_connected
    except Exception as e:
        print(f"Failed to connect to MQTT broker: {str(e)}")
        return False


@mcp.tool()
async def data_stream_updated() -> bool:
    """Get the latest data from a specific MQTT topic"""
    global is_connected, last_message_timestamp
    current_time = int(time.time())
    if not is_connected:
        return False
    
    if current_time - last_message_timestamp > 1:
                return True

# Tool to publish to MQTT topic
@mcp.tool("publish")
def publish(topic: str, message, retain: bool = False) -> str:
    """Publish a message to an MQTT topic
    
    Args:
        topic: The MQTT topic to publish to
        message: The message to publish (will be converted to JSON if possible)
        retain: Whether to retain the message
    """
    global mqtt_client, is_connected
    
    if not is_connected:
        try:
            # Try to reconnect
            broker, port, username, password = get_connection_credentials()
            if not setup_mqtt(broker, port, username, password):
                return "Failed to reconnect to MQTT broker"
        except Exception as e:
            return f"Failed to reconnect to MQTT broker: {str(e)}"
    
    try:
        # Try to parse message as JSON
        try:
            msg_data = json.loads(message)
            payload = json.dumps(msg_data)
        except:
            payload = message
            
        result = mqtt_client.publish(topic, payload, retain=retain)
        if result.rc == 0:
            return f"Successfully published to {topic}"
        else:
            return f"Failed to publish to {topic}: {result.rc}"
    except Exception as e:
        return f"Error publishing to MQTT: {str(e)}"

@mcp.tool()
def is_connected_to_broker()->bool:
    global mqtt_client
    return mqtt_client.is_connected()

@mcp.tool("broker")
def get_connected_broker()->str:
    if mqtt_client.is_connected():
        return f"{mqtt_client.host}:{mqtt_client.port} as {mqtt_client.username}"
    else:
        return "MQTT client not connected"

# Tool to subscribe to a new topic
@mcp.tool("subscribe")
def subscribe_mqtt(topic: str) -> str:
    """Subscribe to a new MQTT topic
    
    Args:
        topic: The MQTT topic to subscribe to
    """
    global mqtt_client, is_connected
    
    if not is_connected:
        return "MQTT client not connected"
        
    try:
        subscribed_topics.append(topic)
        result = mqtt_client.subscribe(topic)
        if result[0] == 0:
            return f"Successfully subscribed to {topic}"
        else:
            return f"Failed to subscribe to {topic}: {result[0]}"
    except Exception as e:
        return f"Error subscribing to MQTT: {str(e)}"

# List available topics
@mcp.tool("subscribedTopics")
def list_mqtt_topics():
    """List all currently subscribed MQTT topics"""
    global is_connected
    if not is_connected:
        return "MQTT client not connected"
    return subscribed_topics

# @mcp.tool("monitor")
async def check_messages_stream() -> dict:
    while True:
        if data_stream_updated():
            return {
                "messages": message_stack_by_topic,
                "timestamp": last_message_timestamp
            }
        
        time.sleep(0.1)

def main():
    global user_topics,mqtt_client
    broker, port, username, password = get_connection_credentials()

    # Setup MQTT connection
    if not setup_mqtt(
        broker=broker,
        port=port,
        username=username,
        password=password,
        topics=user_topics
    ):
        print("Failed to setup MQTT connection")
        sys.exit(1)
    # Run the MCP server
    mcp.run()
    # Start background loop to get topic data


if __name__ == "__main__":
    main()
