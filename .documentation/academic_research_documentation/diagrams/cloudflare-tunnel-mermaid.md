```mermaid
graph TB
    subgraph Local["Local Network 192.168.x.x<br/>Raspberry Pi 5"]
        Django[Django/Gunicorn<br/>Port 8000]
        Postgres[(PostgreSQL<br/>Database)]
        Nginx[Nginx Reverse Proxy<br/>Port 80]
        Cloudflared[cloudflared daemon<br/>Outbound Connection Only]
        
        Cloudflared --> Nginx
        Nginx --> Django
        Django --> Postgres
    end
    
    subgraph Cloudflare["Cloudflare Edge Network<br/>300+ Global Locations"]
        DDoS[DDoS Shield]
        WAF[WAF Rules]
        CDN[CDN Cache]
        SSL[SSL/TLS<br/>Termination]
    end
    
    Users[End Users<br/>Browsers]
    Domain[gymms.domain.com<br/>HTTPS + TLS 1.3]
    
    Cloudflared -->|Outbound HTTPS<br/>Persistent Tunnel<br/>QUIC Protocol| Cloudflare
    Cloudflare -.->|Proxied Requests<br/>Through Tunnel| Cloudflared
    
    Users -->|HTTPS Request| Domain
    Domain --> Cloudflare
    
    style Local fill:#c8e6c9
    style Cloudflare fill:#bbdefb
    style Cloudflared fill:#ffcc80
    style Domain fill:#fff9c4
    
    classDef security fill:#ffcdd2
    class DDoS,WAF security
```

**Key Features to Highlight:**
- ✅ No port forwarding required
- ✅ No static IP needed
- ✅ Origin server IP hidden
- ✅ Automatic SSL certificates
- ✅ DDoS protection at edge
- ✅ Zero inbound firewall rules

**To Render:**
- Copy to GitHub markdown file
- Use https://mermaid.live/
- Or use VS Code Mermaid Preview extension
