import logging
from urllib.parse import urlparse
import requests
from tqdm import tqdm
import gzip
from lxml import etree
import os
from dotenv import load_dotenv

load_dotenv()

BATCH_SIZE = int(os.getenv("BATCH_SIZE", 10000))


def log_method(func):
    """Decorator to log class method calls."""

    def wrapper(self, *args, **kwargs):
        logging.info(f"Starting {func.__name__}")
        result = func(self, *args, **kwargs)
        logging.info(f"Completed {func.__name__}")
        return result

    return wrapper

class XMLDataHandler:
    def __init__(self, url, destination_dir="./",
                 data_store=None, parser_class=None,
                 keep_file=False):
        self.url = url
        self.destination_dir = destination_dir
        self.filename = self._get_filename_from_url()
        self.filepath = os.path.join(self.destination_dir, self.filename)
        self.data_store = data_store
        self.parser_class = parser_class
        self.keep_file = keep_file

    def _get_filename_from_url(self):
        parsed_url = urlparse(self.url)
        return os.path.basename(parsed_url.path)

    @log_method
    def download_file(self):
        """Downloads the XML file."""
        if os.path.exists(self.filepath):
            logging.info(f"File already exists: {self.filepath}")
            return
        logging.info(f"Downloading {self.parser_class.name} file to {self.filepath}")
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

    def parse_xml(self):
        if not self.parser_class:
            raise ValueError("Parser class not defined.")
        data_batch = []
        count = 0
        logging.info(f"Beginning XML parsing for {self.parser_class.name}")
        try:
            with gzip.open(self.filepath, "rb") as gz_file:
                for _, elem in etree.iterparse(gz_file, events=("end",), tag=self.parser_class.name):
                    parsed_data = self.parser_class.parse(elem)
                    data_batch.append(parsed_data)  
                    elem.clear()
                    count += 1

                    if len(data_batch) >= BATCH_SIZE:
                        logging.info(
                            f"Inserting batch of {len(data_batch)} {self.parser_class.name}, total parsed: {count}"
                        )
                        self.data_store.insert(data_batch)
                        data_batch = []

                if data_batch:
                    logging.info(
                        f"Inserting final batch of {len(data_batch)} {self.parser_class.name}, total parsed: {count}"
                    )
                    self.data_store.insert(data_batch)

            if not self.keep_file:
                self.delete_file()

        except KeyboardInterrupt:
            logging.info(
                "XML parsing interrupted by user. Cleanup will not delete the file."
            )
        except Exception as e:
            logging.error(f"Error during XML parsing or data insertion: {e}")

        logging.info(f"Completed XML parsing, total {self.parser_class.name} parsed: {count}")

    @log_method
    def delete_file(self):
        """Deletes the downloaded XML file after successful parsing."""
        try:
            os.remove(self.filepath)
            logging.info(f"Successfully deleted file: {self.filepath}")
        except OSError as e:
            logging.error(f"Error deleting file {self.filepath}: {e}")

class BaseParser:
    name = None

    def parse(self, elem):
        raise NotImplementedError("The parse method must be implemented by subclasses.")
    
class ArtistParser:
    name = 'artist'

    @staticmethod
    def parse(elem):
        logging.debug("Parsing artist data.")
        try:
            artist_info = {
                "id": int(elem.findtext("id")),
                "name": elem.findtext("name"),
                "realname": elem.findtext("realname"),
                "profile": elem.findtext("profile"),
                "data_quality": elem.findtext("data_quality"),
                "urls": [url.text for url in elem.findall("urls/url")],
                "namevariations": [name.text for name in elem.findall("namevariations/name")]
            }
            
            # Parsing images
            artist_info["images"] = ArtistParser._parse_images(elem)
            
            # Parsing aliases
            artist_info["aliases"] = ArtistParser._parse_aliases(elem)
            
            # Parsing groups
            artist_info["groups"] = ArtistParser._parse_groups(elem)
            
            return artist_info
        except Exception as e:
            logging.error(f"Error parsing artist: {e}")
            return {}

    @staticmethod
    def _parse_images(elem):
        """
        Parses the image information from an artist element.
        
        Args:
            elem: An lxml.etree.Element representing an artist in the XML.
            
        Returns:
            A list of dictionaries, each representing an image.
        """
        return [
            {
                "type": image.get("type"),
                "uri": image.get("uri"),
                "uri150": image.get("uri150"),
                "width": image.get("width"),
                "height": image.get("height")
            }
            for image in elem.findall("images/image")
        ]

    @staticmethod
    def _parse_aliases(elem):
        """
        Parses the aliases from an artist element.
        
        Args:
            elem: An lxml.etree.Element representing an artist in the XML.
            
        Returns:
            A list of dictionaries, each representing an alias.
        """
        return [
            {
                "id": int(alias.get("id")),
                "name": alias.text
            }
            for alias in elem.findall("aliases/name")
        ]

    @staticmethod
    def _parse_groups(elem):
        """
        Parses the groups from an artist element.
        
        Args:
            elem: An lxml.etree.Element representing an artist in the XML.
            
        Returns:
            A list of dictionaries, each representing a group.
        """
        return [
            {
                "id": int(group.get("id")),
                "name": group.text
            }
            for group in elem.findall("groups/name")
        ]

class ReleaseParser(BaseParser):
    name = 'release'
   
    @staticmethod
    def parse(elem):
        logging.debug("Parsing release data.")
        try:
            return {
                "id": elem.attrib.get("id"),
                "status": elem.attrib.get("status"),
                "title": elem.findtext("title"),
                "artists": ReleaseParser._parse_artists(elem),
                "extraartists": ReleaseParser._parse_extra_artists(elem),
                "labels": ReleaseParser._parse_labels(elem),
                "formats": ReleaseParser._parse_formats(elem),
                "genres": ReleaseParser._parse_elements(elem, ".//genre"),
                "styles": ReleaseParser._parse_elements(elem, ".//style"),
                "country": elem.findtext("country"),
                "released": elem.findtext("released"),
                "notes": elem.findtext("notes"),
                "data_quality": elem.findtext("data_quality"),
                "master_id": ReleaseParser._get_attribute(elem.find("master_id"), "is_main_release"),
                "tracklist": ReleaseParser._parse_tracklist(elem),
                "videos": ReleaseParser._parse_videos(elem),
                "companies": ReleaseParser._parse_companies(elem),
                "images": ReleaseParser._parse_images(elem),
            }
        except Exception as e:
            logging.error(f"Error parsing release: {e}")
            return {}

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
