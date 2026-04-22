🚀 AI Network Agent (Local, Autonomous, Context-Aware)

A local, agentic AI that monitors a network switch, understands context, and autonomously fixes issues — without overreacting to normal user behavior.

🎯 Why This Exists

Traditional network automation:

reacts to events
applies static rules
cannot distinguish intent vs anomaly

This project demonstrates:

👉 Closed-loop, context-aware remediation using AI + MCP

🧠 What Makes This Different

This is NOT:

a script running show commands
a chatbot for networking

This IS:

🧠 Context-aware reasoning
🔁 Closed-loop automation
🛠️ Tool-based architecture (MCP)
🏠 100% local (no external APIs)

🏗️ Architecture


🧪 Demo Scenarios
✅ 1. Admin Mistake (Auto-Heal)
interface e0/1
shutdown

🧠 Agent:

detects admin down
executes no shutdown
verifies fix

✅ 2. Misconfiguration (Auto-Fix)
Wrong VLAN

🧠 Agent:

detects connectivity issue
applies correct config
🧰 Tech Stack
MCP Server: FastMCP
Network Automation: Netmiko
Local AI: Ollama
Lab: GNS3 + Cisco IOL

🚀 Getting Started
1. Start MCP Server
python mcp_server/server.py
2. Run Agent
python agent/agent.py
3. Simulate Failures
shutdown interface
disconnect endpoint
change VLAN

🧠 Key Insight

The intelligence is not the LLM.

👉 It’s the context you provide to it:

interface state
endpoint presence
recent history
🔒 Local-First Design
No cloud APIs
No external telemetry
Fully self-contained

👉 Suitable for enterprise environments with strict data policies

📌 Future Improvements
VLAN misconfig detection
interface flapping detection
memory (event history)
confidence scoring
multi-device support
🤝 Contributing

PRs welcome. Especially for:

better parsing (Genie/TextFSM)
additional remediation scenarios
performance improvements
⭐ If This Was Useful

Give it a star ⭐ — it helps others discover it.