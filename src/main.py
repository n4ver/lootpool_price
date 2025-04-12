import requests
import json
import os.path
import csv
import logging


logger = logging.getLogger(__name__)


API_URI = r"https://nori.fish"
JSON_SAVE_LOCATION = r"./lootpool.json"
PRICELIST = r"./mythic_prices.csv"


def save_response(response: str) -> None:
    with open(JSON_SAVE_LOCATION, "w+", encoding="utf-8") as f:
        json.dump(response, f, ensure_ascii=False, indent=4)


def download_lootpool():
    print("Local lootpool file does not exist. Grabbing from Nori API...")
    print("NORI  | Getting Token...")

    r = requests.get(f"{API_URI}/api/tokens")
    cookies = r.cookies
    csrf_token = cookies.get('csrf_token')

    print(rf"NORI  | Getting response from {API_URI}/api/lootpool...")

    response = requests.get(rf"{API_URI}/api/lootpool",cookies=cookies,headers={"X-CSRF-Token":csrf_token})
    if response.status_code == 200:
        json_response = json.loads(response.content)
        save_response(json_response)
        print(f"NORI  | Response Saved at `{JSON_SAVE_LOCATION}`.")
    else:
        print(f"ERROR | Status Code {response.status_code}")


def convert_to_denominations(price):
    stx_leftover = price % 262144
    stx = (price - stx_leftover) / 262144
    le_leftover = stx_leftover % 4096
    le = (price - le_leftover) / 4096
    if stx >= 1:
        return f"{stx:.0f}stx, {stx_leftover / 4096:.2f}le"
    else:
        eb_leftover = le_leftover % 64 
        eb = (le_leftover - eb_leftover) / 64
        return f"{le:.0f}le, {eb:.0f}eb, {eb_leftover:.0f}e"


def get_mythic_price(mythic):
    with open(PRICELIST) as f:
        pricereader = csv.reader(f,delimiter=",")
        for row in pricereader:
            if row[0] == mythic:
                return int(row[1])
    return -1

def get_mythics():
    weekly_lootpool_averages = {}
    print("Getting Mythics...")
    with open(JSON_SAVE_LOCATION) as f:
        lootpool = json.load(f)
        f.close()
    for location_loot in lootpool['Loot']:
        location_prices = []
        print(f"{location_loot } Lootpool:")
        location_mythics = lootpool['Loot'][location_loot]['Mythic']
        for mythic in location_mythics:
            mythic_price = get_mythic_price(mythic)
            if mythic_price < 0:
                logger.warning(f"ERROR | Mythic {mythic} not in pricelist")
            else:
                location_prices.append(mythic_price)
                #print(f"{mythic} Price: {convert_to_denominations(mythic_price)} (Unidentified)")
        average_location_price = sum(location_prices)/len(location_prices)
        weekly_lootpool_averages[location_loot] = average_location_price
        print(f"Average price for {location_loot} mythics (Excluding Shinies) is {convert_to_denominations(average_location_price)}")

    highest_avg = 0
    highest_avg_location = ""
    for location, avg_price in weekly_lootpool_averages.items():
        if avg_price > highest_avg:
            highest_avg = avg_price
            highest_avg_location = location

    print("Based on the average mythic price for this week's lootpool,")
    
    print(f"It is recommended that you run {highest_avg_location} with average mythic price of {convert_to_denominations(highest_avg)}.")


def main():
    logging.basicConfig(filename='pricecheck.log', level=logging.INFO)
    logger.info('Started logging...')


    if not os.path.isfile(JSON_SAVE_LOCATION):
        download_lootpool()
    
    get_mythics()

if __name__ == "__main__":
    main()