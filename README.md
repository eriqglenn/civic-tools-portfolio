# Civic Tools for Houston Planning

Tools I built with AI coding assistance (Codex) to support city planning casework, the
Planning & Development front desk, and neighborhood leaders in Houston, Texas.

I'm a city planner, not a software engineer by training. I supplied the city's templates and
processes, walked the AI through how the work is actually done, and tested every build against
real case files before staff used it.

| Project | Who it's for | What it does |
|---|---|---|
| [Planning Wizard](planning-wizard/) (v1.30) | Planners | Turns one case workbook into owner notices, staff reports, maps and a draft council packet |
| [Neighborhood Ledger](neighborhood-ledger/) (AI edition) | Super Neighborhood leaders | Tracks resident concerns, maps public works projects, searches deed records, and drafts follow-ups with an AI assistant |
| [Front Desk Guide](front-desk-guide/) | Front desk staff | A bilingual decision tree that routes visitors and callers to the right office |

---

## Planning Wizard

Houston residents can ask the city to protect the character of their block through
**Special Minimum Lot Size (MLS)** and **Special Minimum Building Line (MBL)** applications.
Preparing one meant pulling county property records parcel by parcel, mapping every affected lot,
and retyping the same details into notices, a staff report and a council packet.

- **About 14 hours down to about 27 minutes** per block case, including planner review
- Four wizards: MLS, MBL, MLS Renewal, MBL Renewal
- Imports the application PDF, fills the calculation workbook, and pulls Harris County Appraisal
  District (HCAD) records. The downloader collected 270+ property records.
- Builds boundary maps from public parcel and street data, with a preview the planner approves
- Generates owner notification letters, staff reports, ordinances, routing forms and the
  Planning Commission packet from city templates
- Packaged as a Windows desktop app staff run without installing Python

**Stack:** Python, Tkinter, python-docx, openpyxl, PyMuPDF, Playwright, ArcGIS REST services, PyInstaller

## Neighborhood Ledger (AI edition)

A desktop workspace for each of Houston's 88 Super Neighborhoods.

- Track resident concerns and follow-ups
- Map Houston Public Works capital projects inside the official neighborhood boundary
- Search the county deed index by subdivision
- Prepare MLS applications for residents
- Gather current local news and City Council items
- **AI assistant** (text or voice): a leader can say "check 311 case ____ and draft a follow-up."
  The assistant runs a live lookup, shows its sources and the time of each check, and returns an
  **editable draft**. Nothing is sent automatically, and the leader reviews and saves every draft.
- Privacy by design: contact fields are never sent to the model, credentials are encrypted with
  Windows DPAPI, and a No-AI edition is available for offices that can't use AI services
- 177 automated tests (`python run_tests.py`)

**Stack:** Python, HTML/CSS/JavaScript, Leaflet, SQLite, OpenAI API / Codex, C# (microphone bridge)

## Front Desk Guide

A single HTML page with no install. Staff answer a short series of questions about what the visitor
needs, and the guide shows the right office, contact, and a script to read aloud in English or
Spanish. To try it, open [`front-desk-guide/index.html`](front-desk-guide/index.html) in a browser.

---

## What's not in this repository

To protect residents and city systems, this portfolio copy leaves out:

- City document templates, the City seal, and filled case workbooks
- Real property records, case files and resident data
- Packaged executables and installers
- Individual staff names and direct phone lines (replaced with department contacts)
- Internal network addresses (replaced with placeholders)

Addresses and account numbers in tests are fictional. Because the templates are excluded, the
Planning Wizard won't generate documents from this copy. The code shows how it works.
