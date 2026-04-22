import asyncio
import json
import re
import sys
import time
import textwrap
from string import Template
import requests
from datetime import datetime
from fastmcp import Client
from fastmcp.client.transports import StreamableHttpTransport

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "gemma4:e4b"
MCP_URL = "http://localhost:8000/mcp"
CHECK_INTERVAL = 30
PRINT_DELAY = 0.02  # seconds per character for slow printing

VIP_IP = "192.168.254.10"
USER_PORT = "Ethernet3/0"
ACCESS_VLAN = 100

SYSTEM_PROMPT = Template(textwrap.dedent("""\
    You are a network operations AI agent. You monitor a VIP endpoint and take corrective action when needed.
    You can also review configuration as a junior network engineer and suggest fixes.

    You have access to a Cisco IOS switch through an MCP server. The MCP server acts as a bridge —
    when you call a tool, it connects to the Cisco IOS switch and executes the corresponding CLI
    commands on your behalf. All tool responses contain real output from the switch.
    Use tools by responding with a JSON tool call.

    AVAILABLE TOOLS (use exact parameter names):
    - check_endpoint(ip: str) — Ping an IP from the switch. Returns {"ip": str, "reachable": bool}.
    - get_interface_state(interface: str) — Get admin/oper state. Returns {"interface": str, "admin_state": str, "oper_state": str}.
    - get_interface_config(interface: str) — Get running-config for an interface. Returns {"interface": str, "config": str}.
    - get_running_config() — Get full running-config of the switch. Returns {"config": str}. Prefer get_interface_config when you only need one interface.
    - no_shutdown(interface: str) — Execute "no shutdown" on an interface. Returns {"interface": str, "action": str, "status": str}.
    - apply_config(config_list: list) — Apply a list of IOS config commands. Returns {"status": str, "error": str if failed}.

    MONITORING RULES:
    1. First, always check if VIP $vip_ip is reachable using check_endpoint.
    2. If VIP is reachable, respond with: {"action": "none", "reason": "VIP is reachable, no action needed."}
    3. If VIP is NOT reachable, check the state of interface $user_port using get_interface_state.
    4. If $user_port admin_state AND oper_state are both "down", the user has probably left for the day.
       Respond with: {"action": "none", "reason": "User port $user_port is down/down. User has probably left for the day."}
    5. If $user_port is NOT in down/down state, perform corrective action:
       - First, check the current interface config using get_interface_config to see what's already configured.
       - If the interface is administratively down, bring it up using no_shutdown.
       - If access vlan $access_vlan is NOT already configured, apply it using apply_config.
       - If any fixes are applied as part of step 5, verify VIP reachability again with check_endpoint.
         After config change, network may take 10-15 seconds to reconverge. Try check_endpoint 2 more times.
    6. If no issues were found at the port level, perhaps there is an issue in the overall configuration on switch.
        Review full config and raise an alert about any issues found so that a senior network engineer can review the proposal. 

    RESPONSE FORMAT:
    To call a tool that READS data (check_endpoint, get_interface_state, get_interface_config, get_running_config), respond ONLY with JSON:
    {"tool": "<tool_name>", "args": {<arguments>}}

    To call a tool that CHANGES config (no_shutdown, apply_config), respond ONLY with JSON:
    {"tool": "<tool_name>", "args": {<arguments>}, "confidence": <0-100>, "confidence_basis": "<1-2 sentence explanation>"}
    Confidence scoring guide:
    - 90-100: Clear evidence from tool results directly points to this fix.
    - 70-89: Strong indication but some ambiguity.
    - 50-69: Reasonable guess based on limited data.
    - Below 50: Uncertain — consider gathering more data before acting.

    When done with NO changes made, respond ONLY with JSON:
    {"action": "none", "reason": "<explanation>"}

    When done AFTER making corrective changes, respond ONLY with JSON:
    {"action": "corrective", "reason": "<explanation>", "summary": "<what was wrong and what was fixed>", "prevention": "<recommendation to prevent recurrence>"}

    Do NOT include any text outside the JSON.
""")).substitute(vip_ip=VIP_IP, user_port=USER_PORT, access_vlan=ACCESS_VLAN)


def slow_print(text: str, delay: float = PRINT_DELAY):
    """Print text character-by-character for readability."""
    for ch in text:
        sys.stdout.write(ch)
        sys.stdout.flush()
        time.sleep(delay)
    sys.stdout.write("\n")
    sys.stdout.flush()


def call_ollama(messages: list) -> tuple[str, str | None, float]:
    """Returns (content, thinking, elapsed_seconds) tuple."""
    start = time.perf_counter()
    resp = requests.post(
        OLLAMA_URL,
        json={"model": MODEL, "messages": messages, "stream": False, "think": True},
        timeout=120,
    )
    elapsed = time.perf_counter() - start
    resp.raise_for_status()
    msg = resp.json()["message"]
    return msg.get("content", ""), msg.get("thinking"), elapsed


def parse_json_response(text: str) -> dict:
    text = text.strip()
    # Handle markdown code blocks
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text[3:]
        text = text.rsplit("```", 1)[0]
        text = text.strip()
    # Try parsing as-is first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # Fallback: fix triple+ curly braces from LLM (e.g. {{{...}}} -> {...})
    text = re.sub(r'\{{3,}', '{', text)
    text = re.sub(r'\}{3,}', '}', text)
    return json.loads(text)


