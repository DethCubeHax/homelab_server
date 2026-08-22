# Homelab Server Stack

Self-hosted media, photos, cloud storage, chat, and monitoring — all orchestrated with Docker Compose. Public HTTPS access goes through **Cloudflare Tunnel → Caddy → services**

## Services

| Category | Services |
|----------|----------|
| Media acquisition | Prowlarr, qBittorrent, Sonarr, Radarr, Lidarr, YouTubeDL-Material, Beets |
| Media serving | Jellyfin (video), Navidrome (music) |
| Photos | Immich |
| Cloud & office | Nextcloud (+ built-in Collabora office) |
| Chat & calls | Matrix (Synapse), Element, Cloudflare TURN, LiveKit |
| Monitoring | Grafana, Prometheus, Loki, Alloy, cAdvisor, node_exporter |
| Reverse proxy | Caddy, Cloudflare Tunnel |

---

## Prerequisites

- Linux host with Docker and Docker Compose v2
- Enough disk for media, photos, and Nextcloud data
- A domain on Cloudflare (for tunnel + public hostnames)
- Intel iGPU with `/dev/dri/renderD128` if you want Jellyfin hardware transcoding (optional)

---

## Initial setup

### 1. Clone and configure environment

```bash
git clone https://github.com/DethCubeHax/homelab_server.git
cd homelab_server
cp env.example .env
nano .env
```

Set **`PUID`**, **`PGID`**, and **`TZ`** first. Find your IDs with `id`

Generate strong passwords where noted:

```bash
openssl rand -hex 24   # DB passwords
openssl rand -hex 12   # LIVEKIT_API_KEY
openssl rand -hex 32   # LIVEKIT_API_SECRET
```

Create config and data directories for every path in `.env` before starting services

### 2. Customize domains (if not using the defaults)

The included `matrix/caddy/Caddyfile` uses `*.example.com` hostnames. Replace `example.com` with your own domain in:

- `matrix/caddy/Caddyfile`
- `matrix/element/config.json`
- `env.example` / `.env` (`NEXTCLOUD_DOMAIN`, `IMMICH_SERVER_URL`, `MATRIX_SERVER_NAME`, etc.)
- Grafana `GF_SERVER_ROOT_URL` in `docker-compose.yml` (or override via env)

### 3. Start everything

```bash
docker compose up -d
```

Or start groups individually (see each section below)

---

## Cloudflare Tunnel & Caddy

These two services expose everything over HTTPS without opening ports on your router

### Cloudflare Tunnel

1. Cloudflare Zero Trust → **Networks → Tunnels** → create a tunnel
2. Copy the tunnel token into `.env` as `CLOUDFLARE_TUNNEL_TOKEN`
3. Add **Public Hostnames** pointing to **`http://caddy:80`** for each subdomain you use

| Public hostname | Caddy route (see Caddyfile) |
|-----------------|----------------------------|
| `cloud.yourdomain.com` | Nextcloud |
| `photos.yourdomain.com` | Immich |
| `jellyfin.yourdomain.com` | Jellyfin |
| `music.yourdomain.com` | Navidrome |
| `matrix.yourdomain.com` | Synapse + LiveKit |
| `chat.yourdomain.com` | Element |
| `grafana.yourdomain.com` | Grafana |
| `sonarr.yourdomain.com` | Sonarr |
| `radarr.yourdomain.com` | Radarr |
| `lidarr.yourdomain.com` | Lidarr |
| `yourdomain.com` | Matrix `.well-known` (optional) |

4. Start the tunnel:

```bash
docker compose up -d caddy cloudflared
```

Caddy must be running before the tunnel connects

---

## Media acquisition

### Prowlarr

Indexer manager for the *arr stack

**`.env`:** `PROWLARR_CONFIG_DIR`

```bash
docker compose up -d prowlarr
```

**Setup:** Open `http://localhost:9696` → add indexers → in each *arr app, add Prowlarr as an indexer (Settings → Apps in Prowlarr gives you the URLs/API keys)

---

### qBittorrent

Torrent client used by Sonarr/Radarr/Lidarr

**`.env`:** `QBITTORRENT_CONFIG_DIR`, `DOWNLOADS_DIR`

```bash
docker compose up -d qbittorrent
```

**Setup:** Open `http://localhost:8080` → default login is often `admin` / `adminadmin` (check container logs) → change password → set download path to `/downloads` → in each *arr app, add qBittorrent under **Settings → Download Clients**

---

### Sonarr

TV show automation

**`.env`:** `SONARR_CONFIG_DIR`, `SONARR_TV_DIR`, `DOWNLOADS_DIR`

```bash
docker compose up -d sonarr
```

