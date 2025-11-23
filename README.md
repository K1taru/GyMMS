# GyMMS - Gym Membership Management System

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-5.0+-green.svg)](https://www.djangoproject.com/)
[![Docker](https://img.shields.io/badge/Docker-ready-blue.svg)](https://www.docker.com/)

A comprehensive web-based gym membership management system built with Django, deployed on Raspberry Pi 5, featuring automated payment processing, real-time analytics, and secure remote access via Cloudflare Tunnel.

---

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Technology Stack](#technology-stack)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Installation & Setup](#installation--setup)
- [Configuration](#configuration)
- [Usage](#usage)
- [Deployment](#deployment)
- [Project Structure](#project-structure)
- [Services & Integrations](#services--integrations)
- [Security](#security)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

---

## 🎯 Overview

### Problem Statement

Traditional gym membership management faces several critical challenges:

1. **Manual Tracking**: Time-consuming, error-prone paper-based record keeping
2. **Subscription Management**: No automated tracking of membership expiration dates
3. **Payment Limitations**: In-person only payments with no digital alternatives
4. **Data Accessibility**: Limited access to business insights and analytics
5. **Operational Inefficiency**: Staff spending excessive time on administrative tasks

### Solution

GyMMS addresses these challenges by providing a fully-featured, automated membership management system that:

- Eliminates manual record-keeping through comprehensive digital tracking
- Automates membership renewals and expiration notifications
- Provides secure remote access from any location
- Delivers real-time analytics and business intelligence
- Reduces administrative overhead by up to 80%

### Target Users

- **Gym Owners**: Full system access, financial reports, staff management
- **Gym Staff**: Member management, payment processing, attendance tracking
- **Members**: Profile management, payment history, attendance records

---

## ✨ Features

### 🏋️ Membership Management
- **Digital Member Profiles**: Comprehensive member information with photo upload
- **Membership Plans**: Flexible subscription tiers and pricing
- **Automated Status Tracking**: Real-time membership status updates (active, expired, expiring soon)
- **Quick Search**: Fast member lookup by name, ID, or phone number
- **Soft Delete**: Safe deletion preserving historical records

### 💰 Payment Processing
- **Transaction Recording**: Complete payment history with receipt generation
- **Automated Renewals**: Automatic membership extension upon payment
- **Multiple Payment Methods**: Cash, bank transfer, online payments support
- **Financial Reports**: Revenue tracking and payment analytics
- **Receipt Management**: PDF receipt generation and email delivery

### 📊 Analytics & Reporting
- **Real-Time Dashboard**: Live statistics on active members, revenue, check-ins
- **Revenue Analytics**: Daily, weekly, monthly revenue trends
- **Member Insights**: Growth trends, retention rates, demographics
- **Attendance Tracking**: Check-in/check-out monitoring with history
- **Custom Reports**: Exportable data for business analysis

### 🔒 Security & Access Control
- **Role-Based Access**: Owner (admin) and Staff roles with granular permissions
- **Secure Authentication**: Industry-standard password hashing (PBKDF2-SHA256)
- **Session Management**: Automatic timeout and secure session handling
- **Audit Logging**: Track sensitive operations for compliance
- **Data Privacy**: GDPR-aligned data protection practices

### 🚀 Deployment & Infrastructure
- **Edge Computing**: Runs on Raspberry Pi 5 (8GB RAM)
- **Containerized Deployment**: Docker and Docker Compose orchestration
- **Zero-Trust Access**: Cloudflare Tunnel for secure remote connectivity
- **Real-Time Monitoring**: Prometheus and Grafana integration
- **Automated Backups**: Daily PostgreSQL dumps with rotation

---

## 🛠️ Technology Stack

### Backend

<img src="https://www.djangoproject.com/m/img/logos/django-logo-negative.png" width="150" alt="Django"/>

- **Django 5.0+** - High-level Python web framework
- **Python 3.11+** - Core programming language
- **Gunicorn** - WSGI HTTP server for production

<img src="https://www.postgresql.org/media/img/about/press/elephant.png" width="100" alt="PostgreSQL"/>

- **PostgreSQL 16** - Robust relational database with advanced features
- **psycopg2** - PostgreSQL adapter for Python

### Frontend

<img src="https://getbootstrap.com/docs/5.0/assets/brand/bootstrap-logo.svg" width="100" alt="Bootstrap"/>

- **Bootstrap 5** - Responsive CSS framework
- **JavaScript (Vanilla)** - Dynamic UI interactions
- **Chart.js** - Data visualization and analytics charts
- **HTML5/CSS3** - Modern web standards

### Deployment & Infrastructure

<img src="https://www.docker.com/wp-content/uploads/2022/03/horizontal-logo-monochromatic-white.png" width="150" alt="Docker"/>

- **Docker** - Containerization platform
- **Docker Compose** - Multi-container orchestration

<img src="https://assets.raspberrypi.com/static/raspberry-pi-logo-46e0bd895c.png" width="100" alt="Raspberry Pi"/>

- **Raspberry Pi 5 (8GB)** - Edge computing hardware
- **Raspberry Pi OS (64-bit)** - Operating system

<img src="https://www.cloudflare.com/img/logo-cloudflare-dark.svg" width="150" alt="Cloudflare"/>

- **Cloudflare Tunnel** - Secure zero-trust remote access
- **WhiteNoise** - Efficient static file serving

### Monitoring & Analytics

<img src="https://prometheus.io/assets/prometheus_logo_grey.svg" width="100" alt="Prometheus"/>

- **Prometheus** - Metrics collection and monitoring

<img src="https://grafana.com/static/img/menu/grafana2.svg" width="100" alt="Grafana"/>

- **Grafana** - Data visualization and dashboards

---

## 🏗️ Architecture

### System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         Internet                             │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │  Cloudflare Tunnel   │
              │   (Zero-Trust CDN)   │
              └──────────┬───────────┘
                         │ HTTPS/WSS
                         ▼
         ┌───────────────────────────────────┐
         │      Raspberry Pi 5 (8GB)         │
         │  ┌─────────────────────────────┐  │
         │  │    Docker Environment       │  │
         │  │                             │  │
         │  │  ┌──────────────────────┐  │  │
         │  │  │   Django Web App     │  │  │
         │  │  │    (Gunicorn)        │  │  │
         │  │  └──────────┬───────────┘  │  │
         │  │             │               │  │
         │  │  ┌──────────▼───────────┐  │  │
         │  │  │   PostgreSQL 16      │  │  │
         │  │  │   (Database)         │  │  │
         │  │  └──────────────────────┘  │  │
         │  │                             │  │
         │  │  ┌──────────────────────┐  │  │
         │  │  │   Prometheus         │  │  │
         │  │  │   (Monitoring)       │  │  │
         │  │  └──────────┬───────────┘  │  │
         │  │             │               │  │
         │  │  ┌──────────▼───────────┐  │  │
         │  │  │   Grafana            │  │  │
         │  │  │   (Visualization)    │  │  │
         │  │  └──────────────────────┘  │  │
         │  │                             │  │
         │  └─────────────────────────────┘  │
         │                                    │
         │  ┌─────────────────────────────┐  │
         │  │   Persistent Storage        │  │
         │  │   - PostgreSQL Data         │  │
         │  │   - Media Files (Photos)    │  │
         │  │   - Backups (USB Drive)     │  │
         │  └─────────────────────────────┘  │
         └───────────────────────────────────┘
```

### Data Flow

1. **User Access**: Users access the system via web browser
2. **Cloudflare Edge**: Requests route through Cloudflare's zero-trust network
3. **Tunnel Connection**: Cloudflare Tunnel securely forwards to Raspberry Pi
4. **Django Processing**: Application processes requests, queries database
5. **Response Delivery**: Data returned through secure tunnel to user
6. **Monitoring**: Prometheus collects metrics, Grafana visualizes system health

---

## 📦 Prerequisites

### Hardware Requirements

- **Raspberry Pi 5** (8GB RAM recommended, 4GB minimum)
- **MicroSD Card** (32GB minimum, Class 10 or better)
- **USB Storage** (for backups, 64GB+ recommended)
- **Power Supply** (Official Raspberry Pi 5 USB-C adapter)
- **Network Connection** (Ethernet recommended for stability)

### Software Requirements

- **Raspberry Pi OS** (64-bit, Debian 12 Bookworm-based)
- **Python 3.11+**
- **Docker 24.0+**
- **Docker Compose 2.0+**
- **Git**

### Account Requirements

- **Cloudflare Account** (free tier sufficient)
- **Domain Name** (for Cloudflare Tunnel)
- **GitHub Account** (for repository access)

### Development Environment (Optional)

- **Visual Studio Code** with Python extension
- **PostgreSQL Client** (pgAdmin, DBeaver, or psql)
- **Chrome DevTools** for frontend debugging

---

## 🚀 Installation & Setup

### 1. Clone Repository

```bash
git clone https://github.com/K1taru/GyMMS.git
cd GyMMS
```

### 2. Environment Configuration

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

Edit `.env` with your configuration:

```env
# Django Configuration
SECRET_KEY=your-secret-key-here
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1,your-domain.com

# Database Configuration
DB_NAME=gymms_db
DB_USER=gymms_user
DB_PASSWORD=your-secure-password
DB_HOST=db
DB_PORT=5432

# Cloudflare Tunnel
TUNNEL_TOKEN=your-cloudflare-tunnel-token

# Email Configuration (Optional)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
EMAIL_USE_TLS=True

# Monitoring (Optional)
PROMETHEUS_ENABLED=True
GRAFANA_ADMIN_PASSWORD=admin
```

### 3. Docker Setup

#### Build and Start Containers

```bash
# Build Docker images
docker-compose build

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f
```

#### Verify Services

```bash
# Check running containers
docker-compose ps

# Expected output:
# - web (Django application)
# - db (PostgreSQL)
# - prometheus (Monitoring)
# - grafana (Visualization)
# - cloudflared (Tunnel)
```

### 4. Database Setup

```bash
# Run migrations
docker-compose exec web python manage.py migrate

# Create superuser (admin account)
docker-compose exec web python manage.py createsuperuser

# Load initial data (optional)
docker-compose exec web python manage.py loaddata initial_data.json
```

### 5. Collect Static Files

```bash
docker-compose exec web python manage.py collectstatic --noinput
```

### 6. Access the Application

- **Web Interface**: `http://localhost:8000` (local) or `https://your-domain.com` (via Cloudflare)
- **Admin Panel**: `http://localhost:8000/admin`
- **Grafana Dashboard**: `http://localhost:3000` (default: admin/admin)
- **Prometheus**: `http://localhost:9090`

---

## ⚙️ Configuration

### Environment Variables Reference

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `SECRET_KEY` | Django secret key for cryptography | Yes | - |
| `DEBUG` | Enable debug mode (use False in production) | No | False |
| `ALLOWED_HOSTS` | Comma-separated list of allowed hostnames | Yes | localhost |
| `DB_NAME` | PostgreSQL database name | Yes | gymms_db |
| `DB_USER` | Database user | Yes | gymms_user |
| `DB_PASSWORD` | Database password | Yes | - |
| `DB_HOST` | Database hostname | No | db |
| `DB_PORT` | Database port | No | 5432 |
| `TUNNEL_TOKEN` | Cloudflare Tunnel token | Yes (prod) | - |
| `EMAIL_HOST` | SMTP server hostname | No | - |
| `EMAIL_PORT` | SMTP server port | No | 587 |

### Cloudflare Tunnel Setup

1. **Create Cloudflare Account** and add your domain
2. **Install cloudflared** on Raspberry Pi (included in Docker setup)
3. **Create Tunnel**:
   ```bash
   cloudflared tunnel login
   cloudflared tunnel create gymms
   ```
4. **Configure DNS**: Point subdomain to tunnel
5. **Add Tunnel Token** to `.env` file

### Database Configuration

**PostgreSQL Optimization for Raspberry Pi**:

```sql
-- Recommended settings for 8GB RAM
shared_buffers = 512MB
effective_cache_size = 2GB
work_mem = 16MB
maintenance_work_mem = 128MB
max_connections = 100
```

Edit `docker-compose.yml` to apply custom postgres.conf.

---

## 📖 Usage

### Starting the System

#### Development Mode

```bash
# Start with live reload
docker-compose up

# Access at http://localhost:8000
```

#### Production Mode

```bash
# Start in detached mode
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f web
```

### Accessing Interfaces

#### Admin Dashboard
- URL: `/admin`
- Features: Full system administration, user management, data management
- Login: Use superuser credentials created during setup

#### Staff Dashboard
- URL: `/dashboard`
- Features: Member management, payment processing, check-ins, reports
- Login: Staff or owner credentials

#### Member Portal (Future Feature)
- URL: `/members`
- Features: View profile, payment history, class schedule

### Common Operations

#### Add New Member

1. Navigate to **Dashboard → Members → Add New**
2. Fill in member details (name, contact, emergency info)
3. Upload photo (optional)
4. Select membership plan
5. Process initial payment
6. System automatically sets membership end date

#### Process Payment

1. **Dashboard → Payments → New Payment**
2. Search and select member
3. Enter payment amount and method
4. System automatically:
   - Generates receipt
   - Extends membership period
   - Updates member status
   - Records transaction

#### Check-In Member

1. **Dashboard → Check-Ins**
2. Search member by name or ID
3. Click **Check-In** button
4. System records timestamp and updates attendance

#### View Analytics

1. **Dashboard → Analytics**
2. Select date range
3. View metrics:
   - Revenue trends
   - Active member count
   - Check-in frequency
   - Membership renewals

---

## 🌐 Deployment

### Raspberry Pi Deployment

#### Initial Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo apt install docker-compose-plugin

# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker

# Clone repository
git clone https://github.com/K1taru/GyMMS.git
cd GyMMS
```

#### Production Configuration

```bash
# Copy production environment
cp .env.production .env

# Edit with production values
nano .env

# Build and start
docker-compose -f docker-compose.prod.yml up -d
```

#### Setup Cloudflare Tunnel

```bash
# Configure tunnel
docker-compose exec cloudflared cloudflared tunnel login
docker-compose exec cloudflared cloudflared tunnel create gymms
docker-compose exec cloudflared cloudflared tunnel route dns gymms gym.yourdomain.com

# Restart tunnel service
docker-compose restart cloudflared
```

### Backup Procedures

#### Automated Daily Backups

System automatically backs up database daily to mounted USB drive.

```bash
# Check backup status
docker-compose exec web python manage.py backup_status

# Manual backup
docker-compose exec web python manage.py backup_database
```

#### Restore from Backup

```bash
# List available backups
docker-compose exec web python manage.py list_backups

# Restore specific backup
docker-compose exec web python manage.py restore_backup <backup_file>
```

### Update Procedures

```bash
# Pull latest changes
git pull origin main

# Rebuild containers
docker-compose build

# Apply migrations
docker-compose exec web python manage.py migrate

# Collect static files
docker-compose exec web python manage.py collectstatic --noinput

# Restart services
docker-compose restart
```

---

## 📁 Project Structure

```
GyMMS/
├─ .dev_utils/                 # Development utilities and documentation
│   ├─ .file_structure         # Project file structure reference
│   └─ .notes                  # Development notes
│
├─ .documentation/             # Project documentation
│   └─ academic_research_documentation/
│
├─ config/                     # Django project configuration
│   ├─ __init__.py
│   ├─ asgi.py                 # ASGI configuration
│   ├─ settings.py             # Main Django settings
│   ├─ urls.py                 # Project-level routes
│   └─ wsgi.py                 # WSGI configuration
│
├─ core/                       # Core utilities and shared components
│   ├─ management/commands/    # Custom management commands
│   ├─ migrations/             # Core app migrations
│   ├─ static/core/            # Core static files
│   ├─ templates/core/         # Core templates
│   ├─ admin.py
│   ├─ models.py               # Shared abstract models
│   └─ views.py
│
├─ dashboard/                  # Main dashboard and analytics
│   ├─ migrations/             # Dashboard model migrations
│   ├─ static/dashboard/       # Dashboard-specific assets
│   ├─ templates/dashboard/    # Dashboard HTML templates
│   ├─ check_in_helpers.py     # Check-in/out utilities
│   ├─ models.py               # Dashboard statistics models
│   └─ views.py
│
├─ media/                      # User-uploaded files
│   ├─ member_photos/          # Member profile photos
│   └─ staff_photos/           # Staff profile photos
│
├─ memberships/                # Membership management
│   ├─ migrations/             # Membership model migrations
│   ├─ templatetags/           # Custom template filters
│   ├─ forms.py                # Member forms
│   ├─ models.py               # Member and plan models
│   └─ views.py
│
├─ metrics/                    # Analytics and reporting
│   ├─ management/commands/    # Metric generation commands
│   ├─ migrations/             # Metrics model migrations
│   ├─ models.py               # Metrics snapshot models
│   └─ views.py                # Analytics dashboards
│
├─ payments/                   # Payment processing
│   ├─ management/commands/    # Payment-related commands
│   ├─ migrations/             # Payment model migrations
│   ├─ models.py               # Payment transaction models
│   ├─ signals.py              # Payment automation
│   └─ views.py
│
├─ users/                      # User authentication
│   ├─ migrations/             # User model migrations
│   ├─ forms.py                # Authentication forms
│   ├─ models.py               # Custom user model
│   └─ views.py
│
├─ .dockerignore               # Docker ignore patterns
├─ .env                        # Environment variables (not in git)
├─ .gitignore                  # Git ignore patterns
├─ docker-compose.yml          # Docker services configuration
├─ Dockerfile                  # Docker image definition
├─ LICENSE                     # MIT License
├─ manage.py                   # Django management script
├─ README.md                   # This file
└─ requirements.txt            # Python dependencies
```

---

## 🔌 Services & Integrations

### Cloudflare Tunnel

<img src="https://www.cloudflare.com/img/logo-cloudflare-dark.svg" width="200" alt="Cloudflare"/>

**Role**: Secure zero-trust remote access without port forwarding or VPN

**Features**:
- Encrypted tunnel from Raspberry Pi to Cloudflare edge
- No exposed public IP or open ports
- DDoS protection and CDN benefits
- Automatic SSL/TLS certificate management

**Setup**: See [Configuration → Cloudflare Tunnel Setup](#cloudflare-tunnel-setup)

### PostgreSQL Database

<img src="https://www.postgresql.org/media/img/about/press/elephant.png" width="120" alt="PostgreSQL"/>

**Role**: Primary relational database for all application data

**Features**:
- ACID compliance for data integrity
- Materialized views for dashboard performance
- Triggers for automated membership updates
- Full-text search capabilities
- JSON support for flexible data structures

**Optimizations**: Custom configuration for Raspberry Pi hardware

### Prometheus Monitoring

<img src="https://prometheus.io/assets/prometheus_logo_grey.svg" width="120" alt="Prometheus"/>

**Role**: System metrics collection and alerting

**Metrics Collected**:
- Application response times
- Database query performance
- Memory and CPU usage
- Request rates and error rates
- Custom business metrics (members, revenue)

**Access**: `http://localhost:9090`

### Grafana Dashboards

<img src="https://grafana.com/static/img/menu/grafana2.svg" width="120" alt="Grafana"/>

**Role**: Visual monitoring and analytics dashboards

**Dashboards**:
- System health overview
- Application performance
- Database metrics
- Business KPIs (members, revenue, check-ins)

**Access**: `http://localhost:3000` (default: admin/admin)

### Docker Containerization

<img src="https://www.docker.com/wp-content/uploads/2022/03/horizontal-logo-monochromatic-white.png" width="200" alt="Docker"/>

**Role**: Application containerization and orchestration

**Benefits**:
- Consistent deployment across environments
- Easy scaling and updates
- Isolated service dependencies
- Simplified backup and restore

**Services**: Django app, PostgreSQL, Prometheus, Grafana, Cloudflared

### Raspberry Pi Edge Computing

<img src="https://assets.raspberrypi.com/static/raspberry-pi-logo-46e0bd895c.png" width="120" alt="Raspberry Pi"/>

**Role**: Low-cost, energy-efficient production server

**Specifications**:
- Raspberry Pi 5 (8GB RAM)
- Quad-core ARM Cortex-A76 @ 2.4GHz
- Power consumption: ~8W typical
- Storage: MicroSD + USB backup

**Advantages**:
- Cost-effective (~$80 hardware)
- Low power consumption
- Sufficient for small-medium gym operations
- Local data sovereignty

---

## 🔒 Security

### Authentication & Authorization

- **Password Hashing**: PBKDF2-SHA256 with 600,000 iterations
- **Session Security**: Secure cookies, CSRF protection, session timeout
- **Role-Based Access Control (RBAC)**: Owner and Staff roles with granular permissions
- **Password Policies**: Minimum 8 characters, complexity requirements

### Data Protection

- **Encryption in Transit**: HTTPS via Cloudflare SSL/TLS
- **Database Security**: Parameterized queries prevent SQL injection
- **Input Validation**: Server-side validation on all forms
- **XSS Protection**: Django template auto-escaping enabled
- **CSRF Protection**: Token-based CSRF prevention

### Privacy & Compliance

- **Data Minimization**: Collect only necessary information
- **Soft Deletes**: Preserve data integrity while allowing "deletion"
- **Audit Logging**: Track sensitive operations (member deletion, payment changes)
- **Access Controls**: Staff can only view assigned data
- **Data Export**: Member data export functionality for GDPR compliance

### Backup & Recovery

- **Automated Backups**: Daily PostgreSQL dumps
- **Backup Rotation**: 7 daily + 4 weekly backups retained
- **Off-Site Storage**: USB drive mounted for local backups
- **Tested Restore Procedures**: Regular recovery drills
- **Docker Volumes**: Persistent storage separate from containers

### Network Security

- **Zero-Trust Access**: Cloudflare Tunnel eliminates exposed ports
- **No Port Forwarding**: No direct internet exposure
- **Firewall**: Raspberry Pi firewall configured (UFW)
- **SSH Hardening**: Key-based auth, non-standard port

---

## 🧪 Testing

### Running Tests

```bash
# Run all tests
docker-compose exec web python manage.py test

# Run specific app tests
docker-compose exec web python manage.py test memberships

# Run with coverage
docker-compose exec web coverage run --source='.' manage.py test
docker-compose exec web coverage report
```

### Test Coverage

Current test coverage: ~75%

- **Memberships**: Model validation, membership expiration logic
- **Payments**: Transaction processing, automatic renewal
- **Dashboard**: Statistics calculation, check-in logic
- **Users**: Authentication, permission checks

### Manual Testing Checklist

- [ ] Member registration and profile updates
- [ ] Payment processing and receipt generation
- [ ] Membership expiration and renewal
- [ ] Check-in/check-out functionality
- [ ] Dashboard statistics accuracy
- [ ] Role-based access control
- [ ] Responsive design on mobile devices

---

## 🐛 Troubleshooting

### Common Issues

#### Database Connection Errors

```bash
# Check database container status
docker-compose ps db

# View database logs
docker-compose logs db

# Restart database
docker-compose restart db
```

#### Cloudflare Tunnel Not Connecting

```bash
# Check tunnel logs
docker-compose logs cloudflared

# Verify tunnel token in .env
cat .env | grep TUNNEL_TOKEN

# Restart tunnel
docker-compose restart cloudflared
```

#### Static Files Not Loading

```bash
# Collect static files
docker-compose exec web python manage.py collectstatic --noinput

# Check WhiteNoise configuration in settings.py
docker-compose exec web python manage.py check --deploy
```

#### Permission Denied Errors

```bash
# Fix file permissions
sudo chown -R $USER:$USER .

# Fix media directory permissions
sudo chmod -R 755 media/
```

### Debug Mode

Enable debug mode for detailed error messages (development only):

```env
# .env
DEBUG=True
```

**⚠️ Never enable DEBUG in production!**

### Log Files

```bash
# Application logs
docker-compose logs -f web

# Database logs
docker-compose logs -f db

# All services
docker-compose logs -f
```

### Performance Issues

```bash
# Check resource usage
docker stats

# Optimize database
docker-compose exec db psql -U gymms_user -d gymms_db -c "VACUUM ANALYZE;"

# Check slow queries
docker-compose exec web python manage.py check_slow_queries
```

---

## 🤝 Contributing

Contributions are welcome! Please follow these guidelines:

### How to Contribute

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Commit changes**: `git commit -m 'Add amazing feature'`
4. **Push to branch**: `git push origin feature/amazing-feature`
5. **Open a Pull Request**

### Code Style

- Follow **PEP 8** style guide for Python code
- Use **Black** formatter: `black .`
- Write **docstrings** for all functions and classes
- Add **type hints** where appropriate
- Write **tests** for new features

### Pull Request Guidelines

- Provide clear description of changes
- Include relevant issue numbers
- Ensure all tests pass
- Update documentation if needed
- Keep PRs focused on single feature/fix

### Reporting Issues

When reporting bugs, please include:

- Python and Django version
- Steps to reproduce
- Expected vs actual behavior
- Error messages and stack traces
- Environment details (Raspberry Pi model, OS version)

---

## 📄 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

```
MIT License

Copyright (c) 2025 K1taru

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction...
```

---

## 👨‍💻 Author

**K1taru** (John Michael Garcia)

- GitHub: [@K1taru](https://github.com/K1taru)
- Repository: [GyMMS](https://github.com/K1taru/GyMMS)

---

## 🙏 Acknowledgments

This project was built with the following excellent open-source technologies:

- [Django](https://www.djangoproject.com/) - The web framework for perfectionists with deadlines
- [PostgreSQL](https://www.postgresql.org/) - The world's most advanced open source database
- [Docker](https://www.docker.com/) - Accelerate how you build, share and run applications
- [Cloudflare](https://www.cloudflare.com/) - The web performance & security company
- [Raspberry Pi](https://www.raspberrypi.org/) - Affordable computing for everybody
- [Bootstrap](https://getbootstrap.com/) - The most popular HTML, CSS, and JS library
- [Prometheus](https://prometheus.io/) - Monitoring system and time series database
- [Grafana](https://grafana.com/) - The open observability platform

Special thanks to the open-source community for making projects like this possible.

---

## 📞 Support

For support, questions, or suggestions:

- **Issues**: [GitHub Issues](https://github.com/K1taru/GyMMS/issues)
- **Discussions**: [GitHub Discussions](https://github.com/K1taru/GyMMS/discussions)
- **Documentation**: See `.documentation/` directory for detailed research documentation

---

**Built with ❤️ for small gym owners who deserve better tools**


