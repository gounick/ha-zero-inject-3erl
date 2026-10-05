# 3ERL Zero-Injection workflow

This document describes the architecture, data flow and operational workflow of the 3ERL Zero-Injection integration.

## End-to-end setup

```mermaid
flowchart TD
    A(["Own a 3ERL contract"]) --> B{"Contract type"}
    B -->|ACI| C1["Use the Bridage signal<br/>Envoy Level 2 = 0%"]
    B -->|ACC| C2["Use the Bridage_CDC signal<br/>Envoy Level 2 = floor %"]
    C1 --> D["Get Installer access on Enphase"]
    C2 --> D
    D --> E["Configure the Envoy DRM relay levels"]
    E --> F["Wire the dry-contact relay"]
    F --> G["Install and configure the integration in HA"]
    G --> H["Verify: relay closes when 3ERL asks for curtailment"]
```

## Architecture overview

```mermaid
flowchart TB
    subgraph HA["Home Assistant"]
        CF["Config Flow"]
        COORD["DataUpdateCoordinator"]
        CTRL["ZeroInjectController"]
        SENS["Sensor / Binary Sensor / Select Entities"]
    end

    API["3ERL API<br/>https://3erl.fr/api.json"]
    RELAY["Dry-contact Relay"]
    INVERTER["PV Inverter (Envoy DRM port)"]
    PV_POWER["Injection Power Sensor"]

    API -->|polls every N minutes| COORD
    PV_POWER -->|state changes| COORD
    COORD --> SENS
    SENS --> CTRL
    CTRL -->|switch.turn_on/off| RELAY
    RELAY -->|limits export| INVERTER
```

## Configuration flow

```mermaid
sequenceDiagram
    participant U as User
    participant CF as Config Flow
    participant API as 3ERL API
    participant HA as Home Assistant

    U->>CF: Add integration
    CF->>U: Ask for API URL, interval, contract type, PV power sensor, relay, notify service
    U->>CF: Submit configuration
    CF->>API: GET /api.json
    API-->>CF: JSON response
    CF->>HA: Create config entry
    HA->>HA: Setup coordinator, controller and entities
```

## Signal selection

The configured contract type selects the API field that drives the relay.

```mermaid
flowchart LR
    A["aggregation_mode option"] --> B{"ACI or ACC?"}
    B -->|ACI| C["Read Bridage"]
    B -->|ACC| D["Read Bridage_CDC"]
    C --> E["Curtailment active?"]
    D --> E
    E --> F["Mode select"]
    F --> G{"Auto / On / Off"}
    G -->|On| H["Relay ON"]
    G -->|Off| I["Relay OFF"]
    G -->|Auto| E
```

## Zero-injection state machine

The controller re-evaluates whenever the mode select or the curtailment signal changes.

```mermaid
stateDiagram-v2
    [*] --> Inactive

    state Inactive {
        [*] --> choose
        state choose <<choice>>
        choose --> Active: mode = On or (mode = Auto and signal = 1)
        choose --> Inactive: mode = Off or (mode = Auto and signal = 0)
    }

    state Active {
        [*] --> choose2
        state choose2 <<choice>>
        choose2 --> Inactive: mode = Off or (mode = Auto and signal = 0)
        choose2 --> Active: mode = On or (mode = Auto and signal = 1)
    }

    Inactive --> Active
    Active --> Inactive
```

## Curtailment and remuneration calculation

```mermaid
flowchart LR
    A["3ERL API<br/>curtailment signal = 1"] --> B["Injection power sensor<br/>W"]
    B --> C["Energy delta<br/>kWh"]
    D["Dernier PRE+<br/>EUR/MWh"] --> E["Remuneration rate<br/>70% of PRE+"]
    C --> F["Estimated gain<br/>EUR"]
    E --> F
    F --> G["Cumulative counters<br/>persisted in Store"]
```

## Operational workflow

1. The user installs the integration via HACS or manual copy, then configures it through the Home Assistant UI.
2. The coordinator fetches the 3ERL API at the configured interval.
3. Each time the configured injection power sensor changes, the coordinator computes the energy curtailed since the last update.
4. The controller listens to coordinator updates and mode-select changes, then decides whether to turn the relay on or off.
5. While curtailment is active, the coordinator accumulates the estimated gain using the latest PRE+ value and the 70% remuneration rule.
6. Cumulative energy and gain counters are saved to Home Assistant storage and restored on restart.

## Maintenance workflow

- To reset counters, call the service `zero_inject_3erl.reset_counters` from **Developer Tools → Services**.
- To change the relay, PV sensor, contract type or polling interval, use **Settings → Devices & services → 3ERL Zero-Injection → Configure**.
