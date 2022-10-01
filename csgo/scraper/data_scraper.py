import re
from urllib.parse import urljoin
from datetime import datetime , timedelta
import cloudscraper
from bs4 import BeautifulSoup


def get_html(url : str , **params):
    scraper = cloudscraper.create_scraper()
    html = scraper.get(url , params = params).text
    return BeautifulSoup( html , 'html.parser')

def get_matches():
    base_url = 'https://csgostats.gg/match'
    soup = get_html(base_url)

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
    base_url = 'https://csgostats.gg/match'
    soup = get_html( base_url + f"/{matchId}#/rounds")
    return [round_ for round_ in parse_match_rounds(soup)]


def parse_player_ids(soup) -> dict:
    for player in soup.find_all(lambda tag : tag.name == "a" \
                            and tag.has_attr("href") \
                            and tag.has_attr("class") \
                            and "player-link" in tag.attrs["class"] \
                            and "player" in tag.attrs["href"]):
        yield { player.attrs["href"].split('/')[-1] : player.text.strip('\n') }


def get_player_ids(matchId : int):
    base_url = 'https://csgostats.gg/match'
    soup = get_html( base_url + f"/{matchId}")
    return [player for player in parse_player_ids(soup)]


def parse_leaderboard_rows(soup):
    for row in soup.find_all("div" , onclick = re.compile(r"/player/\d+")):
        playerId = re.findall( r"/player/(\d+)" , row.attrs['onclick'])[0]
        playerRanking = row.select_one(":nth-child(1)").text.strip("\n").strip()
        playerName = row.select_one(":nth-child(2)").text.strip("\n").strip()

        #weapons = row.find_all("img" , src = re.compile("/weapons/"))
        #primaryWeapon  , secondaryWeapon = weapons[0].attrs["title"] , weapons[1].attrs["title"]
        
        characteristics = ["primaryWeapon" , "secondaryWeapon" , "KD", "HS" , "WinRate", "1vX" , "Rating"]
        stats = row.find_all("div" ,style = re.compile("float:left; width:\d{2}%;text-align:center;"))

        #parsing players weapons
        primaryWeapon = stats[0].find("img" , src = re.compile("/weapons/")).attrs["title"]
        secondaryWeapon = stats[1].find("img" , src = re.compile("/weapons/")).attrs["title"]

        #parsing players kills, deaths, kill/death ratio
        kd , _ = stats[2].text.strip("\n").split("\n")
        kd = float(kd.strip())
        kills , deaths = _.split("/")
        kills , deaths = int(kills.strip()) , int(deaths.strip())

        #parsing players headshots
        headshots = round(int(stats[3].text.strip("%"))/100 , 2)

        #parsing players win rate
        winRate = round(int(stats[4].text.strip("\n").strip().strip("%"))/100 , 2)

        #parsing players duels vs. many players
        vX = int(stats[5].text.strip())

        #parsing player's total rating
        rating = float(stats[6].text.strip())
        
        yield {"playerId" : playerId ,
               "playerRanking" : playerRanking,
               "playerName" : playerName,
               "primaryWeapon" : primaryWeapon,
               "secondaryWeapon" : secondaryWeapon,
               "kd" : kd , 
               "kills" : kills,
               "deaths" : deaths ,
               "headshots" : headshots ,
               "winRate" : winRate,
               "1vX" : vX ,
               "rating": rating}


def get_leaderboard(page : int = 2):
    base_url = "https://csgostats.gg/leaderboards"
    soup = get_html( base_url , page = page)
    for row in parse_leaderboard_rows(soup):
        print(row , flush = True)


def main():
    """For testing purposes"""
    leaderboard = get_leaderboard()

if __name__ == "__main__": main()
