# Example 1: Admin Mistake — Port Administratively Shut Down

> The agent detects a critical interface was accidentally shut down, autonomously brings it back up, and verifies connectivity is restored.

![Example 1 Demo](example1.gif)

---

## Scenario

An administrator accidentally shuts down interface `Ethernet3/0`, breaking connectivity to VIP `192.168.254.10`.

```bash
interface e3/0
  shutdown
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

The agent inspects `Ethernet3/0`. Result: **administratively down**.

```json
{"interface": "Ethernet3/0", "admin_state": "administratively", "oper_state": "down"}
```

**Step 3 — Check interface configuration**

The agent retrieves the running config for the interface to understand what's configured:

```
interface Ethernet3/0
 switchport access vlan 100
 switchport mode access
 shutdown
 duplex auto
```

The `shutdown` command is present, and VLAN 100 is already correctly configured — so the only fix needed is to bring the port back up.

**Step 4 — Apply corrective action**

The LLM reasons with **100% confidence** that `no shutdown` is the correct fix and executes it.

```
🎯 CONFIDENCE: 100% [████████████████████]
   BASIS: The interface state is reported as administratively down, which must be
          corrected using the 'no shutdown' command to bring the port up and restore connectivity.
```

```json
{"interface": "Ethernet3/0", "action": "no shutdown", "status": "applied"}
```

**Step 5 — Verify fix**

The agent re-checks VIP reachability. Result: **reachable** ✅

```json
{"ip": "192.168.254.10", "reachable": true}
```

**Step 6 — Final verdict**

```
🔧 VERDICT [CORRECTIVE]: The VIP was unreachable because the port was administratively
   shut down. Corrective action was taken to bring the port up, restoring connectivity.

📝 SUMMARY: The interface Ethernet3/0 was found to be administratively shut down,
   causing loss of connectivity to 192.168.254.10. Executed 'no shutdown' on the
   interface, which restored endpoint reachability.

🛡️ PREVENTION: Consider implementing proactive monitoring (e.g., SNMP traps) for
   interface administrative state changes to alert operations before service impact.
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
| Total  | 175.68s               | ~13s                |
| LLM    | 153.10s (87%)         | ~11s (84%)          |
| MCP    | 22.56s (13%)          | ~2s (16%)           |
