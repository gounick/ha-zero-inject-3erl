# 3ERL Zero-Injection Workflow

This document describes the architecture, data flow and operational workflow of the 3ERL Zero-Injection integration.

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
    PV_POWER["PV Production Power Sensor"]

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
    CF->>U: Ask for API URL, interval, PV power sensor, relay, notify service
    U->>CF: Submit configuration
    CF->>API: GET /api.json
    API-->>CF: JSON response
    CF->>HA: Create config entry
    HA->>HA: Setup coordinator, controller and entities
```

## Zero-injection state machine

```mermaid
stateDiagram-v2
    [*] --> Auto
    Auto --> Active: Bridage = 1
    Active --> Inactive: Bridage = 0
    Auto --> Active: Mode = On
    Auto --> Inactive: Mode = Off
    Active --> Inactive: Mode = Off
    Inactive --> Active: Mode = On
    On --> Auto: User selects Auto
    Off --> Auto: User selects Auto
```

## Curtailment and remuneration calculation

```mermaid
flowchart LR
    A["3ERL API<br/>Bridage = 1"] --> B["PV power sensor<br/>W"]
    B --> C["Energy delta<br/>kWh"]
    D["Dernier PRE+<br/>EUR/MWh"] --> E["Remuneration rate<br/>70% of PRE+"]
    C --> F["Estimated gain<br/>EUR"]
    E --> F
    F --> G["Cumulative counters<br/>persisted in Store"]
```

## Operational workflow

1. **Initial setup**: User installs the integration via HACS or manual copy, then configures it through the Home Assistant UI.
2. **API polling**: The coordinator fetches the 3ERL API at the configured interval.
3. **Power tracking**: Each time the configured PV production power sensor changes, the coordinator computes the energy curtailed since the last update.
4. **Decision**: The controller listens to coordinator updates and mode-select changes, then decides whether to turn the relay on or off.
5. **Remuneration**: While curtailment is active, the coordinator accumulates the estimated gain using the latest PRE+ value and the 70% remuneration rule.
6. **Persistence**: Cumulative energy and gain counters are saved to Home Assistant storage and restored on restart.

## Maintenance workflow

- To reset counters, call the service `zero_inject_3erl.reset_counters` from **Developer Tools → Services**.
- To change the relay, PV sensor or polling interval, use **Settings → Devices & services → 3ERL Zero-Injection → Configure**.
