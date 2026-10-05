"""Constants for the 3ERL Zero-Injection integration."""

from __future__ import annotations

from datetime import timedelta

DOMAIN = "zero_inject_3erl"

DEFAULT_API_URL = "https://3erl.fr/api.json"
DEFAULT_UPDATE_INTERVAL_MINUTES = 15
DEFAULT_ZERO_INJECT_MODE = "Auto"

DEFAULT_RTE_PRICE_API_URL = "https://www.services-rte.com/cms/open_data/v1/price/table"
DEFAULT_ENEDIS_PRD3_API_URL = "https://openservices.enedis.fr/php/opendata.php"
DEFAULT_PRD3_DAY_OFFSET = -2
DEFAULT_PRD3_PROFILE = "PRD3_BASE"

CONF_API_URL = "api_url"
CONF_UPDATE_INTERVAL = "update_interval"
CONF_PV_SYSTEM_TYPE = "pv_system_type"
CONF_PV_POWER_ENTITY = "pv_power_entity"
CONF_RELAY_ENTITY = "relay_entity"
CONF_NOTIFY_SERVICE = "notify_service"
CONF_AGGREGATION_MODE = "aggregation_mode"
CONF_PRD3_DAY_OFFSET = "prd3_day_offset"

PV_SYSTEM_ENPHASE = "enphase"
PV_SYSTEM_GENERIC = "generic"
PV_SYSTEM_TYPES = [PV_SYSTEM_ENPHASE, PV_SYSTEM_GENERIC]

# Self-consumption contract types. ACI (individual) uses the `Bridage` API
# signal; ACC (collective) uses `Bridage_CDC`.
AGGREGATION_MODE_ACI = "aci"
AGGREGATION_MODE_ACC = "acc"
AGGREGATION_MODES = [AGGREGATION_MODE_ACI, AGGREGATION_MODE_ACC]
DEFAULT_AGGREGATION_MODE = AGGREGATION_MODE_ACI

ZERO_INJECT_MODES = ["Auto", "On", "Off"]

# 3ERL remuneration: 70% of the positive imbalance settlement price (PRE+).
REMUNERATION_RATE = 0.7

# Utility constants used for power/energy conversions.
SECONDS_PER_HOUR = 3600
WATTS_PER_KILOWATT = 1000
MEGAWATT_HOURS_PER_KILOWATT_HOUR = 1000

# Default request timeout for the 3ERL public API.
API_TIMEOUT_SECONDS = 30

# Minimum interval between two production-power based energy updates.
POWER_UPDATE_INTERVAL = timedelta(seconds=10)

# Storage key for cumulative energy and gain values.
STORAGE_KEY = f"{DOMAIN}.cumulative"

# Service identifiers.
SERVICE_RESET_COUNTERS = "reset_counters"

SENSOR_KEY_BRIDAGE = "Bridage"
SENSOR_KEY_BRIDAGE_CDC = "Bridage_CDC"
SENSOR_KEY_DERNIER_PREP = "Dernier_PREP"
SENSOR_KEY_PRD4 = "PRD4"
SENSOR_KEY_PREP_PROFILE = "PREP_Profile"
SENSOR_KEY_HEURE_UPDATE = "Heure_Update"
SENSOR_KEY_BRIDAGE_LONG_TERME = "Bridage_Long_Terme"
SENSOR_KEY_COMMENTAIRES = "Commentaires"
SENSOR_KEY_MODE_DEGRADE = "mode_degrade"
SENSOR_KEY_RTE_INDISPO_DEPUIS = "rte_indispo_depuis"
