from fastapi import FastAPI
from typing import Dict , Union , Optional , List
import pandas as pd
from tensorflow.keras.models import load_model
from csgo.ml.preprocessing import preprocess_features
from csgo.scraper.data_scraper import scrape_matches , scrape_match_round_data , scrape_player_ids
from csgo.utils.connectors import fetch_leaderboard
import os

app = FastAPI()
model_path = "../../notebooks/csgo_tf"
app.state.model = load_model(model_path)

@app.get('/')
def home() -> Dict[str,str]:
    return {"CSGO API": "Made by NChan"}

@app.get('/match')
def matches(limit : Optional[int] = None , rank : Optional[int] = None) -> List:
    """Returns live matches"""
    matches = []
    for match in scrape_matches():
        matches.append(match)

        if limit and len(matches) >= limit:
            break

    return list(filter(lambda match : match.get("rankNum") == rank , matches)) if rank else matches


@app.get('/match/{matchId}/players')
def players(matchId : int) -> Dict:
    player_ids = scrape_player_ids(matchId)
    team_0 = player_ids[:5]
    team_1 = player_ids[5:]

    team_0_players = {}
    for player_info in team_0:
        team_0_players = { **team_0_players , **player_info}

    team_1_players = {}
    for player_info in team_1:
        team_1_players = { **team_1_players , **player_info}

    return {"match" : matchId , 
            "team_0" : team_0_players , 
            "team_1" : team_1_players
            }


@app.get('/players/{playerId}')
def get_player_info(playerId : int) -> Dict:
    return {"message" : "Under Construction!"}


@app.get('/leaderboard')
def leaderboard(page : Optional[int] = 1) -> List[Dict]:
    leaderboard_entries = fetch_leaderboard(os.environ.get("DB_NAME") , page = page)
    return leaderboard_entries
    

@app.get('/match/{matchId}/rounds')
def match(matchId : int , round_index : Optional[int] = None) -> Dict:
    round_data = scrape_match_round_data(matchId)
    try:
        if round_index:
            round_data = round_data[round_index]
    except IndexError:
        pass
    finally:
        return {"match" : matchId , "rounds" : round_data }


@app.get('/about')
def about():
    return {"Secret Portal": "Cookie!"}


@app.post('/predict')
def predict(game_stats : Dict[str , Union[float,str,int,bool]]) -> Dict:
    X_pred = pd.DataFrame(game_stats , index = [0])
    X_pred_trans = preprocess_features(X_pred)
    prediction = app.state.model.predict(X_pred_trans)
    return {"CT win": float(prediction[0][0]),
            "T win": 1 - float(prediction[0][0])}
    

