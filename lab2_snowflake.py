from faker import Faker
import psycopg2
import random
from datetime import datetime, timedelta

fake = Faker()
Faker.seed(42)

conn = psycopg2.connect(
    dbname="CinemaSnowflake",
    user="postgres",
    password="**",
    host="localhost",
    port="5432"
)
cur = conn.cursor()



genres = ["Drama", "Comedy", "Action", "Thriller", "Horror", "Fantasy", "Sci-Fi", "Romance"]
countries = ["USA", "UK", "France", "Germany", "Italy", "Japan", "Ukraine", "India"]

# DimGenre
for g in genres:
    cur.execute("""
        INSERT INTO DimGenre (genre_name)
        VALUES (%s)
    """, (g,))

# DimCountry
for c in countries:
    cur.execute("""
        INSERT INTO DimCountry (country_name)
        VALUES (%s)
    """, (c,))

# DimMovie
for _ in range(20):
    cur.execute("""
        INSERT INTO DimMovie (title, genre_id, duration, country_id, release_year)
        VALUES (%s, %s, %s, %s, %s)
    """, (
        fake.sentence(nb_words=3),
        random.randint(1, len(genres)),
        random.randint(80, 180),
        random.randint(1, len(countries)),
        random.randint(1990, 2025)
    ))


# DimCustomer
for _ in range(150):
    cur.execute("""
        INSERT INTO DimCustomer (full_name, email, phone_number)
        VALUES (%s, %s, %s)
    """, (
        fake.name(),
        fake.email(),
        fake.phone_number()
    ))


# DimDate
start_date = datetime(2023, 1, 1)
for i in range(365):
    d = start_date + timedelta(days=i)
    cur.execute("""
        INSERT INTO DimDate (purchase_date, purchase_day, purchase_month, purchase_year)
        VALUES (%s, %s, %s, %s)
    """, (
        d,
        d.day,
        d.month,
        d.year
    ))



cinemas = ["Multiplex", "Planeta Kino", "Kinopalace", "Cinema City"]
cities = ["Lviv", "Kyiv", "Poltava"]

# DimCinemaName
for c in cinemas:
    cur.execute("""
        INSERT INTO DimCinemaName (cinema_name)
        VALUES (%s)
    """, (c,))

# DimCity
for c in cities:
    cur.execute("""
        INSERT INTO DimCity (city_name)
        VALUES (%s)
    """, (c,))

# DimCinema
for _ in range(10):
    cur.execute("""
        INSERT INTO DimCinema (cinema_name_id, city_id, hall_number)
        VALUES (%s, %s, %s)
    """, (
        random.randint(1, len(cinemas)),
        random.randint(1, len(cities)),
        random.randint(1, 10)
    ))

positions = ["Ticket Seller", "Manager"]

# DimPosition
for p in positions:
    cur.execute("""
        INSERT INTO DimPosition (position_name)
        VALUES (%s)
    """, (p,))

# DimStaff
for _ in range(15):
    cur.execute("""
        INSERT INTO DimStaff (full_name, position_id)
        VALUES (%s, %s)
    """, (
        fake.name(),
        random.randint(1, len(positions))
    ))


# FactSales
for _ in range(10000):
    q = random.randint(1, 5)
    cur.execute("""
        INSERT INTO FactSales (movie_id, customer_id, date_id, cinema_id, staff_id, quantity, amount)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (
        random.randint(1, 20),   
        random.randint(1, 150),   
        random.randint(1, 365),  
        random.randint(1, 10),    
        random.randint(1, 15),   
        q,    
        round(random.uniform(100, 200)*q, 2)  
    ))


conn.commit()
cur.close()
conn.close()
