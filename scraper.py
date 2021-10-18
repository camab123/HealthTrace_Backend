import aiohttp
import asyncio
import json
import os
from aiohttp import ClientSession
import pandas as pd
import csv
import time
from urllib.error import HTTPError
import sys
import requests
from datetime import datetime

from requests import sessions
BASE_URL = "https://www.govdeals.com/index.cfm?fa=Main.AdvSearchResultsNew&searchPg=Category&additionalParams=true&sortOption=ad&timing=BySimple&timingType=&category="
category_ids = {'Agriculture Equip/Commodities': '05', 'Aircraft': '233', 'Aircraft Parts and Components': '234', 'Alarm and Fire Protection Systems': '62', 'All Terrain Vehicles': '94G', 'All Vehicles (Restricted Vehicles)': '94P', 'Ambulance/Rescue': '94J', 'Animal Equipment, Cages and Feed': '16', 'Arts and Crafts': '08', 'Asphalt Equipment': '120', 'Audio/Visual Equipment': '22', 'Automobiles': '94A', 'Automobiles (Classic/Custom)': '94O', 'Aviation': '03', 'Aviation Ground Support Equipment': '235', 'Bags, All Types': '10', 'Barber and Beauty Shop Equipment': '11', 'Barrels and Drums': '12', 'Batteries, All Types': '15', 'Bicycles': '143', 'Boats, Marine Vessels and Supplies': '17', 'Books/Manuals': '18', 'Builders Supplies': '19', 'Buses, Transit and School': '94H', 'Cafeteria and Kitchen Equipment': '21', 'Chemicals, All Types': '24', 'Clocks': '25', 'Clothing/Linens': '26', 'Collectibles': '149', 'Commercial Catering and Restaurant': '287', 'Commercial Furnaces': 'CF', 'Commodities / General Merchandise': '150', 'Communication/Electronic Equipment': '28', 'Compressor Parts and Accessories': '116', 'Compressors': '159', 'Computer Hardware': '50', 'Computers, Parts and Supplies': '29', 'Confiscated/Forfeited/Personal Property': '30', 'Consumer Kitchen': '216', 'Containers - Storage/Shipping': '31', 'Cranes': '152', 'Dental Equipment and Supplies': '300', 'Displays and Exhibit Stands': '34', 'Educational': '145', 'Election Equipment': '39', 'Electrical Supplies': '37', 'Electronics, Personal': '585', 'Engineering Equipment and Supplies': '38', 'Equipment, Heavy / Construction': '36', 'Exercise Equipment': '147', 'Fine Art': '157', 'Fire and Police Equipment': '42', 'Fire Trucks': '94K', 'Firearm Accessories': '158', 'Firearms and Live Ammunition': '55', 'First Aid': '35', 'Food': '44', 'Forklifts': '142', 'Fueling Equipment': '163', 'Furniture/Furnishings': '46', 'Gambling Machines and Equipment': '166', 'Garbage': '48', 'Garbage and Refuse Containers': '49', 'Garbage Trucks': '94M', 'Generators': '153', 'Glass': '47', 'Golf Course Equipment': '73', 'Grandstands and bleachers': '981', 'Health and Beauty': '161', 'Highway Equipment': '54', 'Holiday/Seasonal Items': '164', 'HVAC Equipment': '52', 'Industrial Compressors': '114', 'Industrial Equipment, General': '51', 'Industrial Pumps': '113', 'Industrial Pumps and Compressors': '112', 'Janitorial Equipment': '53', 'Jewelry and Watches': '56', 'Knives / Multi-Tools': '527', 'Laboratory Equipment': '57', 'Laboratory Pumps and Tubing': '302', 'Laundry Equipment': '59', 'Library Equipment': '60', 'Lighting/Fixtures': '151', 'Lost/Abandoned Property': '156', 'Lumber': '63', 'Machinery': '65', 'Mailing Equipment': '66', 'Material Handling Equipment': '140', 'Medical Equipment and Supplies': '67', 'Medication Dispensing and Measuring': '308', 'Metal, Scrap': '68', 'Miscellaneous Vehicles': '94', 'Motor Homes / Travel Trailers': '94E', 'Motorcycles': '94F', 'Mowing Equipment': '71', 'Music/Musical Equipment': '70', 'Nursery/Horticulture/Landscaping': '40', 'Office Equipment/Supplies': '72', 'Outdoor Living': '155', 'Paper and Paper Products': '75', 'Parking Meters': '77', 'Permanent Buildings': '20', 'Photographic Equipment': '76', 'Pipe, Valves, and Fittings, Industrial': '79', 'Playground / Amusement Park Equipment': '130', 'Plumbing Equipment and Supplies': '78', 'Pool Supplies and Equipment': '165', 'Portable Buildings and structures': '980', 'Printing and Binding Equipment': '96', 'Public Safety and Control': '111', 'Public Utility Equipment': '80', 'Pump': '141', 'Pump Parts and Accessories': '115', 'Rail Equipment and Accessories': '83', 'Real Estate / Land Parcels': '84', 'Real Estate Tax Liquidations - Pennsylvania': '864', 'Recovered Items': '162', 'Recyclable Materials': '85', 'Road/Highway/Bridge Supplies': '87', 'Scales and Weighing Apparatus': '88', 'School Equipment': '89', 'Security Equipment': '14', 'Simulators': '146', 'Snow Removal Equipment': '154', 'Sporting Equipment': '91', 'Survey Equipment': '144', 'SUV': '94L', 'Sweeper - Parking Lot/Warehouse': '110', 'Sweeper - Street': '94N', 'Tanks': '148', 'Televisions': '514', 'Tires and Tubes': '93', 'Tools, All Types': '90', 'Towers -- Water/Fire/Transmission': '97', 'Tractor - Farm': '100', 'Traffic Signals and Controls': '92', 'Trailers': '94I', 'Trucks, Heavy Duty 1 ton and Over': '94C', 'Trucks, Light Duty under 1 ton': '94B', 'Vans': '94D', 'Vehicle Equipment/Parts': '09', 'Vending Equipment': 'VE', 'Welding Equipment': '95', 'Woodworking Equipment': '160'}
class WebScraper(object):
    def __init__(self, categories):
        self.categories = categories
        #initialize dictionary for storage
        self.master_dict = {}
        # Run The Scraper:
        asyncio.run(self.main())

    async def fetch(self, session, category):
        try:
            time.sleep(1)
            url = ("https://store.steampowered.com/app/{}/".format(appId))
            async with session.head(url) as response:
                if response.status == 302:
                    return [appId, "302"]
                if response.status == 403:
                    return [appId, "403"]
                if response.status == 429:
                    time.sleep(120)
                    return [appId, "429"]
                if response.status != 200:
                    return [appId, str(response.status)]
                else:
                    return [appId, "200"]
        except Exception as e:
            print(str(e))

    async def main(self):
        tasks = []
        headers = {
            "user-agent": "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"}
        async with aiohttp.ClientSession(headers=headers) as session:
            for appId in self.appIds:
                tasks.append(self.fetch(session, appId))

            data_fetched = await asyncio.gather(*tasks)
            for data in data_fetched:
                if data is not None:
                    gameID = data[0]
                    true_game = data[1]
                    self.master_dict[gameID] = true_game
                else:
                    print("{} failed".format(appId))

startTime = datetime.now()
appIds = master_df['appId'].to_list()
appIds = appIds[:10000]
scraper = WebScraper(appIds = appIds)
df = pd.DataFrame.from_dict(scraper.master_dict, orient='index', columns=["response"])
df.to_csv("steam_urls.csv")
print(datetime.now() - startTime)