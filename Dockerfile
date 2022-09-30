FROM python:3.8.6-buster

COPY csgo src/csgo
COPY requirements.txt src/requirements.txt
COPY setup.py src/setup.py
COPY models src/models
WORKDIR src

RUN pip install --upgrade pip
RUN pip install .

CMD uvicorn csgo.app.app:app --reload --host $PORT

