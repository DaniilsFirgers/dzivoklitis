from typing import List
from bs4 import BeautifulSoup
import requests
import pandas as pd
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.mime.text import MIMEText
import toml
from pathlib import Path
import os

from scraper.config import Config, District, GeneralConfig, GmailConfig, TelegramConfig


LIST_OF_DISTRICTS = []
FLATS = {}
my_email = "Your email"
password = "Your password in Environ"
MSG = MIMEMultipart()
BODY_PART = MIMEText("See new ads!", 'plain')
MSG['Subject'] = "New advertisements"
MSG['From'] = my_email
MSG['To'] = my_email


class FlatsParser:
    def __init__(self):
        self.config = self.load_config()

    def load_config(self):

        cwd = os.getcwd()
        config_path = Path(cwd) / "config.toml"
        with open(config_path, "r") as file:
            data = toml.load(file)

        telegram = TelegramConfig(**data["telegram"])
        gmail = GmailConfig(**data["gmail"])
        general = GeneralConfig(**data["general"])
        districts = [District(**district) for district in data["districts"]]

        return Config(telegram=telegram, gmail=gmail, general=general, districts=districts)

    def start(self, districts: List[District]) -> None:
        for district in districts:
            pages_link = f"https://www.ss.lv/en/real-estate/flats/{self.config.general.city_name}/{district.name}/{self.config.general.look_back_argument}/{self.config.general.deal_type}/"
            print(pages_link)
        pass

    def get_districts_list(self) -> tuple[List[int], List[str]]:
        districts_found = []
        warnings = []
        link = f"https://www.ss.lv/en/real-estate/flats/{self.config.general.city_name.lower()}/"

        try:
            response = requests.get(link, timeout=10)
            response.raise_for_status()
        except requests.RequestException as e:
            raise ValueError(f"Error accessing the website: {e}")

        try:
            soup = BeautifulSoup(response.text, "html.parser")
            district_elements = soup.find_all(name="h4", class_="category")

            if not district_elements:
                raise ValueError("No district elements found on page")

            for index, district in enumerate(district_elements):
                area: str = district.getText().strip().lower().replace(" ", "-")
                districts_found.append(area)

                if index == 38:  # Optional limit on number of districts
                    break

            final_districts = []
            for district in self.config.districts:
                try:
                    districts_found.index(district.name)
                    final_districts.append(district)
                except ValueError:
                    warnings.append(f"District {district.name} not found")

            return final_districts, warnings

        except Exception as e:
            raise ValueError(f"Error parsing district data: {e}")

# accessing the site


def starting_link():
    selected_districts = []
    link = "https://www.ss.lv/en/real-estate/flats/riga/"
    response = requests.get(link)
    main_text = response.text
    soup = BeautifulSoup(main_text, "html.parser")
    districts = soup.find_all(name="h4", class_="category")

    # retrieving all the districts and replacing a space with -
    for index, district in enumerate(districts):
        area = district.getText().lower()
        if " " in area:
            new_area = area.replace(" ", "-")
        else:
            new_area = area
        LIST_OF_DISTRICTS.append(new_area)
        if index == 38:

            break
    print(LIST_OF_DISTRICTS)
    # appending a list with districts we are interested in
    for name in ("centre", "plyavnieki", "purvciems", "mezhapark"):
        selected_district = LIST_OF_DISTRICTS.index(name)
        selected_districts.append(selected_district)

    return selected_districts


