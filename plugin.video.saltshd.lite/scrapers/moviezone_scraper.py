"""
    SALTS XBMC Addon
    Copyright (C) 2014 tknorris

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
import scraper
import urlparse
import urllib
import re
from salts_lib import scraper_utils
from salts_lib import kodi
from salts_lib import log_utils
from salts_lib import dom_parser
from salts_lib.constants import VIDEO_TYPES
from salts_lib.constants import FORCE_NO_MATCH
from salts_lib.constants import QUALITIES

BASE_URL = 'http://moviezone.ch'

class MovieZone_Scraper(scraper.Scraper):
    base_url = BASE_URL

    def __init__(self, timeout=scraper.DEFAULT_TIMEOUT):
        self.timeout = timeout
        self.base_url = kodi.get_setting('%s-base_url' % (self.get_name()))

    @classmethod
    def provides(cls):
        return frozenset([VIDEO_TYPES.MOVIE])

    @classmethod
    def get_name(cls):
        return 'MovieZone'

    def resolve_link(self, link):
        return link

    def format_source_label(self, item):
        label = '[%s]' % (item['quality'])
        if '3D' in item and item['3D']:
            label += ' (3D)'
        if 'format' in item:
            label += ' (%s)' % (item['format'])
        label += ' %s' % (item['host'])
        return label

    def get_sources(self, video):
        source_url = self.get_url(video)
        sources = []
        if source_url and source_url != FORCE_NO_MATCH:
            url = urlparse.urljoin(self.base_url, source_url)
            html = self._http_get(url, cache_limit=8)
            for source in dom_parser.parse_dom(html, 'source', ret='src'):
                host = self._get_direct_hostname(source)
                if host == 'gvideo':
                    quality = scraper_utils.gv_get_quality(source)
                else:
                    quality = QUALITIES.HIGH
                source = {'multi-part': False, 'url': source, 'host': host, 'class': self, 'quality': quality, 'views': None, 'rating': None, 'direct': True}
                sources.append(source)

        return sources

    def search(self, video_type, title, year, season=''):
        results = []
        search_url = urlparse.urljoin(self.base_url, '/?s=%s' % (urllib.quote_plus(title)))
        html = self._http_get(search_url, cache_limit=8)
        for item in dom_parser.parse_dom(html, 'div', {'class': 'item'}):
            post_type = dom_parser.parse_dom(item, 'div', {'class': 'typepost'})
            if post_type and post_type[0] == 'tv': continue
            match = re.search('href="([^"]+)', item)
            match_title = dom_parser.parse_dom(item, 'span', {'class': 'tt'})
            year_frag = dom_parser.parse_dom(item, 'span', {'class': 'year'})
            if match and match_title:
                url = match.group(1)
                match_title = match_title[0]
                match = re.search('(.*?)\s+\((\d{4})\)', match_title)
                if match:
                    match_title, match_year = match.groups()
                else:
                    match_title = match_title
                    match_year = ''
                
                if year_frag:
                    match = re.search('(\d{4})', year_frag[0])
                    if match:
                        match_year = match.group(1)

                if not year or not match_year or year == match_year:
                    result = {'title': scraper_utils.cleanse_title(match_title), 'year': match_year, 'url': scraper_utils.pathify_url(url)}
                    results.append(result)

        return results
