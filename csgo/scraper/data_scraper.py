import re
from urllib.parse import urljoin
from datetime import datetime , timedelta
import cloudscraper
from bs4 import BeautifulSoup

def get_matches():
    scraper = cloudscraper.create_scraper()
    base_url = 'https://csgostats.gg/match'
    html = scraper.get(base_url).text

    for match in soup.select('tr[class="p-row js-link"]'):
    
        match_endpoint = re.findall(r'/match/(\d+)' , match.attrs['onclick'])[0]
        rank = match.find('img' , src = re.compile(r'ranks')).attrs["alt"]
        rankNum = match.find('img' , src = re.compile(r'ranks')).attrs['src'].split('/')[-1].strip('.png')
        upload_time_elapsed = match.find('td' , class_ = 'nowrap').text.strip()
        upload_time = datetime.now() - timedelta(minutes = int(upload_time_elapsed.split(' ')[0]))
        maps = match.find('img' , src = re.compile('maps')).attrs["alt"]
        yield dict( matchId = match_endpoint,
                    rank = rank,
                    rankNum = rankNum,
                    date = upload_time,
                    map = maps)