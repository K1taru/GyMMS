Cloudflare Tunnel, Domain gymms.space, and Docker Configuration Documentation

1. Cloudflare Tunnel Overview

Cloudflare Tunnel (cloudflared) provides a secure method to expose services running on a private device, such as a Raspberry Pi 5, to the public internet without opening ports on the router. It works by creating an encrypted outbound connection from the Raspberry Pi to Cloudflare. Traffic sent to the domain gymms.space is routed through Cloudflare and forwarded to the Raspberry Pi.

This tunnel does not require port forwarding, and since SSH is enabled, the Raspberry Pi remains accessible within the LAN. The application is served on http://localhost:8000 and is also reachable via LAN IP, such as http://192.168.x.x:8000.

2. Domain gymms.space Configuration

The domain gymms.space is managed under Cloudflare DNS. A Cloudflare Tunnel is created and linked to this domain. Public hostnames are assigned to forward incoming traffic to local services.

Example Cloudflare configuration file (/etc/cloudflared/config.yml):

tunnel: gymms-tunnel
credentials-file: /etc/cloudflared/gymms-tunnel.json

ingress:
  - hostname: gymms.space
    service: http://localhost:8000
  - hostname: admin.gymms.space
    service: http://localhost:8000/admin
  - service: http_status:404

This configuration instructs Cloudflare to forward requests to the Django application running on port 8000.

To enable the tunnel at boot:

sudo systemctl enable cloudflared
sudo systemctl start cloudflared

To check the status:

systemctl status cloudflared

3. Docker and Docker Compose Service

The Django application, including its dependencies (database, backend services), runs inside Docker containers using docker-compose. The application listens at http://localhost:8000 internally, which Cloudflare Tunnel forwards externally.

4. Systemd Service for Automatic Docker Startup

The systemd service ensures docker-compose starts automatically during boot.

Example file: /etc/systemd/system/gymms_docker.service

[Unit]
Description=GyMMS Django Docker Compose Service
After=network-online.target docker.service
Requires=docker.service

[Service]
Type=oneshot
WorkingDirectory=/home/k1taru/gymms
ExecStart=/usr/bin/docker compose up --build -d
ExecStop=/usr/bin/docker compose down
RemainAfterExit=yes
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target

Enable and start the service:

sudo systemctl daemon-reload
sudo systemctl enable gymms_docker.service
sudo systemctl start gymms_docker.service

Check status:

systemctl status gymms_docker.service

Check logs:

journalctl -u gymms_docker.service -n 50 --no-pager

5. How All Components Work Together

Boot sequence of the Raspberry Pi:

1. systemd launches the gymms_docker.service, which starts all Docker containers in detached mode.
2. cloudflared.service starts and establishes a secure tunnel to Cloudflare.
3. Cloudflare routes traffic from gymms.space to the Raspberry Pi on localhost:8000.
4. Local LAN users may also access the application directly via http://192.168.x.x:8000.

6. Testing Auto-Start Behavior

To test:

systemctl status gymms_docker.service
systemctl status cloudflared

To reboot and test automatically:

sudo reboot

After reboot:

docker ps
systemctl status cloudflared
systemctl status gymms_docker.service