**Setup:** `http://localhost:8989` → connect Prowlarr + qBittorrent → add root folder `/tv` → add series

---

### Radarr

Movie automation

**`.env`:** `RADARR_CONFIG_DIR`, `RADARR_MOVIES_DIR`, `DOWNLOADS_DIR`

```bash
docker compose up -d radarr
```

**Setup:** `http://localhost:7878` → connect Prowlarr + qBittorrent → add root folder `/movies`

---

### Lidarr

Music automation

**`.env`:** `LIDARR_CONFIG_DIR`, `LIDARR_MUSIC_DIR`, `DOWNLOADS_DIR`

```bash
docker compose up -d lidarr
```

**Setup:** `http://localhost:8686` → connect Prowlarr + qBittorrent → add root folder `/music`

---

### YouTubeDL-Material

Download YouTube/audio for your music library

**`.env`:** `YTDL_CONFIG_DIR`, `YTDL_DOWNLOADS_DIR`

```bash
docker compose up -d ytdl-material
```

**Setup:** `http://localhost:8998` → complete the web wizard → point output to `/app/audio`

---

### Beets

Music library tagger/organizer (CLI-focused; runs alongside Lidarr)

**`.env`:** `BEETS_CONFIG_DIR`, `LIDARR_MUSIC_DIR`, `DOWNLOADS_DIR`

```bash
docker compose up -d beets
```

**Setup:** Exec into the container and run `beet` commands, or configure `config.yaml` in your beets config dir. Shares the same music folder as Lidarr/Navidrome

---

## Media serving

### Jellyfin

Video streaming with optional Intel Quick Sync transcoding

**`.env`:** `JELLYFIN_CONFIG_DIR`, `JELLYFIN_TV_DIR`, `JELLYFIN_MOVIES_DIR`, `JELLYFIN_CACHE_DIR`

Uses **`network_mode: host`** — it listens on port **8096** on the host (Caddy proxies via `host.docker.internal:8096`)

```bash
docker compose up -d jellyfin
```

**Setup:**

1. Open `http://localhost:8096` and create an admin account
2. **Dashboard → Libraries** → add `/media/Movies` and `/media/Anime` (map to your movie/TV paths)
3. For hardware transcoding: **Dashboard → Playback → Transcoding** → enable hardware acceleration (QSV/VAAPI). Requires `/dev/dri/renderD128` on the host

**Public URL:** `https://jellyfin.yourdomain.com` (via tunnel)

---

### Navidrome

Lightweight music streaming server

**`.env`:** `NAVIDROME_CONFIG_DIR`, `NAVIDROME_MUSIC_DIR`

```bash
docker compose up -d navidrome
```

**Setup:** Open `http://localhost:4533` → first user becomes admin → music is read from `/music` (same library as Lidarr)

**Public URL:** `https://music.yourdomain.com`

---

## Photos — Immich

Self-hosted Google Photos alternative

**`.env`:** `IMMICH_UPLOAD_LOCATION`, `IMMICH_DB_DATA_LOCATION`, `IMMICH_MODEL_CACHE_DIR`, `DB_USERNAME`, `DB_PASSWORD`, `IMMICH_SERVER_URL`

Set `IMMICH_SERVER_URL` to your public URL (e.g. `https://photos.yourdomain.com`) when using the tunnel

```bash
docker compose up -d immich-server immich-microservices immich-machine-learning redis database
```

**Setup:** Open `http://localhost:2283` or your public URL → create admin account → install mobile apps and point them at your server URL

**Public URL:** `https://photos.yourdomain.com`

---

## Cloud & office — Nextcloud

Files, sync, and document editing via built-in Collabora CODE

**`.env`:** `NEXTCLOUD_DOMAIN`, `NEXTCLOUD_ADMIN_USER`, `NEXTCLOUD_ADMIN_PASSWORD`, `NEXTCLOUD_DB_PASSWORD`, `NEXTCLOUD_HTML_DIR`, `NEXTCLOUD_DATA_DIR`, `NEXTCLOUD_DB_DATA_LOCATION`

```bash
mkdir -p "${NEXTCLOUD_HTML_DIR%/*}"/{html,postgres} "${NEXTCLOUD_DATA_DIR}"
docker compose up -d nextcloud-db nextcloud-redis nextcloud
docker compose restart caddy
```

**Setup:**

1. Visit `https://cloud.yourdomain.com` and log in with your admin credentials
2. **Apps** → enable **Nextcloud Office** and **Built-in CODE Server**
3. If office does not connect automatically:

```bash
docker exec -u www-data nextcloud php occ richdocuments:activate-config
```

See [nextcloud/README.md](nextcloud/README.md) for more detail

---

## Chat & calls — Matrix

