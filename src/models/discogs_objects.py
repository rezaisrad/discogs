from urllib.parse import urlencode
from bs4 import BeautifulSoup
import logging
from datetime import datetime
import re


class DiscogsPageBase:
    def __init__(self, url, session_manager):
        self.url = url
        self.session_manager = session_manager
        self.session, self.proxy = self.session_manager.get_session() 
    
    def fetch_page_content(self):
        logging.debug(f"Fetching page content for {self.url}")
        try:
            response = self.session.get(self.url)
            response.raise_for_status()
            return response.text
        except Exception as e:
            logging.error(f"Failed to fetch page content for {self.url}: {e}")
            return None

class DiscogsRelease(DiscogsPageBase):
    def __init__(self, release_id, session_manager):
        url = f'https://www.discogs.com/release/{release_id}'
        super().__init__(url, session_manager)
        self.release_id = release_id
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

            if key == 'Last Sold':
                value = safe_parse_date(value_element.text.strip())

            elif key in ['Have', 'Want', 'Ratings']:
                value = safe_parse_int(value_element.text.strip())

            elif key in ['Avg Rating', 'Low', 'Median', 'High']:
                value_text = value_element.text.strip()
                if key == 'Avg Rating':
                    value = safe_parse_float(value_text.split('/')[0].strip())
                else:
                    value = safe_parse_price(value_text)[1]
            else:
                value = value_element.strip()

            stats[key] = value

        return stats
    
class DiscogsStatsPage(DiscogsPageBase):
    def __init__(self, release_id, session_manager):
        url = f'https://www.discogs.com/release/stats/{release_id}'
        super().__init__(url, session_manager)
        self.release_id = release_id
        self.stats = None
        self.members_have = [] 
        self.members_want = []
        
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
    def __init__(self, url, session_manager, query_params=None):
        if query_params:
            query_string = urlencode(query_params)
            self.url = f"{url}?{query_string}"
        else:
            self.url = url
        super().__init__(url, session_manager)
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
        item['ships_from'] = ships_from_span.next_sibling.strip() if ships_from_span and ships_from_span.next_sibling else None


        # Price
        price_cell = row.find('td', class_='item_price')
        price_span = price_cell.find('span', class_='price')
        if price_span:
            price_text = price_span.text.strip()
            item['currency'], item['price'] = safe_parse_price(price_text)
        else:
            item['price'] = None
            item['currency'] = None
            
        return item
    
class DiscogsSellerPage(DiscogsSellerPageBase):
    def __init__(self, username, session_manager, query_params=None):
        url = f"https://www.discogs.com/seller/{username}/profile"
        super().__init__(url, session_manager, query_params)
        self.username = username
        self.stats = None

class DiscogsSellerPageRelease(DiscogsSellerPageBase):
    def __init__(self, release_id, session_manager, query_params=None):
        url = f"https://www.discogs.com/sell/release/{release_id}"
        super().__init__(url, session_manager, query_params)
        self.release_id = release_id
        self.stats = None
        
        
def safe_parse_int(value_str):
    """Safely parses integers, accounting for '--' or empty strings."""
    try:
        return int(value_str.replace(',', '')) if value_str.strip() and value_str != '--' else None
    except ValueError:
        return None

def safe_parse_float(value_str):
    """Safely parses floats, accounting for '--' or empty strings."""
    try:
        return float(value_str) if value_str.strip() and value_str != '--' else None
    except ValueError:
        return None

def safe_parse_date(date_str):
    """Safely parses dates, accounting for 'Never'."""
    try:
        return datetime.strptime(date_str, '%b %d, %Y').date() if date_str.strip().lower() != 'never' else None
    except ValueError:
        return None

def safe_parse_price(price_text):
    """Safely parses price text to extract currency and value, handling edge cases."""
    match = re.match(r'([^\d]*)(\d+[\.,]?\d*)', price_text.replace(',', '.'))
    if match:
        currency = match.group(1).strip() if match.group(1) else None
        try:
            price = float(match.group(2)) if match.group(2) else None
        except ValueError:
            price = None
        return currency, price
    return None, None
