# My Self-Hosted Media NAS Stack

This repository contains a `docker-compose.yml` setup for a comprehensive, self-hosted media and photo management server. It uses the popular "Arr" stack for media acquisition, Jellyfin and Navidrome for serving, and Immich for photo management

## Services Included

- **Prowlarr**: Indexer manager for Sonarr, Radarr, etc
- **qBittorrent**: Torrent client
- **Sonarr**: TV show automation
- **Radarr**: Movie automation
- **Lidarr**: Music automation
- **Jellyfin**: Media server for movies and TV shows
- **Navidrome**: Music server and streamer
- **Immich**: Self-hosted photo and video backup solution

## Getting Started

1.  **Clone the Repository**
    ```bash
    git clone [https://github.com/your-username/your-repo-name.git](https://github.com/your-username/your-repo-name.git)
    cd your-repo-name
    ```

2.  **Configure Your Environment**
    Copy the example environment file to create your own personal configuration
    ```bash
    cp env.example .env
    ```

3.  **Edit the `.env` file** (`nano .env`) and update all the paths and settings to match your system. Pay close attention to `PUID`, `PGID`, `TZ`, and all the directory paths

4.  **Start the Stack**
    Launch all the services using Docker Compose
    ```bash
    docker compose up -d
    ```

The services will now be running and accessible at their respective ports on your server's IP address
