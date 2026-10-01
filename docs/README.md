# Documentation

This documentation follows the [Diátaxis](https://diataxis.fr/) structure. Pick the page that matches what you need right now.

```mermaid
flowchart TD
    START(["I want to..."]) --> Q1{"Understand what this<br/>project does and why?"}
    Q1 -->|yes| EXPL["explanation/concepts.md<br/>3ERL, curtailment, ACI vs ACC, DRM"]
    START --> Q2{"Set up the system<br/>from scratch?"}
    Q2 -->|yes| FLOW["Follow the order below"]
    FLOW --> H1["1. how-to/configure-envoy-drm.md<br/>Installer access and relay levels"]
    FLOW --> H2["2. how-to/wire-the-relay.md<br/>Connect the dry-contact relay"]
    FLOW --> H3["3. how-to/install-and-configure.md<br/>Install and set up the integration"]
    FLOW --> H4["4. how-to/build-a-dashboard.md<br/>Optional Lovelace cards"]
    START --> Q3{"Look up exact field,<br/>entity or service names?"}
    Q3 -->|yes| REF["reference/"]
    START --> Q4{"Fix something<br/>that does not work?"}
    Q4 -->|yes| TS["troubleshooting.md"]
```

| I need to... | Go to |
|---|---|
| Understand 3ERL, curtailment, ACI vs ACC and how the relay stops export | [explanation/concepts.md](explanation/concepts.md) |
| Get Installer access on Enphase and configure the DRM relay levels | [how-to/configure-envoy-drm.md](how-to/configure-envoy-drm.md) |
| Wire a dry-contact relay to the Envoy DRM port | [how-to/wire-the-relay.md](how-to/wire-the-relay.md) |
| Install and configure the integration in Home Assistant | [how-to/install-and-configure.md](how-to/install-and-configure.md) |
| Add dashboard cards | [how-to/build-a-dashboard.md](how-to/build-a-dashboard.md) |
| Look up configuration fields | [reference/configuration-options.md](reference/configuration-options.md) |
| Look up the created entities | [reference/entities.md](reference/entities.md) |
| Look up the 3ERL API fields | [reference/api-fields.md](reference/api-fields.md) |
| Look up the exposed services | [reference/services.md](reference/services.md) |
| Diagnose a problem | [troubleshooting.md](troubleshooting.md) |
| Understand the internal architecture | [../WORKFLOW.md](../WORKFLOW.md) |
