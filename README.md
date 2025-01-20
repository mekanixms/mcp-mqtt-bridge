# MQTT MCP Server for Claude

A FastMCP-based MQTT bridge that enables Claude to interact with MQTT devices and messages. This server acts as a middleware between Claude and an MQTT broker, allowing Claude to monitor and control IoT devices through MQTT protocol.

## Overview

This server provides Claude with the ability to:
- Monitor MQTT messages in real-time
- Publish messages to MQTT topics
- Subscribe to new topics
- Track message history
- Manage MQTT broker connections

## Installation

1. Ensure you have Python 3.7 or higher installed. Clone the repository and cd into the clone folder.

2. Install the required packages:
```bash
pip install -r requirements.txt
```

## Configuration

1. Edit the MQTT broker settings in `mqtt_mcp_server.py`:
```python
broker = "your_broker_ip"
port = 1883
username = "your_username"
password = "your_password"
```

Locate claude_desktop_config.json and use the template below to add "MQTT Bridge" to the mcpServers section.
MacOs: ~/Library/Application Support/Claude/claude_desktop_config.json
Windows: C:\Users\<username>\AppData\Roaming\Claude\claude_desktop_config.json
  
```json
{
  "mcpServers": {
    "MQTT Bridge": {
      "command": "/path/to/python3.12",
      "args": [
        "path/to/mqtt_mcp_server.py"
      ],
      "env": {
        "CLAUDE_MCP_MQTT_BROKER": "your broker ip",
        "CLAUDE_MCP_MQTT_PORT": "1883",
        "CLAUDE_MCP_MQTT_USERNAME": "username",
        "CLAUDE_MCP_MQTT_PASSWORD": "password"
      }
    }
  }
}
```

## Message Logs

2. Active session messages are logged in different locations based on your operating system:
- Windows: `R:\inMessages.txt`
- macOS: `/Volumes/hgst4T/ClaudeMCP-FS-Folder/inMessages.txt`
- Linux: `/tmp/inMessages.txt`
Change the path to your own folder.

## MCP Tools Available to Claude

### Message Management
- `messagesByTopic`: Retrieve messages for a specific topic
- `allMessages`: Get all messages ordered by timestamp

### MQTT Operations
- `publish`: Send a message to an MQTT topic
- `subscribe`: Subscribe to a new MQTT topic
- `subscribedTopics`: List all currently subscribed topics

### Connection Management
- `broker`: Get information about the connected broker
- `is_connected_to_broker`: Check connection status

## Default Topics

The server automatically subscribes to below topics. Change them to your needs.
- claude/commands
- claude/status
- devices/#
- mqdevcmds
- mqperipheralcmds
- statusupdate
- DEVCONF
- PRESENCE
- DEVLASTWILL
- DEVONLINE
- mqhomeintercom
- DISPLAY
- SETMIN
- SETMAX

## Running the Server

Start the server with:
```bash
python mqtt_mcp_server.py
```

The server will:
1. Connect to the configured MQTT broker
2. Subscribe to the default topics
3. Begin monitoring messages
4. Log all messages with timestamps

## Message Logging

Messages are logged in a tab-separated format:
```
timestamp    topic    payload
```

## Dependencies

- fastmcp>=0.1.0
- paho-mqtt>=1.6.1

## Error Handling

The server includes automatic handling for:
- Connection failures with automatic reconnection
- Message parsing errors
- Subscription/publication issues
- Broker disconnections

## Security Note

Remember to:
- Use strong credentials for MQTT authentication
- Keep your broker credentials secure
- Update the default credentials in the configuration