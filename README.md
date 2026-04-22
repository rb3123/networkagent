# 🚀 AI Network Agent (Local, Autonomous, Context-Aware)

A local, agentic AI that monitors network infrastructure, understands context, and autonomously remediates issues—without overreacting to normal user behavior.

---

## 🎯 Why This Exists

Traditional network automation often fails because it:
*   **Reacts blindly** to events.
*   **Applies static rules** that don't account for environment changes.
*   **Cannot distinguish** between intentional administrative changes and genuine anomalies.

**This project demonstrates closed-loop, context-aware remediation using AI + MCP (Model Context Protocol).**

---

## 🧠 What Makes This Different?

This is **NOT**:
*   ❌ A simple script running `show` commands.
*   ❌ A basic chatbot for networking queries.

This **IS**:
*   🧠 **Context-aware reasoning**: Evaluates state before acting.
*   🔁 **Closed-loop automation**: Detects, analyzes, fixes, and verifies.
*   🛠️ **Tool-based architecture**: Uses MCP to bridge the gap between LLMs and CLI.
*   🏠 **100% Local**: Privacy-focused, running entirely on your hardware.

---

## 🏗️ Architecture

![High Level Lab Design](architecture/high_level_lab_design.png)

The system utilizes an MCP server to provide the LLM with specific "tools" (via Netmiko) to interact with Cisco switches, while Ollama handles the reasoning logic locally.

---

## 🧪 Demo Scenarios

### ✅ 1. Admin Mistake (Auto-Heal)
**Scenario:** An administrator accidentally shuts down a critical trunk interface.

```bash
interface e3/0
  shutdown
```

**Agent Action:**
1.  **Detects** the `admin down` state.
2.  **Analyzes** the interface's importance based on connected neighbors.
3.  **Executes** `no shutdown`.
4.  **Verifies** the link is back up.

### ✅ 2. Misconfiguration (Auto-Fix)
**Scenario:** An endpoint is moved to a port with the wrong VLAN assigned, breaking connectivity.

**Agent Action:**
1.  **Detects** a connectivity issue.
2.  **Applies** the correct VLAN configuration.
3.  **Confirms** end-to-end reachability.

---

## 🧰 Tech Stack

| Component              | Technology                                    |
|:-----------------------|:----------------------------------------------|
| **MCP Server**         | [FastMCP](https://github.com/jlowin/fastmcp)  |
| **Network Automation** | [Netmiko](https://github.com/ktbyers/netmiko) |
| **Local AI Engine**    | [Ollama](https://ollama.com/)                 |
| **Local LLM**          | [Gemma4(E4B)](https://deepmind.google/models/gemma/gemma-4/#e2b-and-e4b)            |
| **Lab Environment**    | GNS3                                          |

---

## 🚀 Getting Started

1.  **Start the MCP Server:**
    ```bash
    python mcp_server/server.py
    ```
2.  **Run the Agent:**
    ```bash
    python agent/network_agent_1P.py
    ```
3.  **Simulate Failures:**
    *   Shut down a critical interface.
    *   Change a production VLAN.
    *   Apply an ACL to deny traffic.
    *   Pause a connection on GNS3.

---

## 🧠 Key Insight

> The intelligence is not just the LLM; it is the **context** you provide to it.

The agent makes decisions based on:
*   Real-time interface states.
*   Endpoint presence.
*   Recent configuration history.

---

## 🔒 Local-First Design

*   No cloud APIs.
*   No external telemetry.
*   Fully self-contained.
*   **Suitable for enterprise environments with strict data privacy policies.**

---

## 📌 Future Improvements

- [ ] VLAN misconfiguration detection.
- [ ] Interface flapping detection and dampening.
- [ ] Long-term memory (event history database).
- [ ] Confidence scoring for autonomous actions.
- [ ] Multi-vendor/Multi-device support.

---

## 🤝 Contributing

PRs are welcome! 

⭐ **If this was useful, give it a star — it helps others discover the project!**