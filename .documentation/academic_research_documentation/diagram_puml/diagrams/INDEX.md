# GyMMS Diagram Index

## Overview

This directory contains 5 Graphviz DOT files that generate professional diagrams for the GyMMS academic research documentation. Each diagram is available in three formats (PNG, SVG, PDF) for different use cases.

---

## Diagram Catalog

### 1. Use Case Diagram
**File:** `use_case_diagram.dot`  
**Outputs:** `output/use_case_diagram.{png,svg,pdf}`  
**Document Location:** Figure 3.1 - System Analysis, Section 3.4  
**Purpose:** Illustrates system actors (Owner, Staff, Member) and their interactions with system functions  

**Key Elements:**
- 3 Actor types with different permission levels
- 14 Primary use cases covering core functionality
- 4 Admin-only use cases for system configuration
- 4 Extended/included use cases for reusable functions
- Include and extend relationships showing dependencies
- Color-coded legend distinguishing use case types

**Best Used For:** Understanding who uses the system and what actions they can perform

---

### 2. System Architecture Diagram
**File:** `system_architecture_diagram.dot`  
**Outputs:** `output/system_architecture_diagram.{png,svg,pdf}`  
**Document Location:** Figure 3.2 - System Analysis, Section 3.5  
**Purpose:** Depicts three-tier architecture with technology stack details  

**Key Elements:**
- Presentation Tier: Client devices (Desktop, Tablet, Mobile) with web technologies
- Application Tier: Django 5.0+ framework with MVT pattern and 6 modular apps
- Data Tier: PostgreSQL 16 database with 9 interconnected tables
- Infrastructure Layer: Docker containerization on Raspberry Pi 5 hardware
- Cloudflare Tunnel for secure remote access
- Request/response flow paths with protocol labels
- Technology specifications for each component

**Best Used For:** Understanding overall system structure and technology choices

---

### 3. Deployment Infrastructure Diagram
**File:** `deployment_infrastructure_diagram.dot`  
**Outputs:** `output/deployment_infrastructure_diagram.{png,svg,pdf}`  
**Document Location:** Figure 4.1 - Design & Implementation, Section 4.1.1  
**Purpose:** Shows physical deployment architecture and networking  

**Key Elements:**
- End-to-end request flow from users through Cloudflare to Raspberry Pi
- Cloudflare Edge Network with security features (DDoS, WAF, SSL/TLS, CDN)
- Docker container details: gymms_web, gymms_db, gymms_nginx
- Container networking with bridge network and DNS resolution
- Docker volumes for persistent storage (database, media, static files)
- Optional monitoring stack (Prometheus, Grafana, exporters)
- Automated backup system
- Hardware specifications (CPU, RAM, Storage, Power consumption)
- Cost analysis showing operational expenses

**Best Used For:** Understanding how the system is deployed and runs in production

---

### 4. Database Schema Diagram
**File:** `database_schema_diagram.dot`  
**Outputs:** `output/database_schema_diagram.{png,svg,pdf}`  
**Document Location:** Figure 3.3 - System Analysis, Section 3.6  
**Purpose:** Displays complete database structure with tables and relationships  

**Key Elements:**
- 9 Database tables with all fields and data types
- Foreign key relationships with 1:N cardinality indicators
- Color coding: Core tables (green), Config tables (yellow), Transaction tables (red), Aggregate tables (wheat)
- Indexes on frequently queried fields
- Constraints and data integrity rules
- Soft-delete pattern for data preservation
- UUID usage for transaction identifiers

**Tables:**
- StaffUser: Authentication and user management
- Member: Core member information and subscription tracking
- MembershipConfig: System configuration for membership rules
- MembershipPricing: Pricing tiers (1 month, 3 months, 6 months, 1 year)
- Payment: Transaction records with data preservation
- GymCheckIn: Attendance tracking with session duration
- DashboardStats: Materialized view for dashboard metrics
- PaymentSummary: Aggregated financial data
- ActiveMemberSnapshot: Historical snapshots for analytics

**Best Used For:** Understanding data structure and table relationships

---

### 5. User Story Map
**File:** `user_story_map.dot`  
**Outputs:** `output/user_story_map.{png,svg,pdf}`  
**Document Location:** Supplementary material for Section 3.4  
**Purpose:** Visual representation of user stories organized by activities  

**Key Elements:**
- 6 User activities (epics): Authentication, Member Management, Payment Processing, Facility Access, Analytics, Administration
- 23 User stories in "As a [role], I want [action], so that [benefit]" format
- Implementation priorities: MVP (green), Phase 2 (yellow), Future (blue)
- Stories grouped by epic and arranged by workflow
- MVP stories (8 total) covering essential functionality
- Phase 2 stories (10 total) for enhanced features
- Future enhancements (5 total) for long-term roadmap

**Best Used For:** Understanding user requirements and implementation priorities

---

## Quick Reference Table

| Diagram | Purpose | Audience | Complexity | Size (PNG) |
|---------|---------|----------|------------|------------|
| Use Case | System functionality | Non-technical stakeholders | Medium | 143 KB |
| System Architecture | Technical structure | Developers, architects | High | 195 KB |
| Deployment Infrastructure | Production deployment | DevOps, system admins | High | 130 KB |
| Database Schema | Data structure | Database developers | High | 174 KB |
| User Story Map | Requirements & priorities | Product owners, stakeholders | Medium | ~150 KB |

