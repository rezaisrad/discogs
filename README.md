# Discogs Data Scraper

## Overview
Tool for extracting music release information from Discogs, designed for efficiency and ease of use. Utilizes multi-threading, proxy rotation, and integrates with PostgreSQL for data storage.

## Project Structure

- `db/`: SQL scripts for database initialization and cleanup.
- `examples/`: Jupyter notebooks for sandbox testing and examples.
- `src/`: Main source code directory.
  - `managers/`: Proxy and session management utilities.
  - `models/`: Data models and sinks for processing and storing fetched data.
  - `scraper/`: Core scraper functionality.
  - `utils/`: Utility scripts for XML handling and parser utilities.
- `tests/`: Unit tests for the various components of the scraper.
- `requirements.txt`: Project dependencies.
- `main.py`: Entry point for running the scraper.

## Getting Started

### Prerequisites

- Python 3.9 or higher
- PostgreSQL database

### Installation

1. **Clone the Repository**

   ```
   git clone https://github.com/your-github-username/your-repo-name.git
   cd your-repo-name
   ```

2. **Set Up a Virtual Environment (optional)**

   ```
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install Dependencies**

   ```
   pip install -r requirements.txt
   ```

4. **Environment Configuration**

   Copy the `.env.example` file to `.env` and update the variables to match your environment.

   ```
   cp .env.example .env
   ```

5. **Database Setup**

   The files in the `db/` directory can help guide you in creating your database

### Running the Scraper

To start the scraper, use the `main.py` script.

```
python src/main.py
```

This will fetch data based on the configurations and save the results to your database.

## Usage

### Running the Extractor

`main.py` is designed to fetch release information from Discogs. Adjust the `QUERY_PATH` in `main.py` to specify the SQL query that will return the release IDs you want to pull additional information for.

### XML Loading from File

Utility scripts for XML processing are available under `src/utils/xml_handler.py`. These can be used for loading and parsing XML files as needed.

### Testing

Unit tests are located in the `tests/` directory. Run tests using pytest:

```
pytest tests/
```
