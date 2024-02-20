# Discogs Data Extractor

## Overview

This tool is designed for extracting and managing music release information from Discogs. It utilizes multi-threading for efficiency, proxy rotation for reliability, and integrates seamlessly with PostgreSQL for robust data storage.

## Features

- **Low Memory XML Loading** (under 500mb memory usage for 13gb xml.gz file) 
- **Proxy rotation** to manage request limits.
- **Multi-threaded requests** for efficient data extraction.
- **PostgreSQL** for data storage.

## Getting Started

### Prerequisites

- Python 3.9+
- PostgreSQL

### Installation

1. Clone the repository and navigate into it:
   ```sh
   git clone https://github.com/your-github-username/your-repo-name.git
   cd your-repo-name
   ```
2. (Optional) Set up a virtual environment:
   ```sh
   python3 -m venv venv
   source venv/bin/activate
   ```
3. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```
4. Set up environment variables by copying `.env.example` to `.env` and adjusting values:
   ```sh
   cp .env.example .env
   ```

### Database Setup

Run SQL scripts located in `db/` to set up and initialize your database.

## Usage

### 1. XML Data Loading

Load data from [Discogs monthly dumps](https://discogs-data-dumps.s3.us-west-2.amazonaws.com/index.html) using `load.py`. This script downloads an XML.gz file, parses relevant fields, and loads data into PostgreSQL. Currently, it supports loading data for releases and artists, storing each record with a primary key and a JSONB column named `data`.

Example usage for loading artist data:
```python
handler = XMLDataHandler(DATA_URL, 
                         DESTINATION_DIR,
                         data_store,
                         ArtistParser()
                         )
```

### 2. Extracting Additional Information

1. Use `main.py` to fetch additional information from Discogs based on a set of release IDs. Example query from `QUERY_PATH`: 
```
SELECT id
FROM releases e
JOIN release_formats f ON f.release_id = e.id
WHERE format_name = 'Vinyl'
AND release_date BETWEEN '2000-01-01` AND '2002-01-01'
```
2. Iterate through the set of `id` values using the `scraper` object
```
scraper = Scraper(URL, max_workers=MAX_WORKERS)
```
3. Insert into your postgres table using the `BATCH_SIZE` constant
```
   for i in range(0, len(release_ids), BATCH_SIZE):
      batch_ids = release_ids[i : i + BATCH_SIZE]
      try:
         releases = scraper.run(batch_ids)
         write_to_postgres(p, releases)
      except Exception as e:
         logging.error(f"Error processing batch {i//BATCH_SIZE}: {e}")
```

### Session and Proxy Management

The `SessionManager` and `ProxyManager` classes ensure efficient and reliable extracting:

- **SessionManager** maintains a session for each thread, utilizing proxies from **ProxyManager**.
- **ProxyManager** handles proxy rotation, selecting a new proxy if the current one fails.

Example:
```python
proxy_manager = ProxyManager(PROXIES_URL)
session_manager = SessionManager(proxy_manager)
scraper = Scraper(proxy_list_url=PROXIES_URL, max_workers=MAX_WORKERS)
```

Each thread created by the `Scraper` uses a unique session and proxy, managed by `SessionManager`. I have had success using setting my `MAX_WORKERS=32`.

## Testing

Run unit tests using pytest:
```sh
pytest tests/
```
