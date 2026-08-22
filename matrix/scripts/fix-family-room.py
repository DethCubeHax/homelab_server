#!/usr/bin/env python3
"""Fix call permissions and clear stuck call/widget state in a Matrix room.

Requires env vars:
  MATRIX_FIX_USER       Matrix localpart (e.g. admin)
  MATRIX_FIX_PASSWORD   Account password
  MATRIX_FIX_ROOM_ID    Room ID (e.g. !abc:example.com)

Optional:
  MATRIX_BASE_URL       Synapse URL (default: http://synapse:8008)
"""
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

BASE = os.environ.get("MATRIX_BASE_URL", "http://synapse:8008")


def require_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        print(f"Missing {name}. Export it or pass -e to docker exec.", file=sys.stderr)
        sys.exit(1)
    return value


def api(method, path, token=None, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(
        f"{BASE}{path}",
        data=data,
        method=method,
        headers={
            "Content-Type": "application/json",
            **({"Authorization": f"Bearer {token}"} if token else {}),
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        raw = resp.read()
        return json.loads(raw) if raw else {}


def put_state(token, room_id, event_type, state_key, content):
    enc_key = urllib.parse.quote(state_key, safe="")
    api(
        "PUT",
        f"/_matrix/client/v3/rooms/{room_id}/state/{event_type}/{enc_key}",
        token,
        content,
    )


def main():
    user = require_env("MATRIX_FIX_USER")
    password = require_env("MATRIX_FIX_PASSWORD")
    room_id = require_env("MATRIX_FIX_ROOM_ID")

    login = api(
        "POST",
        "/_matrix/client/v3/login",
        body={
            "type": "m.login.password",
            "identifier": {"type": "m.id.user", "user": user},
            "password": password,
            "device_id": "ROOMFIXSCRIPT",
        },
    )
    token = login["access_token"]
    print(f"Logged in as {login['user_id']}")

    pl = api("GET", f"/_matrix/client/v3/rooms/{room_id}/state/m.room.power_levels", token)
    pl.setdefault("users_default", 0)
    pl.setdefault("events_default", 0)
    pl.setdefault("state_default", 50)
    pl.setdefault("ban", 50)
    pl.setdefault("kick", 50)
    pl.setdefault("redact", 50)
    pl.setdefault("invite", 0)
    pl.setdefault("historical", 100)
    pl.setdefault("events", {})
    pl.setdefault("users", {})

    pl["events"]["org.matrix.msc3401.call"] = 0
    pl["events"]["org.matrix.msc3401.call.member"] = 0
    pl["events"]["im.vector.modular.widgets"] = 50
    pl["users"] = {login["user_id"]: 100}

    api("PUT", f"/_matrix/client/v3/rooms/{room_id}/state/m.room.power_levels", token, pl)
    print("Updated power levels: call.member=0, other users back to default level")

    state = api("GET", f"/_matrix/client/v3/rooms/{room_id}/state", token)

    for event in state:
        etype = event.get("type", "")
        skey = event.get("state_key", "")
        content = event.get("content") or {}

        if etype == "org.matrix.msc3401.call.member" and content:
            put_state(token, room_id, etype, skey, {})
            print(f"  Cleared active call: {skey}")

        if etype == "im.vector.modular.widgets" and content:
            put_state(token, room_id, etype, skey, {})
            print(f"  Removed widget: {skey}")

    for skey in (
        "_@dethcube:example.com_JTFQWNLBBY_m.call",
        "_@naznin:example.com_XPBZBZBCVP_m.call",
    ):
        try:
            put_state(token, room_id, "org.matrix.msc3401.call.member", skey, {})
            print(f"  Reset call state: {skey}")
        except urllib.error.HTTPError as e:
            if e.code != 403:
                print(f"  call {skey}: HTTP {e.code}")

    for skey in (
        "XOm5SMEQpO5c7IX3zuYWJo4F",
        "7A9Csu15s5QZFSbJ19LLoLMk",
        "4eZ6rEbRlYbBjpHzOmKjOQjX",
        "m.jitsi_@nizam:example.com_1783348662219",
    ):
        try:
            put_state(token, room_id, "im.vector.modular.widgets", skey, {})
            print(f"  Reset widget: {skey}")
        except urllib.error.HTTPError as e:
            if e.code != 403:
                print(f"  widget {skey}: HTTP {e.code}")

    pl2 = api("GET", f"/_matrix/client/v3/rooms/{room_id}/state/m.room.power_levels", token)
    print("Final call.member power level:", pl2["events"].get("org.matrix.msc3401.call.member"))
    print("Done.")


if __name__ == "__main__":
    main()
