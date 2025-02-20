import hashlib
import requests
import io
import psycopg2
from PIL import Image
from datetime import datetime
import re
from geopy.geocoders import Nominatim


class Coordinates:
    def __init__(self, latitude: float, longitude: float):
        self.latitude = latitude
        self.longitude = longitude


class Flat:
    def __init__(self, flat_data, source, city: str):
        self.flat_data = flat_data
        self.source = source
        self.city = city
        self.flat_id = self.generate_id()
        self.img_url = flat_data.get('thumbnail')
        self.image_data = None
        self.location = None
        self.load_img()
        self.get_coordinates()

    def generate_id(self):
        # Construct the ID using the given hashing function
        return hashlib.md5(
            f"{self.source}-{self.flat_data['district']}-{self.flat_data['street']}-{self.flat_data['series']}-{self.flat_data['rooms']}-{self.flat_data['m2']}-{self.flat_data['floor']}-{self.flat_data['last_floor']}".encode()
        ).hexdigest()

    def load_img(self):
        if self.img_url is None:
            return
        response = requests.get(self.img_url)
        if response.status_code != 200:
            return

        image_file = io.BytesIO(response.content)
        image = Image.open(image_file)
        max_size = (303, 230)
        image.thumbnail(max_size, Image.LANCZOS)  # Maintains aspect ratio
        resized_image_file = io.BytesIO()
        image.save(resized_image_file, format="JPEG")

        resized_image_file.seek(0)
        self.image_data = resized_image_file.getvalue()

    def get_coordinates(self):
        # Use the geolocator to get the coordinates
        geolocator = Nominatim(user_agent="flats_scraper")
        cleaned_street = re.sub(
            r'\b[A-Za-z]{1,7}\.\s*', '', self.flat_data['street'])  # Clean street name
        try:
            location = geolocator.geocode({
                "street": cleaned_street,
                "city": self.city,
                "country": "Latvia"
            })

            if location is None:
                print(
                    f"Could not get coordinates for {self.flat_data['street']}")
                return

            self.location = Coordinates(location.latitude, location.longitude)
        except Exception as e:
            print(f"Error while getting coordinates: {e}")
            return

    def insert_flats(self, cursor):
        query = """
        INSERT INTO flats (flat_id, source, url, district, street, rooms, floors_total, floor, area, series, location, image_data, created_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, ST_SetSRID(ST_MakePoint(%s, %s), 4326), %s, %s)
        ON CONFLICT (flat_id) DO NOTHING;
        """
        coordinates = (self.location.latitude, self.location.longitude) if self.location else (
            0.0, 0.0)  # Use (0.0, 0.0) if no coordinates found
        cursor.execute(query, (
            self.flat_id,
            self.source,
            self.flat_data['link'],
            self.flat_data['district'],
            self.flat_data['street'],
            self.flat_data['rooms'],
            self.flat_data['last_floor'],
            self.flat_data['floor'],
            self.flat_data['m2'],
            self.flat_data['series'],
            coordinates[0],  # longitude
            coordinates[1],  # latitude
            self.image_data,
            datetime.now()
        ))

    def insert_flats_price(self, cursor):
        query = """
        INSERT INTO flats_price (flat_id, price_per_m2, updated_at)
        VALUES (%s, %s, %s);
        """
        cursor.execute(query, (
            self.flat_id,
            self.flat_data['price_per_m2'],
            datetime.now()
        ))

    def insert_favourite_flats(self, cursor):
        query = """
        INSERT INTO favourite_flats (flat_id)
        VALUES (%s);
        """
        cursor.execute(query, (self.flat_id,))


