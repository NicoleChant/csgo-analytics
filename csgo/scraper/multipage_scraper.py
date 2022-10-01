import concurrent.futures
import os
from termcolor import colored
from csgo.scraper.data_scraper import scrape_leaderboard
from csgo.utils.connectors import * 
from pydantic import BaseModel
import time

db_name = os.environ.get("DB_NAME")

def store_to_db(job : int):
    leaderboard = scrape_leaderboard(page = job)
    try:
        columns = ",".join(leaderboard[0].keys())
        placeholders = ",".join(["?"]*len(leaderboard[0]))
        query = f"""INSERT INTO leaderboard ({columns}) 
                    VALUES ({placeholders});"""
        with SQLconnector(get_db_name(db_name)) as curs:
            for row in leaderboard:
                curs.execute(query, list(row.values()))
            return leaderboard
    except Exception as error_message:
        print(colored(error_message,"red"))
        return False

def store_to_gbq() -> bool:
    try:
        total_pages = int(os.environ.get("TOTAL_PAGES"))
        for page in range(1,total_pages,1):
            leaderboard = fetch_leaderboard(os.environ.get("DB_NAME") , page = page)
            print(colored("Added new leaderboard to GBQ!", "green"))
        return True
    except Exception as error_message:
        print(colored("Failed to store data to GBQ." , "red"))
        return False

def scrape_many(jobs , drop : bool = False , create : bool = False , verbose : bool = False):
    if drop:
        drop_table(db_name = db_name , table_name = "leaderboard")

    if create:
        create_leaderboard_table(db_name = db_name)
    print(colored(f"Detected CPUs: {os.cpu_count()}" , "green"))
    print(colored(f"Total jobs detected: {len(jobs)}." , "green"))
    print("Initializing scraping processes...")

    tik = time.perf_counter()
    with concurrent.futures.ProcessPoolExecutor() as executor:
        scraped_pages = executor.map(store_to_db, jobs)

        # for scraped_page in scraped_pages:
        #     print(scraped_page)
    tak = time.perf_counter()
    if verbose:
        query_db(db_name , "leaderboard")

    print(colored(f"Process completed within {tak-tik : .2f} second(s)!" , "green"))

def main():
    """Testing"""
    jobs = range(95,96,1)
    scrape_many(jobs)

if __name__ == "__main__": main()