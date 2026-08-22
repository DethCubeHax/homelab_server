# Nextcloud

Self-hosted files and office at **https://cloud.example.com**

Document editing uses **Nextcloud Office** with the built-in Collabora CODE server (`richdocumentscode` app)

## Before first start

1. Copy and edit environment:

   ```bash
   cp env.example .env
   nano .env
   ```

2. Set at minimum:

   | Variable | What to set |
   |----------|-------------|
   | `NEXTCLOUD_ADMIN_USER` | Admin username |
   | `NEXTCLOUD_ADMIN_PASSWORD` | Strong admin password |
   | `NEXTCLOUD_DB_PASSWORD` | PostgreSQL password |

3. Create data directories (once):

   ```bash
   mkdir -p /mnt/Data/Plex_Config/nextcloud/{html,postgres} \
            /mnt/Data/Cloud/nextcloud/data
   ```

## Cloudflare Tunnel DNS

Add on your existing tunnel (same as jellyfin/grafana):

| Public hostname | Service |
|-----------------|---------|
| `cloud.example.com` | `http://caddy:80` |

## Start

```bash
docker compose up -d nextcloud-db nextcloud-redis nextcloud
docker compose restart caddy
```

## Nextcloud Office (Collabora)

1. **Apps** → enable **Nextcloud Office** and **Built-in CODE Server**
2. **Administration settings → Office** — should auto-detect the built-in server
3. Run if needed:

   ```bash
   docker exec -u www-data nextcloud php occ richdocuments:activate-config
   ```

## Useful commands

```bash
docker exec -u www-data nextcloud php occ status
docker compose logs -f nextcloud
```
