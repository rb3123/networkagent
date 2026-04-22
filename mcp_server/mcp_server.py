from fastmcp import FastMCP
from netmiko import ConnectHandler
import subprocess

mcp = FastMCP("network-agent")

# ---- Device Config ----
DEVICE = {
    'host':'192.168.152.128',
     'port':5001,
      'device_type':'cisco_ios_telnet', 
      'username':'cisco', 
      'secret':'cisco',
}


@mcp.tool(description="Simple greeting tool for testing connectivity to the MCP server. Returns a greeting message with the provided name.")
def greet(name: str) -> str:
    return f"Hello, {name}!"


def get_connection():
    return ConnectHandler(**DEVICE)


# ---- TOOL 1: Get Interface State ----
@mcp.tool(description="""Retrieve the administrative and operational status of a specific network interface on the Cisco switch.
Use this tool to diagnose whether an interface is up/down before taking corrective action.
Returns a dict with 'interface', 'admin_state' (e.g. 'administratively down' or 'up'), and 'oper_state' (e.g. 'up' or 'down').
""")
def get_interface_state(interface: str) -> dict:
    """
    Args:
        interface: Cisco IOS interface name, e.g. 'GigabitEthernet0/1', 'FastEthernet0/0', 'Loopback0'.
    """
    conn = get_connection()
    output = conn.send_command(f"show ip interface brief | include {interface}")
    conn.disconnect()

    parts = output.split()

    return {
        "interface": interface,
        "admin_state": parts[4],
        "oper_state": parts[5]
    }


# ---- TOOL 2: Check Endpoint ----
@mcp.tool(description="""Ping an IP address from the Cisco switch to check Layer 3 reachability.
Use this tool to verify if a remote host or endpoint is reachable from the switch's perspective.
Returns a dict with 'ip' and 'reachable' (true/false). A timeout of 60 seconds is used.
""")
def check_endpoint(ip: str) -> dict:
    """
    Args:
        ip: IPv4 address of the target endpoint, e.g. '10.0.0.1'.
    """
    conn = get_connection()
    output = conn.send_command(f"ping {ip}", read_timeout=60)
    conn.disconnect()

    return {
        "ip": ip,
        "reachable": False if 'Success rate is 0 percent' in output else True
    }


# ---- TOOL 3: Enable Interface ----
@mcp.tool(description="""Execute 'no shutdown' on a Cisco switch interface to bring it administratively up.
CAUTION: This is a configuration change. Only use this when the interface admin_state is 'administratively down' and it needs to be enabled.
Returns a dict with 'interface', 'action', and 'status' ('applied').
""")
def no_shutdown(interface: str) -> dict:
    """
    Args:
        interface: Cisco IOS interface name to enable, e.g. 'GigabitEthernet0/1'.
    """
    conn = get_connection()

    cmds = [
        f"interface {interface}",
        "no shutdown"
    ]

    conn.send_config_set(cmds)
    conn.disconnect()

    return {
        "interface": interface,
        "action": "no shutdown",
        "status": "applied"
    }


# ---- TOOL 4: Get Interface Running Config ----
@mcp.tool(description="""Retrieve the running configuration of a specific interface on the Cisco switch.
Use this to inspect current config (IP address, switchport mode, VLAN, shutdown state, etc.) before making changes.
Returns a dict with 'interface' and 'config' (the raw IOS config block for that interface).
""")
def get_interface_config(interface: str) -> dict:
    """
    Args:
        interface: Cisco IOS interface name, e.g. 'Ethernet3/0', 'GigabitEthernet0/1'.
    """
    conn = get_connection()
    output = conn.send_command(f"show running-config interface {interface}")
    conn.disconnect()

    return {
        "interface": interface,
        "config": output.strip()
    }


# ---- TOOL 5: Get Full Running Config ----
@mcp.tool(description="""Retrieve the full running configuration of the Cisco IOS switch.
Use this for a complete view of the device config — helpful for auditing, troubleshooting, or verifying overall state.
Returns a dict with 'config' containing the raw output of 'show running-config'.
Note: Output can be large. Prefer get_interface_config when you only need a single interface.
""")
def get_running_config() -> dict:
    conn = get_connection()
    output = conn.send_command("show running-config")
    conn.disconnect()

    return {
        "config": output.strip()
    }


# ---- TOOL 6: Apply Configuration ----
@mcp.tool(description="""Apply a list of Cisco IOS configuration commands to the switch in config mode.
CAUTION: This is a generic configuration tool that can make arbitrary changes to the device.
Use this only when no other specific tool (like no_shutdown) covers the required action.
Commands are applied via 'configure terminal' and exited automatically.
Returns a dict with 'status' ('applied' or 'failed'). If failed, an 'error' field contains the IOS error output or exception message.
""")
def apply_config(config_list: list) -> dict:
    """
    Args:
        config_list: List of Cisco IOS config-mode commands, e.g. ['interface GigabitEthernet0/1', 'ip address 10.0.0.1 255.255.255.0'].
    """
    try:
        conn = get_connection()
        output = conn.send_config_set(config_list)
        conn.disconnect()

        if "%" in output or "Invalid" in output or "Incomplete" in output:
            return {
                "status": "failed",
                "error": output.strip()
            }

        return {
            "status": "applied"
        }
    except Exception as e:
        return {
            "status": "failed",
            "error": str(e)
        }

if __name__ == "__main__":
    mcp.run(transport="streamable-http")