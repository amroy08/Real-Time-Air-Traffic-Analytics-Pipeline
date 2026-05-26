# Real-Time Air Traffic Analytics Pipeline

## Project Overview

This project is a real-time air traffic analytics pipeline built using OpenSky API, Python, Google BigQuery, SQL, local cron automation, and Power BI.

The pipeline fetches live aircraft state-vector data for India, cleans and transforms the data, stores timestamped snapshots in BigQuery, and visualizes insights through a 5-page Power BI dashboard.

## Architecture

OpenSky API  
→ Python Ingestion Script  
→ Local CSV Backup  
→ Google BigQuery  
→ SQL Views  
→ Power BI Dashboard  
→ Local Cron Automation every 10 minutes

## Tech Stack

- Python
- Pandas
- Requests
- Google BigQuery
- SQL
- Power BI
- OpenSky Network API
- Cron Scheduler

## Features

- Fetches live aircraft data from OpenSky API
- Cleans latitude, longitude, speed, altitude, aircraft status, and origin country
- Stores every ingestion as a timestamped snapshot in BigQuery
- Creates analytical SQL views for reporting
- Builds a Power BI dashboard with live KPIs and aircraft map visualization
- Tracks pipeline runs and data freshness

## Dashboard Pages

1. Live Overview  
   - Total aircraft
   - Airborne aircraft
   - Aircraft on ground
   - Origin countries
   - Average speed
   - Average altitude
   - Last refresh time

2. Live Aircraft Map  
   - Aircraft positions using latitude and longitude
   - Origin country slicer
   - Altitude band slicer
   - Aircraft details table

3. Country Analysis  
   - Country-wise aircraft count
   - Average speed by country
   - Average altitude by country

4. Altitude & Speed Analysis  
   - Aircraft distribution by altitude band
   - Average speed by altitude band
   - Altitude-band trend over time

5. Pipeline Monitoring  
   - Records loaded per run
   - Unique aircraft count
   - Null location records
   - API time
   - Pipeline run history

## BigQuery Views

- `vw_live_aircraft_summary`
- `vw_latest_aircraft_snapshot`
- `vw_aircraft_by_country`
- `vw_altitude_band_summary`
- `vw_pipeline_run_summary`

## How to Run Locally

1. Create a virtual environment

```bash
python3 -m venv venv
source venv/bin/activate
