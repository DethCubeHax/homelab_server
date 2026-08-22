# MatrixRTC (Element X video calls)

Self-hosted LiveKit + lk-jwt-service for Element X / Element Web calls

## What was added

| Service | Role |
|---------|------|
| `livekit` | WebRTC media server (SFU) + embedded TURN |
| `lk-jwt-service` | Issues LiveKit tokens for Matrix users |
| Caddy routes on `matrix.example.com` | `/livekit/jwt/*` and `/livekit/sfu/*` |

Call backend URL: **`https://matrix.example.com/livekit/jwt`**

## After deploy — required client step

Element X caches `.well-known` on first login. After this change, each phone must:

1. **Settings → Apps → Element X → Clear cache** (Android)
2. Log out and log back in

Or calls may still point at the old matrix.org backend

## Update Cloudflare Worker

If you use the worker for `example.com/.well-known/matrix/client`, redeploy
`matrix/well-known/cloudflare-worker.js` so `livekit_service_url` is:

```json
"https://matrix.example.com/livekit/jwt"
```

(`matrix.example.com/.well-known` is already served by Synapse with the same URL.)

## Optional: TURN over TCP (no UDP port forward)

LiveKit embeds TURN on **TCP 5349** (TLS). For calls over mobile data when UDP
to your home IP is blocked, add a **TCP** public hostname in Cloudflare Zero Trust:

1. **Networks → Connectors → your tunnel → Public Hostname → Add**
2. **Subdomain:** `matrix` (or use a dedicated `turn` subdomain)
3. **Service type:** TCP
4. **URL:** `livekit:5349` (docker service name on `media_net`)

Clients will use `turns:matrix.example.com:5349` via Cloudflare’s edge

The bundled cert is self-signed for `matrix.example.com`. For best mobile
compatibility, replace `matrix/livekit/certs/tls.crt` and `tls.key` with a
Cloudflare Origin Certificate or other trusted cert for that hostname

## Verify

```bash
curl -s https://matrix.example.com/livekit/jwt/healthz
# expect: OK

curl -s https://matrix.example.com/.well-known/matrix/client | jq .org.matrix.msc4143
# expect livekit_service_url -> https://matrix.example.com/livekit/jwt

docker compose logs livekit lk-jwt-service --tail 20
```

## LiveKit keys

LiveKit API key/secret must match in both places:

1. Copy the example config (local `livekit.yaml` is gitignored):

   ```bash
   cp matrix/livekit/livekit.yaml.example matrix/livekit/livekit.yaml
   ```

2. Set the same values in `.env` as `LIVEKIT_API_KEY` / `LIVEKIT_API_SECRET`

3. Generate TURN TLS certs locally (certs/ is gitignored):

   ```bash
   mkdir -p matrix/livekit/certs
   openssl req -x509 -newkey rsa:2048 -nodes \
     -keyout matrix/livekit/certs/tls.key \
     -out matrix/livekit/certs/tls.crt \
     -days 3650 -subj "/CN=matrix.example.com"
   ```

Keep `.env` and `livekit.yaml` in sync if you rotate keys