def main():
    # Sample JSON data
    flats_data = {
        "3": {
            "id": "dm_55531560",
            "timestamp": 1731786434001,
            "flat": {
                "id": "dm_55531560",
                "link": "https://www.ss.lv//msg/en/real-estate/flats/riga/centre/fjcki.html",
                "thumbnail": "https://i.ss.lv/gallery/7/1306/326448/65289438.800.jpg",
                "district": "centre",
                "price_per_m2": 1500,
                "rooms": 2,
                "street": "Gogola 10",
                "m2": 60.0,
                "floor": 3,
                "last_floor": 5,
                "series": "Pre-war house",
                "full_price": 90000
            }
        },
        "6": {
            "id": "dm_54894512",
            "timestamp": 1732010577114,
            "flat": {
                "id": "dm_54894512",
                "link": "https://www.ss.lv//msg/en/real-estate/flats/riga/imanta/achdd.html",
                "thumbnail": "https://i.ss.lv/gallery/7/1220/304827/60965237.800.jpg",
                "district": "imanta",
                "price_per_m2": 1742,
                "rooms": 2,
                "street": "Progresa 3",
                "m2": 64.0,
                "floor": 4,
                "last_floor": 5,
                "series": "New",
                "full_price": 111500
            }
        },
        "10": {
            "id": "dm_55727435",
            "timestamp": 1732205691102,
            "flat": {
                "id": "dm_55727435",
                "link": "https://www.ss.lv//msg/en/real-estate/flats/riga/centre/dkxmd.html",
                "thumbnail": "https://i.ss.lv/gallery/6/1188/296772/59354270.800.jpg",
                "district": "centre",
                "price_per_m2": 2170,
                "rooms": 2,
                "street": "Artilerijas 6",
                "m2": 53.0,
                "floor": 5,
                "last_floor": 5,
                "series": "Recon.",
                "full_price": 115000
            }
        },
        "13": {
            "id": "dm_55544474",
            "timestamp": 1733133657437,
            "flat": {
                "id": "dm_55544474",
                "link": "https://www.ss.lv//msg/en/real-estate/flats/riga/plyavnieki/dihgc.html",
                "thumbnail": "https://i.ss.lv/gallery/7/1304/325769/flats-riga-plyavnieki-65153665.800.jpg",
                "district": "plyavnieki",
                "price_per_m2": 1299,
                "rooms": 2,
                "street": "Zemes 3",
                "m2": 50.0,
                "floor": 5,
                "last_floor": 9,
                "series": "602-th",
                "full_price": 64950
            }
        },
        "15": {
            "id": "dm_55784784",
            "timestamp": 1733404485154,
            "flat": {
                "id": "dm_55784784",
                "link": "https://www.ss.lv//msg/en/real-estate/flats/riga/teika/becfjo.html",
                "thumbnail": "https://i.ss.lv/gallery/7/1298/324470/flats-riga-teika-64893838.800.jpg",
                "district": "teika",
                "price_per_m2": 1620,
                "rooms": 2,
                "street": "Burtnieku 36a",
                "m2": 74.0,
                "floor": 3,
                "last_floor": 5,
                "series": "New",
                "full_price": 119900
            }
        },
        "17": {
            "id": "dm_55004268",
            "timestamp": 1733951430586,
            "flat": {
                "id": "dm_55004268",
                "link": "https://www.ss.lv//msg/en/real-estate/flats/riga/centre/cnncn.html",
                "thumbnail": "https://i.ss.lv/gallery/7/1230/307290/flats-riga-centre-61457877.800.jpg",
                "district": "centre",
                "price_per_m2": 1864,
                "rooms": 2,
                "street": "Valmieras 28",
                "m2": 59.0,
                "floor": 5,
                "last_floor": 5,
                "series": "New",
                "full_price": 110000
            }
        },
        "19": {
            "id": "dm_55839924",
            "timestamp": 1734768411061,
            "flat": {
                "id": "dm_55839924",
                "link": "https://www.ss.lv//msg/en/real-estate/flats/riga/centre/coonh.html",
                "thumbnail": "https://i.ss.lv/gallery/7/1309/327035/flats-riga-centre-65406829.800.jpg",
                "district": "centre",
                "price_per_m2": 2222,
                "rooms": 2,
                "street": "Klijanu 16",
                "m2": 54.0,
                "floor": 3,
                "last_floor": 10,
                "series": "New",
                "full_price": 120000
            }
        },
        "20": {
            "id": "dm_55846392",
            "timestamp": 1734959216448,
            "flat": {
                "id": "dm_55846392",
                "link": "https://www.ss.lv//msg/en/real-estate/flats/riga/purvciems/beinp.html",
                "thumbnail": "https://i.ss.lv/gallery/7/1305/326112/flats-riga-purvciems-65222306.800.jpg",
                "district": "purvciems",
                "price_per_m2": 1491,
                "rooms": 2,
                "street": "Ilukstes 99",
                "m2": 55.0,
                "floor": 14,
                "last_floor": 16,
                "series": "Spec. pr.",
                "full_price": 82000
            }
        },
        "24": {
            "id": "dm_55878570",
            "timestamp": 1736276776164,
            "flat": {
                "id": "dm_55878570",
                "link": "https://www.ss.lv//msg/en/real-estate/flats/riga/centre/cmlne.html",
                "thumbnail": "https://i.ss.lv/gallery/7/1312/327946/flats-riga-centre-65589117.800.jpg",
                "district": "centre",
                "price_per_m2": 1934,
                "rooms": 2,
                "street": "Valdemara 113",
                "m2": 62.0,
                "floor": 4,
                "last_floor": 5,
                "series": "Pre-war house",
                "full_price": 119900
            }
        },
        "25": {
            "id": "dm_54581282",
            "timestamp": 1736341346934,
            "flat": {
                "id": "dm_54581282",
                "link": "https://www.ss.lv//msg/en/real-estate/flats/riga/centre/fxxpp.html",
                "thumbnail": "https://i.ss.lv/gallery/7/1259/314699/62939691.800.jpg",
                "district": "centre",
                "price_per_m2": 1984,
                "rooms": 2,
                "street": "Skanstes 29",
                "m2": 61.0,
                "floor": 3,
                "last_floor": 24,
                "series": "New",
                "full_price": 121000
            }
        },
        "26": {
            "id": "dm_55899963",
            "timestamp": 1736686900407,
            "flat": {
                "id": "dm_55899963",
                "link": "https://www.ss.lv//msg/en/real-estate/flats/riga/centre/beekji.html",
                "thumbnail": "https://i.ss.lv/gallery/7/1309/327035/flats-riga-centre-65406829.800.jpg",
                "district": "centre",
                "price_per_m2": 1788,
                "rooms": 2,
                "street": "Cesu 5B",
                "m2": 46.0,
                "floor": 4,
                "last_floor": 6,
                "series": "Recon.",
                "full_price": 82230
            }
        },
        "27": {
            "id": "dm_55905558",
            "timestamp": 1736838157685,
            "flat": {
                "id": "dm_55905558",
                "link": "https://www.ss.lv//msg/en/real-estate/flats/riga/plyavnieki/dpxgb.html",
                "thumbnail": "https://i.ss.lv/gallery/7/1315/328653/flats-riga-plyavnieki-65730446.800.jpg",
                "district": "plyavnieki",
                "price_per_m2": 1269,
                "rooms": 2,
                "street": "Ulbrokas 12 k-3",
                "m2": 67.0,
                "floor": 6,
                "last_floor": 9,
                "series": "New",
                "full_price": 85000
            }
        },
        "28": {
            "id": "dm_55923091",
            "timestamp": 1737270545210,
            "flat": {
                "id": "dm_55923091",
                "link": "https://www.ss.lv//msg/en/real-estate/flats/riga/plyavnieki/bemmjk.html",
                "thumbnail": "https://i.ss.lv/gallery/7/1317/329093/flats-riga-plyavnieki-65818463.800.jpg",
                "district": "plyavnieki",
                "price_per_m2": 1186,
                "rooms": 2,
                "street": "Salnas 26",
                "m2": 51.0,
                "floor": 6,
                "last_floor": 9,
                "series": "602-th",
                "full_price": 60500
            }
        },
        "29": {
            "id": "dm_55925271",
            "timestamp": 1737313595385,
            "flat": {
                "id": "dm_55925271",
                "link": "https://www.ss.lv//msg/en/real-estate/flats/riga/centre/adfli.html",
                "thumbnail": "https://i.ss.lv/gallery/7/1317/329149/flats-riga-centre-65829760.800.jpg",
                "district": "centre",
                "price_per_m2": 2083,
                "rooms": 2,
                "street": "Artilerijas 19",
                "m2": 48.0,
                "floor": 4,
                "last_floor": 5,
                "series": "Pre-war house",
                "full_price": 100000
            }
        },
        "30": {
            "id": "dm_55926407",
            "timestamp": 1737368497104,
            "flat": {
                "id": "dm_55926407",
                "link": "https://www.ss.lv//msg/en/real-estate/flats/riga/centre/aohin.html",
                "thumbnail": "https://i.ss.lv/gallery/7/1317/329176/flats-riga-centre-65835024.800.jpg",
                "district": "centre",
                "price_per_m2": 1547,
                "rooms": 2,
                "street": "Alauksta 12",
                "m2": 53.0,
                "floor": 2,
                "last_floor": 5,
                "series": "Pre-war house",
                "full_price": 82000
            }
        },
        "31": {
            "id": "dm_55933057",
            "timestamp": 1737486070428,
            "flat": {
                "id": "dm_55933057",
                "link": "https://www.ss.lv//msg/en/real-estate/flats/riga/purvciems/omjjo.html",
                "thumbnail": "https://i.ss.lv/gallery/7/1318/329341/flats-riga-purvciems-65868191.800.jpg",
                "district": "purvciems",
                "price_per_m2": 1231,
                "rooms": 2,
                "street": "Vejavas 10k2",
                "m2": 52.0,
                "floor": 4,
                "last_floor": 9,
                "series": "602-th",
                "full_price": 64000
            }
        }
    }

    # Connect to the PostgreSQL database
    conn = psycopg2.connect(
        dbname="flats",
        user="admin",
        password="supersecret",
        host="postgres",
        port="5432"
    )
    cursor = conn.cursor()
    print("Connected to the database")

    # Insert the data into the database
    source = "ss"  # Modify if needed
    city = "Riga"  # Modify if needed
    for flat_data in flats_data.values():
        flat = Flat(flat_data['flat'], source, city)
        print(f"Inserting flat with ID: {flat.flat_id}")
        flat.insert_flats(cursor)
        print(f"Inserted flat with ID: {flat.flat_id}")
        flat.insert_flats_price(cursor)
        print(f"Inserted flat price with ID: {flat.flat_id}")
        flat.insert_favourite_flats(cursor)
        print(f"Inserted favourite flat with ID: {flat.flat_id}")

    # Commit changes and close the connection
    conn.commit()
    cursor.close()
    conn.close()


if __name__ == "__main__":
    main()
