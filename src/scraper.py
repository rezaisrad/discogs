from urllib.parse import urlencode
import cloudscraper
from bs4 import BeautifulSoup
import logging
from datetime import datetime
import re
import time 
from functools import wraps


def rate_limited(method):
    """Decorator to enforce rate limiting on methods."""
    @wraps(method)
    def wrapper(self, *args, **kwargs):
        if not hasattr(self, '_last_call_time'):
            self._last_call_time = 0.0

        self.elapsed = time.time() - self._last_call_time
        max_per_minute = getattr(self, 'max_requests_per_minute', 25)  # Default to 25 if not set
        min_interval = 60.0 / float(max_per_minute)
        wait_required = min_interval - self.elapsed

        if wait_required > 0:
            time.sleep(wait_required)

        self._last_call_time = time.time()
        return method(self, *args, **kwargs)
    return wrapper

class DiscogsPageBase:
    def __init__(self, url, max_requests_per_minute=25):
        self.url = url
        self.scraper = self.create_scraper()
        self.max_requests_per_minute = max_requests_per_minute

    @staticmethod
    def create_scraper():
        return cloudscraper.create_scraper()
    
    @rate_limited
    def fetch_page_content(self):
        """Fetches page content with rate limiting."""
        try:
            response = self.scraper.get(self.url)
            response.raise_for_status()  # Raises an HTTPError for bad responses
            return response.text
        except Exception as e:
            logging.error(f"Failed to fetch page content for {self.url}: {e}")
            return None

class DiscogsRelease(DiscogsPageBase):
    def __init__(self, release_id, max_requests_per_minute=25):
        self.release_id = release_id
        self.url = f'https://www.discogs.com/release/{release_id}'
        super().__init__(self.url, max_requests_per_minute)
        self.stats = None
    
    def fetch_and_parse(self):
        html_content = self.fetch_page_content()
        if html_content:
            self.stats = self.parse_stats(html_content)
    
    def parse_stats(self, html_content):
        soup = BeautifulSoup(html_content, 'html.parser')
        stats_section = soup.find('section', id='release-stats')
        if not stats_section:
            logging.warning("Stats section not found in HTML content")
            return {}
        stats = {}

        for li in stats_section.find_all('li'):
            key_element = li.find('span')
            key = key_element.text.strip(':').strip()
            value_element = key_element.next_sibling

            if key in ['Last Sold']:
                # Convert date to datetime object
                value = datetime.strptime(value_element.text.strip(), '%b %d, %Y').date()
            elif key in ['Have', 'Want', 'Ratings']:
                elem = value_element.text.strip()
                value = int(elem) if len(elem) > 0 else None
            elif key in ['Avg Rating', 'Low', 'Median', 'High']:
                # Extract text from the span element and handle conversion
                value_text = value_element.text.strip()
                if key == 'Avg Rating':
                    # Capture only the numerator from the rating and convert to float
                    value = float(value_text.split('/')[0].strip()) if '/' in value_text else None
                else:
                    # Remove the $ symbol for price fields, convert to float or set to None if not a valid number
                    value_text = value_text.replace('$', '').strip()
                    value = float(value_text) if value_text.replace('.', '', 1).isdigit() else None
            else:
                value = value_element.strip()

            stats[key] = value

        return stats
    
class DiscogsStatsPage(DiscogsPageBase):
    def __init__(self, stats_id, max_requests_per_minute=25):
        self.stats_id = stats_id
        self.url = f"https://www.discogs.com/release/stats/{stats_id}"
        super().__init__(self.url, max_requests_per_minute)
        self.members_have = None
        self.members_want = None

    def fetch_and_parse(self):
        html_content = self.fetch_page_content()
        if html_content:
            self.parse_members_data(html_content)
    
    def parse_members_data(self, html_content):
        soup = BeautifulSoup(html_content, 'html.parser')
        stats_groups = soup.find_all('div', class_='release_stats_group')

        if len(stats_groups) >= 2:
            self.members_have = self.parse_members(stats_groups[1])
            if len(stats_groups) >= 3:
                self.members_want = self.parse_members(stats_groups[2])

    def parse_members(self, stats_group):
        members_list = stats_group.find('ul', role='list').find_all('li')
        return [member.find('a').text.strip() for member in members_list]
    

