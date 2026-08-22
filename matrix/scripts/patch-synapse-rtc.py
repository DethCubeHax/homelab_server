#!/usr/bin/env python3
"""Update Synapse homeserver.yaml for self-hosted MatrixRTC (LiveKit)."""
from pathlib import Path

import yaml

RTC_JWT_URL = "https://matrix.example.com/livekit/jwt"
path = Path("/data/homeserver.yaml")
config = yaml.safe_load(path.read_text())

config.setdefault("experimental_features", {})
config["experimental_features"].update(
    {
        "msc3266_enabled": True,
        "msc4222_enabled": True,
        "msc4143_enabled": True,
        "msc4140_enabled": True,
    }
)

config["max_event_delay_duration"] = "24h"
config["rc_message"] = {"per_second": 0.5, "burst_count": 30}
config["rc_delayed_event_mgmt"] = {"per_second": 1, "burst_count": 20}

config["matrix_rtc"] = {
    "transports": [
        {
            "type": "livekit",
            "livekit_service_url": RTC_JWT_URL,
        }
    ]
}

config["extra_well_known_client_content"] = {
    "org.matrix.msc4143.rtc_foci": [
        {
            "type": "livekit",
            "livekit_service_url": RTC_JWT_URL,
        }
    ]
}

path.write_text(yaml.dump(config, default_flow_style=False, sort_keys=False))
print(f"Patched {path} for MatrixRTC at {RTC_JWT_URL}")
