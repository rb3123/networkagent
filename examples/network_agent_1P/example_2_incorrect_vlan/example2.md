# Example 2: Misconfiguration — Incorrect VLAN on User Port

> The agent detects a VLAN mismatch on a user-facing port, autonomously corrects it, and verifies connectivity is restored.

![Example 2 Demo](example2.gif)

---

## Scenario

An endpoint is moved to a port configured with the wrong VLAN (`99` instead of `100`), breaking connectivity to VIP `192.168.254.10`.

```
interface Ethernet3/0
 switchport access vlan 99
 switchport mode access
 duplex auto
```

---

## Agent Walkthrough

### Cycle #1 — Detect, Analyze, Fix, Verify

**Step 1 — Check VIP reachability**

The agent pings the VIP endpoint. Result: **unreachable**.

```json
{"ip": "192.168.254.10", "reachable": false}
```

**Step 2 — Check interface state**

The agent inspects `Ethernet3/0`. Result: **up/up** — the port is physically fine.

```json
{"interface": "Ethernet3/0", "admin_state": "up", "oper_state": "up"}
```

**Step 3 — Check interface configuration**

The agent retrieves the running config for the interface:

```
interface Ethernet3/0
 switchport access vlan 99
 switchport mode access
 duplex auto
```

The port is up and not shut down, but the access VLAN is `99` — it should be `100`.

**Step 4 — Apply corrective action**

The LLM reasons with **95% confidence** that the VLAN needs to be changed from 99 to 100 and applies the fix.

```
🎯 CONFIDENCE: 95% [███████████████████░]
   BASIS: The monitoring rules require changing the access VLAN from the current
          VLAN 99 to the specified VLAN 100 for the endpoint port.
```

```json
{"tool": "apply_config", "args": ["interface Ethernet3/0", "switchport access vlan 100"]}
```

```json
{"status": "applied"}
```

**Step 5 — Verify fix**

The agent re-checks VIP reachability. Result: **reachable** ✅

```json
{"ip": "192.168.254.10", "reachable": true}
```

**Step 6 — Final verdict**

```
🔧 VERDICT [CORRECTIVE]: The VIP 192.168.254.10 was initially unreachable. The issue
   was identified as the incorrect access VLAN (VLAN 99) on port Ethernet3/0, which
   was corrected by changing it to the required VLAN 100.

📝 SUMMARY: The VIP 192.168.254.10 was unreachable. I corrected the configuration on
   interface Ethernet3/0 by changing the access VLAN from 99 to 100. The endpoint is
   now reachable.

🛡️ PREVENTION: Verify that the expected access VLAN for this endpoint is 100 in the
   network documentation, and consider implementing port security or AAA/NAC to prevent
   manual misconfigurations of VLANs.
```

### Cycle #2 — Steady State

Subsequent cycles confirm the VIP remains reachable with no action needed.

```
✅ VERDICT [NONE]: VIP is reachable, no action needed.
```

---

## Timing

| Metric | Cycle #1 (Remediation) | Cycle #2+ (Steady) |
|:-------|:----------------------:|:-------------------:|
| Total  | 294.68s               | ~29s                |
| LLM    | 96.15s (33%)          | ~13s (43%)          |
| MCP    | 20.84s (7%)           | ~2s (8%)            |