class DiscogsSellerPageBase(DiscogsPageBase):
    def __init__(self, base_url, query_params=None, max_requests_per_minute=25):
        if query_params:
            query_string = urlencode(query_params)
            url = f"{base_url}?{query_string}"
        else:
            url = base_url
        super().__init__(url, max_requests_per_minute)
        self.items_for_sale = []

    def fetch_and_parse(self):
        html_content = self.fetch_page_content()
        if html_content:
            self.items_for_sale = self.parse_items_for_sale(html_content)

    def parse_items_for_sale(self, html_content):
        soup = BeautifulSoup(html_content, 'html.parser')
        table = soup.find('table', class_='table_block mpitems push_down table_responsive')
        items = []

        for row in table.find('tbody').find_all('tr', class_='shortcut_navigable'):
            item = self.parse_item_row(row)
            items.append(item)
        
        return items
    
    def parse_item_row(self, row):
        item = {}
        # Parsing image and community data
        item_picture_cell = row.find('td', class_='item_picture')
        image_tag = item_picture_cell.find('img')
        item['image_url'] = image_tag['src'] if image_tag else None

        # Community ratings, have, want
        community_data = item_picture_cell.find('div', class_='community_data_text')
        if community_data:
            rating_strong = community_data.find('strong')
            item['rating'] = float(rating_strong.text) if rating_strong else None
            community_results = community_data.find_all('div', class_='community_result')
            item['have'] = int(community_results[0].find('span', class_='community_number').text.strip()) if len(community_results) > 0 else None
            item['want'] = int(community_results[1].find('span', class_='community_number').text.strip()) if len(community_results) > 1 else None

        # Description, label, cat#, media condition, seller info, price
        item_description_cell = row.find('td', class_='item_description')
        title_link = item_description_cell.find('a', class_='item_description_title')
        item['title'] = title_link.text if title_link else None
        label_and_cat = item_description_cell.find('p', class_='label_and_cat')
        item['label'] = label_and_cat.find('a').text if label_and_cat and label_and_cat.find('a') else None
        item['catno'] = label_and_cat.find('span', class_='item_catno').text if label_and_cat and label_and_cat.find('span', class_='item_catno') else None
        
        # Extracting Media Condition
        # Find all spans with "mplabel" class within the item description cell
        mplabel_spans = item_description_cell.find_all('span', class_='mplabel')

        # If mplabel spans are found, proceed to get the media condition from the last mplabel span's next sibling
        if mplabel_spans:
            last_mplabel_span = mplabel_spans[-1]  # Last element of mplabel spans
            media_condition_span = last_mplabel_span.find_next_sibling()

            if media_condition_span:
                media_condition = media_condition_span.text.strip().split('\n')[0]
                item['media_condition'] = media_condition

                # Attempting to extract description from a possible tooltip within the media condition span
                description_span = media_condition_span.find('span', {'class': 'has-tooltip'})
                if description_span:
                    description_text = description_span.get('title') or description_span.find('span', {'class': 'tooltip-inner'}).text.strip()
                    item['media_condition_description'] = description_text
                else:
                    item['media_condition_description'] = None
            else:
                item['media_condition'] = None
                item['media_condition_description'] = None
        else:
            item['media_condition'] = None
            item['media_condition_description'] = None

        # Seller info
        seller_info_cell = row.find('td', class_='seller_info')
        seller_link = seller_info_cell.find('a')
        item['seller'] = seller_link.text if seller_link else None
        seller_rating_span = seller_info_cell.find('span', class_='star_rating')
        if seller_rating_span:
            rating_match = re.search(r'(\d+(\.\d+)?)', seller_rating_span['alt'])
            item['seller_rating'] = float(rating_match.group(1)) if rating_match else None
        else:
            item['seller_rating'] = None
        ships_from_span = seller_info_cell.find('span', text='Ships From:')
        item['ships_from'] = ships_from_span.next_sibling.strip() if ships_from_span else None

        # Price
        price_cell = row.find('td', class_='item_price')
        price_span = price_cell.find('span', class_='price')
        if price_span:
            price_text = price_span.text.strip()
            # Find the index of the first digit in the price text
            match = re.search(r'\d', price_text)
            if match:
                first_digit_index = match.start()
                item['currency'] = price_text[:first_digit_index]
                item['price'] = float(price_text[first_digit_index:])
            else:
                item['price'] = None
                item['currency'] = None
        else:
            item['price'] = None
            item['currency'] = None
            
        return item

class DiscogsSellerPage(DiscogsSellerPageBase):
    def __init__(self, username, query_params=None, max_requests_per_minute=25):
        base_url = f"https://www.discogs.com/seller/{username}/profile"
        super().__init__(base_url, query_params, max_requests_per_minute)

class DiscogsSellerPageRelease(DiscogsSellerPageBase):
    def __init__(self, release_id, query_params=None, max_requests_per_minute=25):
        base_url = f"https://www.discogs.com/sell/release/{release_id}"
        super().__init__(base_url, query_params, max_requests_per_minute)