async def run_agent_cycle(client: Client, cycle: int):
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"\n{'='*60}")
    print(f"[{timestamp}] Monitoring cycle #{cycle}")
    print(f"{'='*60}")

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Run monitoring check now. Start by checking if VIP {VIP_IP} is reachable."},
    ]

    cycle_start = time.perf_counter()
    total_llm_time = 0.0
    total_mcp_time = 0.0

    for step in range(10):  # max 10 tool calls per cycle
        print(f"\n--- Step {step + 1}: Asking AI ---")
        ai_response, thinking, llm_elapsed = call_ollama(messages)
        total_llm_time += llm_elapsed
        print(f"  ⏱️  LLM response time: {llm_elapsed:.2f}s")

        if thinking:
            print(f"\n  💭 THINKING:")
            for line in thinking.strip().splitlines():
                slow_print(f"     {line}")

        print(f"\n  🤖 RESPONSE:")
        slow_print(f"  {ai_response}")

        try:
            parsed = parse_json_response(ai_response)
        except (json.JSONDecodeError, ValueError):
            print(f"  ⚠️  Could not parse AI response, ending cycle.")
            break

        # Final verdict — no more tool calls
        if "action" in parsed and "tool" not in parsed:
            action = parsed.get("action", "unknown")
            reason = parsed.get("reason", "No reason provided.")
            icon = "✅" if action == "none" else "🔧"
            slow_print(f"\n  {icon} VERDICT [{action.upper()}]: {reason}")

            if action == "corrective":
                summary = parsed.get("summary")
                prevention = parsed.get("prevention")
                if summary:
                    slow_print(f"\n  📝 SUMMARY: {summary}")
                if prevention:
                    slow_print(f"  🛡️  PREVENTION: {prevention}")

            cycle_elapsed = time.perf_counter() - cycle_start
            print(f"\n  ⏱️  CYCLE TIMING:")
            print(f"       Total cycle:  {cycle_elapsed:.2f}s")
            print(f"       LLM time:     {total_llm_time:.2f}s ({total_llm_time/cycle_elapsed*100:.0f}%)")
            print(f"       MCP time:     {total_mcp_time:.2f}s ({total_mcp_time/cycle_elapsed*100:.0f}%)")
            print(f"       Overhead:     {cycle_elapsed - total_llm_time - total_mcp_time:.2f}s")
            break

        # Tool call
        tool_name = parsed.get("tool")
        tool_args = parsed.get("args", {})

        if not tool_name:
            print("  ⚠️  No tool or action in response, ending cycle.")
            break

        # Normalize: AI sometimes sends args as a list for apply_config
        if isinstance(tool_args, list) and tool_name == "apply_config":
            tool_args = {"config_list": tool_args}

        if isinstance(tool_args, dict):
            args_str = ", ".join(f"{k}={v!r}" for k, v in tool_args.items())
        else:
            args_str = repr(tool_args)
        print(f"\n  🔧 TOOL CALL: {tool_name}({args_str})")

        confidence = parsed.get("confidence")
        confidence_basis = parsed.get("confidence_basis")
        if confidence is not None:
            bar_len = confidence // 5
            bar = "█" * bar_len + "░" * (20 - bar_len)
            print(f"  🎯 CONFIDENCE: {confidence}% [{bar}]")
            if confidence_basis:
                print(f"     BASIS: {confidence_basis}")
        mcp_start = time.perf_counter()
        try:
            result = await client.call_tool(tool_name, tool_args)
            mcp_elapsed = time.perf_counter() - mcp_start
            total_mcp_time += mcp_elapsed
            result_text = str(result)
            print(f"  ⏱️  MCP response time: {mcp_elapsed:.2f}s")
            # Try to pretty-print if it looks like a dict/list
            try:
                result_obj = json.loads(result_text.replace("'", '"'))
                print(f"  📋 RESULT:")
                for k, v in result_obj.items():
                    slow_print(f"       {k}: {v}")
            except (json.JSONDecodeError, AttributeError):
                slow_print(f"  📋 RESULT: {result_text}")
        except Exception as e:
            mcp_elapsed = time.perf_counter() - mcp_start
            total_mcp_time += mcp_elapsed
            result_text = f"ERROR: {e}"
            print(f"  ⏱️  MCP response time: {mcp_elapsed:.2f}s")
            print(f"  ❌ ERROR: {e}")

        messages.append({"role": "assistant", "content": ai_response})
        messages.append({"role": "user", "content": f"Tool result for {tool_name}: {result_text}\n\nContinue with the monitoring rules."})


async def main():
    print(f"Starting Network Agent — monitoring VIP {VIP_IP} every {CHECK_INTERVAL}s")
    print(f"Model: {MODEL} | MCP: {MCP_URL}")

    client = Client(StreamableHttpTransport(MCP_URL))

    async with client:
        tools = await client.list_tools()
        print(f"Connected to MCP. Available tools: {[t.name for t in tools]}")

        cycle = 1
        # while True:
        for _ in range(5):
            try:
                await run_agent_cycle(client, cycle)
            except Exception as e:
                print(f"\nERROR in cycle #{cycle}: {e}")

            cycle += 1
            print(f"\nNext check in {CHECK_INTERVAL}s...")
            await asyncio.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    asyncio.run(main())