Synapse homeserver, Element web client, Cloudflare TURN for legacy VoIP, and LiveKit for Element X video calls

### Synapse (first-time install)

**`.env`:** `SYNAPSE_CONFIG_DIR`, `SYNAPSE_DB_DATA_LOCATION`, `SYNAPSE_DB_PASSWORD`, `MATRIX_SERVER_NAME`

```bash
# Generate homeserver.yaml (once)
docker run -it --rm \
  -v "${SYNAPSE_CONFIG_DIR}:/data" \
  -e SYNAPSE_SERVER_NAME=yourdomain.com \
  -e SYNAPSE_REPORT_STATS=no \
  matrixdotorg/synapse:latest generate

# Edit homeserver.yaml — set database password to match SYNAPSE_DB_PASSWORD
nano "${SYNAPSE_CONFIG_DIR}/homeserver.yaml"

docker compose up -d synapse-db synapse
```

Register your first user:

```bash
docker exec -it synapse register_new_matrix_user \
  -c /data/homeserver.yaml http://localhost:8008
```

### Element

**Config:** `matrix/element/config.json` — set `base_url` and `server_name`

```bash
docker compose up -d element
```

**Public URL:** `https://chat.yourdomain.com`

### Cloudflare TURN (turnify)

Needed for Matrix 1:1 VoIP when UDP is blocked

**`.env`:** `CF_TURN_TOKEN_ID`, `CF_TURN_API_TOKEN`

Create a TURN key: Cloudflare Dashboard → **Realtime → TURN → Create**

```bash
docker compose up -d turnify
```

### LiveKit + Element X calls

**`.env`:** `LIVEKIT_API_KEY`, `LIVEKIT_API_SECRET`, `MATRIX_SERVER_NAME`

```bash
cp matrix/livekit/livekit.yaml.example matrix/livekit/livekit.yaml
# Edit livekit.yaml — set keys to match .env

mkdir -p matrix/livekit/certs
openssl req -x509 -newkey rsa:2048 -nodes \
  -keyout matrix/livekit/certs/tls.key \
  -out matrix/livekit/certs/tls.crt \
  -days 3650 -subj "/CN=matrix.yourdomain.com"

docker compose up -d livekit lk-jwt-service
docker compose restart caddy
```

After deploy, Element X users may need to clear app cache and re-login so `.well-known` picks up the LiveKit backend

Full details: [matrix/MATRIX_RTC_SETUP.md](matrix/MATRIX_RTC_SETUP.md)

**Public URLs:**

- Homeserver: `https://matrix.yourdomain.com`
- Element: `https://chat.yourdomain.com`

---

## Monitoring

Grafana dashboards, Prometheus metrics, Loki logs (including SSH auth and *arr logs via Alloy)

**`.env`:** `MONITORING_DIR`, `MONITORING_PASSWORD`, `MONITORING_ADMIN_EMAIL`

```bash
mkdir -p "${MONITORING_DIR}"/{grafana,prometheus,loki,alloy,logs}
docker compose up -d prometheus loki grafana alloy node_exporter cadvisor intel-gpu-exporter
docker compose restart caddy
```

**Setup:**

1. Open `http://localhost:3000` or `https://grafana.yourdomain.com`
2. Log in with username from `MONITORING_ADMIN_EMAIL` and `MONITORING_PASSWORD`
3. Pre-provisioned dashboards load automatically from `monitoring/grafana/provisioning/`

After changing `MONITORING_PASSWORD`:

```bash
./monitoring/scripts/update-monitoring-auth.sh
```

### Email alerts (optional)

Grafana sends mail via Postfix on the host. Configure Cloudflare Email Sending:

```bash
sudo ./scripts/setup-cloudflare-email.sh YOUR_CLOUDFLARE_API_TOKEN alert@yourdomain.com
```

Update the alert recipient in `monitoring/grafana/provisioning/alerting/contact-points.yml`

---

## Local ports reference

| Service | Port |
|---------|------|
| qBittorrent | 8080 |
| Sonarr | 8989 |
| Radarr | 7878 |
| Lidarr | 8686 |
| Prowlarr | 9696 |
| YouTubeDL-Material | 8998 |
| Navidrome | 4533 |
| Immich | 2283 |
| Grafana | 3000 |
| Jellyfin | 8096 (host network) |
| cAdvisor | 8081 |

Most services are intended for HTTPS access via Cloudflare Tunnel rather than exposing these ports publicly

---

## Useful commands

```bash
# Status
docker compose ps

# Logs for a service
docker compose logs -f jellyfin

# Restart after .env changes
docker compose up -d

# Pull updates and recreate
docker compose pull && docker compose up -d
```