---

## Generation Commands

### Generate All Diagrams
```bash
# Windows PowerShell
.\generate_diagrams.ps1

# Linux/macOS/Raspberry Pi
./generate_diagrams.sh
```

### Generate Individual Diagram
```bash
# PNG format (web/presentations)
dot -Tpng use_case_diagram.dot -o output/use_case_diagram.png

# SVG format (documents, recommended)
dot -Tsvg use_case_diagram.dot -o output/use_case_diagram.svg

# PDF format (printing)
dot -Tpdf use_case_diagram.dot -o output/use_case_diagram.pdf

# High-resolution PNG (300 DPI)
dot -Tpng -Gdpi=300 use_case_diagram.dot -o output/use_case_diagram_hires.png
```

---

## Usage Guidelines

### In Academic Papers

**APA Format:**
```
Figure 1. Use case diagram showing primary actors and system interactions.
```

**LaTeX:**
```latex
\begin{figure}[h]
  \centering
  \includegraphics[width=0.9\textwidth]{diagrams/output/use_case_diagram.pdf}
  \caption{Use case diagram showing primary actors and system interactions}
  \label{fig:use_case}
\end{figure}

As shown in Figure~\ref{fig:use_case}, the system supports three actor types...
```

**Markdown:**
```markdown
![Use Case Diagram](diagrams/output/use_case_diagram.png)
*Figure 3.1: Use case diagram showing primary actors and system interactions*
```

### In Presentations

- Use PNG format for PowerPoint/Google Slides
- SVG format for web-based presentations
- Ensure diagrams are readable at projection size
- Consider splitting complex diagrams across multiple slides

### For Documentation Website

- Use SVG format for scalability
- Provide PNG fallback for older browsers
- Implement lightbox/zoom functionality for detailed diagrams
- Add alt text for accessibility

---

## Diagram Maintenance

### When to Update

1. **Use Case Diagram:** When adding/removing system features or changing user roles
2. **System Architecture:** When changing technology stack or architectural patterns
3. **Deployment Infrastructure:** When modifying hosting setup or container configuration
4. **Database Schema:** When adding/modifying tables or changing relationships
5. **User Story Map:** When adding stories or reprioritizing features

### Update Process

1. Edit the `.dot` source file
2. Test changes by generating locally: `dot -Tpng file.dot -o test.png`
3. Review generated image for accuracy
4. Regenerate all formats: `./generate_diagrams.sh` or `.\generate_diagrams.ps1`
5. Update references in documentation if figure numbers changed
6. Commit both source `.dot` files and generated outputs to version control

---

## Troubleshooting

### Common Issues

**"dot: command not found"**
- Install Graphviz: See README.md for platform-specific instructions

**Overlapping nodes or text**
- Increase `nodesep` or `ranksep` values in the DOT file
- Try different layout engine: `neato -Tpng file.dot -o output.png`

**Large file sizes**
- PNG files are larger; use SVG for documents
- Reduce DPI: `dot -Tpng -Gdpi=72 file.dot -o output.png`
- Simplify diagram or split into multiple diagrams

**Text too small**
- Increase `fontsize` attribute in DOT file
- Generate higher DPI: `dot -Tpng -Gdpi=150 file.dot -o output.png`

---

## File Structure

```
diagrams/
├── README.md                              # Detailed usage guide
├── INDEX.md                               # This file
├── GENERATION_SUMMARY.md                  # Generation report
├── generate_diagrams.sh                   # Linux/macOS generation script
├── generate_diagrams.ps1                  # Windows PowerShell script
├── use_case_diagram.dot                   # Source: Use cases
├── system_architecture_diagram.dot        # Source: Architecture
├── deployment_infrastructure_diagram.dot  # Source: Deployment
├── database_schema_diagram.dot            # Source: Database
├── user_story_map.dot                     # Source: User stories
└── output/                                # Generated images
    ├── use_case_diagram.png
    ├── use_case_diagram.svg
    ├── use_case_diagram.pdf
    ├── system_architecture_diagram.png
    ├── system_architecture_diagram.svg
    ├── system_architecture_diagram.pdf
    ├── deployment_infrastructure_diagram.png
    ├── deployment_infrastructure_diagram.svg
    ├── deployment_infrastructure_diagram.pdf
    ├── database_schema_diagram.png
    ├── database_schema_diagram.svg
    ├── database_schema_diagram.pdf
    ├── user_story_map.png
    ├── user_story_map.svg
    └── user_story_map.pdf
```

---

## Resources

- [Graphviz Official Documentation](https://graphviz.org/documentation/)
- [DOT Language Guide](https://graphviz.org/doc/info/lang.html)
- [Node Shapes Gallery](https://graphviz.org/doc/info/shapes.html)
- [Color Reference](https://graphviz.org/doc/info/colors.html)
- [Layout Engines](https://graphviz.org/docs/layouts/)

---

## Credits

Diagrams created for the Gym Membership Management System (GyMMS) academic research documentation.

**Author:** K1taru  
**Created:** November 2025  
**Tool:** Graphviz 14.0.4  
**License:** Same as GyMMS project
