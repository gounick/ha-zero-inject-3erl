from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import entity_registry as er

from .const import DOMAIN

CONTRACT_ENTITIES = {
    ("binary_sensor", "Bridage"): "aci",
    ("binary_sensor", "Bridage_CDC"): "acc",
    ("sensor", "current_prep"): "acc",
    ("sensor", "estimated_daily_prep"): "aci",
    ("sensor", "PREP_Profile_Num"): "aci",
}


@callback
def sync_contract_visibility(hass: HomeAssistant, entry: ConfigEntry, contract: str) -> None:
    registry = er.async_get(hass)
    managed_ids = set()
    for (domain, key), expected in CONTRACT_ENTITIES.items():
        entity_id = registry.async_get_entity_id(domain, DOMAIN, f"{DOMAIN}_{entry.entry_id}_{key}")
        if entity_id is None:
            continue
        item = registry.async_get(entity_id)
        policy = item.options.get(DOMAIN, {})
        if item.hidden_by is er.RegistryEntryHider.USER:
            registry.async_update_entity_options(entity_id, DOMAIN, {"visibility_override": True})
            continue
        if policy.get("visibility_override"):
            continue
        if "contract_hidden" in policy and bool(item.hidden_by) != policy["contract_hidden"]:
            registry.async_update_entity_options(entity_id, DOMAIN, {"visibility_override": True})
            continue
        hidden = contract != expected
        registry.async_update_entity_options(entity_id, DOMAIN, {"contract_hidden": hidden})
        registry.async_update_entity(
            entity_id, hidden_by=er.RegistryEntryHider.INTEGRATION if hidden else None
        )
        managed_ids.add(entity_id)

    @callback
    def remember_override(event) -> None:
        if event.data.get("action") != "update" or "hidden_by" not in event.data.get("changes", {}):
            return
        entity_id = event.data["entity_id"]
        if entity_id not in managed_ids or (item := registry.async_get(entity_id)) is None:
            return
        policy = item.options.get(DOMAIN, {})
        if bool(item.hidden_by) != policy.get("contract_hidden"):
            registry.async_update_entity_options(entity_id, DOMAIN, {"visibility_override": True})

    entry.async_on_unload(
        hass.bus.async_listen(er.EVENT_ENTITY_REGISTRY_UPDATED, remember_override)
    )
