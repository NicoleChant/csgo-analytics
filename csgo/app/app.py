from fastapi import FastAPI
from typing import Dict , Union , Optional
from tensorflow.keras.models import load_model
import pandas as pd
from csgo.ml.preprocessing import preprocess_features
from csgo.scraper.data_scraper import get_matches

app = FastAPI()
model_path = "../../notebooks/csgo_tf"
app.state.model = load_model(model_path)

@app.get('/')
def home():
    return {"CSGO API": "Made by NChan"}

@app.get('/matches')
def matches(limit : Optional[int] = None):
    """Returns live matches"""
    matches = []
    for match in get_matches():
        matches.append(match)

        if limit and len(matches) >= limit:
            break
    return matches


@app.get('/match/{matchId}')
def match(matchId : int):
    return {"match": matchId}


@app.post('/predict')
def predict(game_stats : Dict[str , Union[float,str,int,bool]]):
    X_pred = pd.DataFrame(game_stats , index = [0])
    X_pred_trans = preprocess_features(X_pred)
    prediction = app.state.model.predict(X_pred_trans)
    return {"CT win": float(prediction[0][0]),
            "T win": 1 - float(prediction[0][0])}
    