# filling in a FLATS dictionary with all the data
def number_of_pages(district_number):
    pages_link = f"https://www.ss.lv/en/real-estate/flats/riga/{LIST_OF_DISTRICTS[district_number]}/today-2/sell/"
    response_1 = requests.get(pages_link)
    pages = response_1.text

    soup_1 = BeautifulSoup(pages, "html.parser")
    page_numbers = soup_1.find_all(name="a", class_="navi")

    # determining number of pages
    list_of_pages = [1]
    for page_num in page_numbers[1:-1]:
        page_text = int(page_num.getText())
        list_of_pages.append(page_text)
    # extracting text from each page
    for page in list_of_pages:
        specific_page_link = f"https://www.ss.lv/en/real-estate/flats/riga/" \
                             f"{LIST_OF_DISTRICTS[district_number]}/today-2/sell/page{page}.html"
        response_2 = requests.get(specific_page_link)
        ads_on_page = response_2.text
        soup_2 = BeautifulSoup(ads_on_page, "html.parser")

        descriptions = soup_2.find_all(name="a", class_="am")
        streets = soup_2.find_all(name="td", class_="msga2-o pp6")
        info = []
        streets_info = []

        # extracting links for all flats
        for description in descriptions:
            new_info = description.get("href")
            info.append(f"https://www.ss.lv/{new_info}")

        # extracting all data about a flat
        for street in streets:
            new_street = street.getText()
            streets_info.append(new_street)

        # nested dictionary with a link as a key
        street = 0
        rooms = 1
        m2 = 2
        floor = 3
        series = 4
        price_m2 = 5
        full_price = 6

        print(len(info))

        # filling in the FLATS dictionary
        for n in range(0, len(info)):
            link = info[n]
            FLATS[link] = {}

            FLATS[link]["street"] = streets_info[street]
            FLATS[link]["rooms"] = streets_info[rooms]
            FLATS[link]["m^2"] = streets_info[m2]
            FLATS[link]["floor"] = streets_info[floor]
            FLATS[link]["series"] = streets_info[series]
            FLATS[link]["price per m^2"] = streets_info[price_m2]
            FLATS[link]["full price"] = streets_info[full_price]
            street += 7
            rooms += 7
            m2 += 7
            floor += 7
            series += 7
            price_m2 += 7
            full_price += 7

# checking whether the dictionary is empty, creating a csv file and sending it to our email


def main():

    for district in districts:
        number_of_pages(district)
    if len(FLATS) != 0:
        # creating a dataframe
        df = pd.DataFrame.from_dict({i: FLATS[i]
                                     for i in FLATS.keys()},
                                    orient='index')
        # filtering and manipulating the dataframe
        df["full price"] = df["full price"].replace(
            {"  €": "", ",": ""}, regex=True)
        df["price per m^2"] = df["price per m^2"].replace(
            {" €": "", ",": ""}, regex=True)
        df["full price"] = df["full price"].astype(int)
        df["price per m^2"] = df["price per m^2"].astype(int)
        df["m^2"] = df["m^2"].astype(int)
        print(df)
        df = df.loc[
            (df["full price"] <= "your value") & (df["price per m^2"] <= "your value") & (df["price per m^2"] >= "your value") & (
                df["m^2"] >= "your value")]
        df.to_csv("flats.csv")

        MSG.attach(BODY_PART)
        with open("flats.csv", 'rb') as file:
            # Attach the file with filename to the email
            MSG.attach(MIMEApplication(file.read(), Name="flats.csv"))
        # with smtplib.SMTP("smtp.gmail.com", port=587) as connection:
        #     connection.starttls()
        #     connection.login(my_email, password)
        #     connection.sendmail(from_addr=MSG["From"],
        #                         to_addrs=MSG['To'],
        #                         msg=MSG.as_string())
    else:
        with smtplib.SMTP("smtp.gmail.com", port=587) as connection:
            connection.starttls()
            connection.login(my_email, password)
            connection.sendmail(from_addr=MSG["From"],
                                to_addrs=MSG['To'],
                                msg=f"Subject:No new advertisements!\n\n"
                                    f"Unfortunately, no new ads under specified conditions for two previous "
                                    f"days found :(")


if __name__ == "__main__":
    scraper = FlatsParser()
    try:
        districts, warnings = scraper.get_districts_list()
    except Exception as e:
        # Here we will send intial message to ther messenger if fail the parsing
        print(f"Error: {e}")
    else:
        if warnings:
            # here we will send message to the messenger about warnings
            print("\n".join(warnings))
        scraper.start(districts)
    # main()
