from google.cloud import bigquery
import os
from termcolor import colored
import argparse
import pandas as pd

def get_all_gbq_data(chunk_size) -> pd.DataFrame:
    offset = 0
    cnt = 0
    while True:
        offset += int(chunk_size)
        cnt += 1
        if offset > int(os.environ.get("TOTAL_ROWS")):
            break
        
        print(f"Fetching chunk {cnt}...")
        yield get_data_from_gbq(chunk_size , offset)

def create_dataset():
    dataset = f"{os.environ.get('GCP_PROJECT')}.{os.environ.get('DATASET')}"
    client = bigquery.Client()
    dataset = bigquery.Dataset(dataset)
    dataset.location = os.environ.get("LOCATION")
    dataset = client.create_dataset(dataset , timeout = 30)
    print(colored(f"Created dataset {dataset.dataset_id} in project {client.project}" , "green"))

def create_table(table_id , schema):
    client = bigquery.Client()
    if table_exists(table_id , client = client):
        return
    print(colored("⚙️ Constructing big query table...","blue"))
    table = bigquery.Table(table_id, schema=schema)
    table = client.create_table(table)
    print(colored(f"✅ Succesfully created big query table ({table.project},{table.dataset_id},{table.table_id})","green"))

def store_data_to_gbq():
    csgo_data = pd.read_csv(os.environ.get("DATA_PATH"))
    table_dest = f"{os.environ.get('GCP_PROJECT')}.{os.environ.get('DATASET')}.csgo_round_snapshots"
    csgo_data.to_gbq(table_dest)
    print(colored("✅ Succesfully stored data to big query table","green"))

def get_data_from_gbq(chunk_size : int , offset : int) -> pd.DataFrame:
    table_dest = f"{os.environ.get('GCP_PROJECT')}.{os.environ.get('DATASET')}.csgo_round_snapshots"
    print(table_dest)
    csgo_data = pd.read_gbq(f"SELECT * FROM {table_dest} LIMIT {chunk_size} OFFSET {offset}")
    return csgo_data

def list_datasets():
    client = bigquery.Client()
    datasets = list(client.list_datasets())

    project = client.project

    if datasets:
        print(f"In project {project} found datasets:")
        for dataset in datasets:
            print(f"{dataset.dataset_id}")
    else:
        print(f"{project=} does not have any datasets...")

if __name__ == "__main__":
    #create_dataset()
    #list_datasets()
    #store_data_to_gbq()
    df = get_data_from_gbq()
    print(df)