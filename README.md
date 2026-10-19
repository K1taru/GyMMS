# GyMMS

**Gym Membership Management System**

GyMMS brings a gym's front desk and day-to-day management into one web application. Owners and staff can manage members, track attendance, collect payments, and review business performance from a browser.

Built for gym operations in the Philippines, GyMMS records amounts in Philippine pesos and uses Asia/Manila time for dates and reporting.

**Open GyMMS:** [gymms.k1taru.space](https://gymms.k1taru.space/)

## What GyMMS does

- **Member management:** Register members, maintain profiles and photos, and track membership status and expiry dates.
- **Attendance:** Check members in and out and view gym activity from the dashboard.
- **Memberships and pricing:** Manage membership plans and durations, collect renewals, and handle walk-in customers.
- **Payments and receipts:** Record cash payments and offer optional PayMongo QR Ph checkout for supported banks and wallets, including GCash, Maya, and GoTyme. Digital payments are confirmed through the provider before a live payment is recorded and membership is updated.
- **Transaction history:** Search and filter payments by customer, dates, and payment method. View full payment references and the staff member who processed each transaction.
- **Business reporting:** Explore revenue, attendance, membership trends, retention, and payment methods through interactive charts. Owners can also review completed sales by processor.
- **Owner and staff accounts:** Separate access for daily front-desk work and owner administration, including staff account management and pricing controls.

Payment records retain member, plan, and processor details from the time of the transaction, preserving historical context when profiles change.

## Deployment

GyMMS is self-hosted on a 64-bit Raspberry Pi using Docker Compose. Cloudflare Tunnel provides the public HTTPS connection to the application; the web service listens only on the host's loopback interface, and PostgreSQL stays on the private container network.

The deployment runs the web application, PostgreSQL, and a background payment worker. Database storage and uploaded member photos persist separately from application containers.

The release pipeline uses GitHub Actions and GitHub Container Registry to build and publish signed images for ARM64 and AMD64. The host deployment service supports verifying those releases, backing up data, and applying updates. Operational configuration and deployment status are covered in the [CI/CD guide](docs/ci-cd.md).

## Technology

| Layer | Technology |
| --- | --- |
| Application | Python 3.14.8 and Django 6.1.2 |
| Interface | Django templates, HTML, CSS, and JavaScript with Fetch for dynamic updates |
| Charts | Chart.js |
| Database | PostgreSQL 18.6 with Psycopg 3 |
| Web serving | Gunicorn and WhiteNoise |
| Payments | PayMongo QR Ph API, signed webhooks, and a Django background worker |
| Hosting | Docker Compose on Raspberry Pi, exposed through Cloudflare Tunnel |
| Releases | GitHub Actions, GitHub Container Registry, and Cosign signature verification |

## Documentation

For administrators maintaining an installation:

- [Setup and configuration](docs/setup.md)
- [Docker operations, backups, and recovery](docs/docker.md)
- [PayMongo payments](docs/paymongo.md)
- [CI/CD and signed releases](docs/ci-cd.md)
- [Metrics dashboard](metrics/README.md)
