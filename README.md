# Discogs Data Scraper

## Overview
A streamlined tool for extracting music release information from Discogs, designed for efficiency and ease of use. Utilizes multi-threading, proxy rotation, and integrates with PostgreSQL for data storage.

## Quick Start
1. **Setup Environment**
   - Requires Python 3.7+.
   - Install dependencies: `pip install -r requirements.txt`.
   - Setup `.env` with PostgreSQL and proxy details. (use the `.env.example` for guidance)

2. **Run Scraper**
   ```bash
   python main.py
   ```

## Components

### `main.py`
Entry point. Processes release IDs in batches and writes data to PostgreSQL.
- **Example**: Batch process and store data.
  ```python
  # main.py snippet
  for i in range(0, len(release_ids), BATCH_SIZE):
      batch_ids = release_ids[i:i + BATCH_SIZE]
      releases = scraper.run_scraper(URL, batch_ids, MAX_WORKERS)
      write_to_postgres(p, releases)
  ```

### `scraper.py`
Manages proxy rotation and scraping tasks.
- **Usage**: Fetch release data.
  ```python
  # Using run_scraper
  releases = scraper.run_scraper(PROXY_URL, release_ids, MAX_WORKERS)
  ```

### `data.py`
Defines page interaction classes.
- **Example**: Fetch and parse a release page.
  ```python
  # data.py snippet
  release_page = DiscogsRelease(release_id)
  release_page.fetch_and_parse()
  ```

### `xml_handler.py`
For XML data ingestion.
- **Example**: Parse XML to extract release data.
  ```python
  # Using XMLDataHandler
  handler = XMLDataHandler(DATA_URL, DEST_DIR)
  handler.download_file()
  handler.parse_xml()
  ```

## Usage

1. **Configure Environment**
   - Define environment variables in `.env`.

2. **Running the Scraper**
   - Execute `main.py` to start scraping Discogs based on a list of release IDs.

3. **Ingesting XML Data**
   - Use `load.py` for XML-based workflows, adapting `XMLDataHandler` as needed.
