import re
from urllib.parse import urljoin
from datetime import datetime , timedelta
import cloudscraper
from bs4 import BeautifulSoup

def get_matches():
    scraper = cloudscraper.create_scraper()
    base_url = 'https://csgostats.gg/match'
    html = scraper.get(base_url).text
    soup = BeautifulSoup(html , 'html.parser')

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


def parse_team_round_score(round_info):
     for team_info in round_info.find_all("div" , class_ = re.compile("team-")):
        team_assigned = team_info.attrs["class"][1].split('-')[-1]
        team_survivors = int(team_info.text.strip())
        team_victorious = bool(len(team_info.attrs["class"]) == 3)
        
        yield {"team_assigned" : team_assigned,
               "survivors": team_survivors,
               "victorious" : team_victorious}
        
        
def parse_monetary_stats(table):
        for val in table.find_all("div" , style = re.compile("float:left; width:16%; font-size:12px;")):
            yield val.text.strip('\n').strip()
          
        
def parse_kill_death_events(table) -> dict:
    for event in table.find_all("div" , class_ = "tl-inner"):
        try:
            eventTimestamp = event.find("span" , title = re.compile("Tick")).text
            actors = event.find_all("span" , class_ = re.compile("team-"))

            
            weapon = event.find("img" , src = re.compile("weapons")).attrs["title"]

            killers = list(map(lambda x : x.text , actors[:-1]))
            deceased = actors[-1].text

            is_headshot = event.find("img" , alt = "Headshot")
            wallbang = event.find("img" , alt = "Wallbang")

            yield {"eventTimestamp" : eventTimestamp,
                    "weapon" : weapon,
                    "killers" : killers,
                    "deceased": deceased,
                    "headshot" : bool(is_headshot),
                    "wallbang" : bool(wallbang)
                  }
        except AttributeError as e:
            yield {"eventTimestamp" : eventTimestamp,
                   "weapon" : "world",
                    "deceased" : actors[0].text
                    }
            
        
def parse_match_rounds(soup) -> dict:
    for idx , round_ in enumerate(soup.find_all("div" , style = re.compile("padding:7px 0;"))):
        cur_round = {f"round_{idx+1}" : {"team_0" : {} , "team_1" : {} , "kills" : []} }
        round_info = round_.find("div" , class_ = "round-score")
        gen = parse_team_round_score(round_info)
        cur_round[f"round_{idx+1}"]["team_0"] = next(gen)
        cur_round[f"round_{idx+1}"]["team_1"] = next(gen)

        #print(len(round_.find_all("div" , class_ = re.compile("round-info-side"))))

        monetary_table , kill_death_table = round_.find_all("div" , class_ = "round-info-side")

        ## Parsing monetary table
        gen = parse_monetary_stats(monetary_table)

        ##Equipment Value
        cur_round[f"round_{idx+1}"]["team_0"].update({"equipmentValue" : next(gen) })
        cur_round[f"round_{idx+1}"]["team_1"].update({"equipmentValue" : next(gen) })

        ##Cash
        cur_round[f"round_{idx+1}"]["team_0"].update({"cash" : next(gen)})
        cur_round[f"round_{idx+1}"]["team_1"].update({"cash" : next(gen)})

        ##Cash Spent
        cur_round[f"round_{idx+1}"]["team_0"].update({"cashSpent" : next(gen)})
        cur_round[f"round_{idx+1}"]["team_1"].update({"cashSpent" : next(gen)})

        ##Parsing Kill/Death tables
        gen = parse_kill_death_events(kill_death_table)

        for event in gen:
            cur_round[f"round_{idx+1}"]["kills"].append(event)
        yield cur_round

    

def get_match_round_data(matchId : int):
    scraper = cloudscraper.create_scraper()
    base_url = 'https://csgostats.gg/match'

    html = scraper.get( base_url + f"/{matchId}#/rounds").text
    soup = BeautifulSoup(html , 'html.parser')

    return [round_ for round_ in parse_match_rounds(soup)]

def parse_player_ids(soup) -> dict:
    for player in soup.find_all(lambda tag : tag.name == "a" \
                            and tag.has_attr("href") \
                            and tag.has_attr("class") \
                            and "player-link" in tag.attrs["class"] \
                            and "player" in tag.attrs["href"]):
        yield { player.attrs["href"].split('/')[-1] : player.text.strip('\n') }

def get_player_ids(matchId : int):
    scraper = cloudscraper.create_scraper()
    base_url = 'https://csgostats.gg/match'

    html = scraper.get( base_url + f"/{matchId}").text
    soup = BeautifulSoup(html , 'html.parser')
    return [player for player in parse_player_ids(soup)]

