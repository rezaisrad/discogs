import logging
from urllib.parse import urlparse
import requests
from tqdm import tqdm
import gzip
from lxml import etree
import os
from dotenv import load_dotenv

load_dotenv()

BATCH_SIZE = os.getenv("BATCH_SIZE", 10000)


def log_method(func):
    """Decorator to log class method calls."""

    def wrapper(self, *args, **kwargs):
        logging.info(f"Starting {func.__name__}")
        result = func(self, *args, **kwargs)
        logging.info(f"Completed {func.__name__}")
        return result

    return wrapper


class XMLDataHandler:
    def __init__(self, url, destination_dir="./", data_store=None):
        self.url = url
        self.destination_dir = destination_dir
        self.filename = self._get_filename_from_url()
        self.filepath = os.path.join(self.destination_dir, self.filename)
        self.data_store = data_store

    def _get_filename_from_url(self):
        parsed_url = urlparse(self.url)
        return os.path.basename(parsed_url.path)

    @log_method
    def download_file(self):
        if os.path.exists(self.filepath):
            logging.info(f"File already exists: {self.filepath}")
            return
        logging.info(f"Downloading file to {self.filepath}")
        with (
            requests.get(self.url, stream=True) as response,
            open(self.filepath, "wb") as file,
            tqdm(
                desc="Downloading",
                total=int(response.headers.get("content-length", 0)),
                unit="B",
                unit_scale=True,
            ) as progress_bar,
        ):
            for chunk in response.iter_content(chunk_size=4096):
                file.write(chunk)
                progress_bar.update(len(chunk))

    @log_method
    def parse_xml(self):
        logging.info("Beginning XML parsing")
        data_batch = []
        release_count = 0
        try:
            with gzip.open(self.filepath, "rb") as gz_file:
                for _, elem in etree.iterparse(gz_file, events=("end",), tag="release"):
                    # Assume ReleaseParser(elem).parse() returns a dict representing a release
                    parsed_data = ReleaseParser(elem).parse()
                    data_batch.append(parsed_data)
                    elem.clear()
                    release_count += 1

                    if len(data_batch) >= BATCH_SIZE:
                        logging.info(
                            f"Inserting batch of {len(data_batch)} releases, total parsed: {release_count}"
                        )
                        self.data_store.insert(data_batch)
                        data_batch = []

                if data_batch:
                    logging.info(
                        f"Inserting final batch of {len(data_batch)} releases, total parsed: {release_count}"
                    )
                    self.data_store.insert(data_batch)
        except Exception as e:
            logging.error(f"Error during XML parsing or data insertion: {e}")
        logging.info(f"Completed XML parsing, total releases parsed: {release_count}")


class ReleaseParser:
    def __init__(self, elem):
        self.root = elem

    def parse(self):
        logging.debug("Parsing release data.")
        return {
            "id": self.root.attrib.get("id"),
            "status": self.root.attrib.get("status"),
            "title": self.root.findtext("title"),
            "artists": self._parse_artists(),
            "extraartists": self._parse_extra_artists(),
            "labels": self._parse_labels(),
            "formats": self._parse_formats(),
            "genres": self._parse_elements(self.root, ".//genre"),
            "styles": self._parse_elements(self.root, ".//style"),
            "country": self.root.findtext("country"),
            "released": self.root.findtext("released"),
            "notes": self.root.findtext("notes"),
            "data_quality": self.root.findtext("data_quality"),
            "master_id": self._get_attribute(
                self.root.find("master_id"), "is_main_release"
            ),
            "tracklist": self._parse_tracklist(),
            "videos": self._parse_videos(),
            "companies": self._parse_companies(),
            "images": self._parse_images(),
        }

    def _get_attribute(self, elem, attr_name):
        """Safely gets an attribute from an element, returning None if the element or attribute doesn't exist."""
        if elem is not None:
            return elem.attrib.get(attr_name)
        return None

    def _parse_images(self):
        return [
            {
                "type": self._get_attribute(image, "type"),
                "uri": self._get_attribute(image, "uri"),
                "uri150": self._get_attribute(image, "uri150"),
                "width": self._get_attribute(image, "width"),
                "height": self._get_attribute(image, "height"),
            }
            for image in self.root.findall(".//images/image")
        ]

    def _parse_extra_artists(self):
        return [
            {
                "id": artist.find("id").text if artist.find("id") is not None else None,
                "name": (
                    artist.find("name").text
                    if artist.find("name") is not None
                    else None
                ),
                "role": (
                    artist.find("role").text
                    if artist.find("role") is not None
                    else None
                ),
            }
            for artist in self.root.findall(".//extraartists/artist")
        ]

    def _parse_formats(self):
        return [
            {
                "name": self._get_attribute(format_, "name"),
                "qty": self._get_attribute(format_, "qty"),
                "descriptions": [
                    desc.text for desc in format_.findall(".//description") if desc.text
                ],
            }
            for format_ in self.root.findall(".//formats/format")
        ]

    def _parse_artists(self):
        return [
            {"id": artist.find("id").text, "name": artist.find("name").text}
            for artist in self.root.findall(".//artists/artist")
        ]

    def _parse_labels(self):
        return [
            {
                "name": label.attrib.get("name"),
                "catno": label.attrib.get("catno"),
                "id": label.attrib.get("id"),
            }
            for label in self.root.findall(".//labels/label")
        ]

    def _parse_elements(self, root, xpath):
        return [element.text.strip() for element in root.findall(xpath) if element.text]

    def _parse_tracklist(self):
        return [
            {
                "position": track.find("position").text,
                "title": track.find("title").text,
                "duration": track.find("duration").text,
            }
            for track in self.root.findall(".//tracklist/track")
        ]

    def _parse_videos(self):
        return [
            {
                "src": video.attrib.get("src"),
                "title": video.find("title").text,
                "description": video.find("description").text,
            }
            for video in self.root.findall(".//videos/video")
        ]

    def _parse_companies(self):
        return [
            {
                "id": company.find("id").text,
                "name": company.find("name").text,
                "entity_type_name": company.find("entity_type_name").text,
            }
            for company in self.root.findall(".//companies/company")
        ]
