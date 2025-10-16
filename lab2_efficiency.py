import psycopg2
import time

#Star schema
conn = psycopg2.connect(
    dbname="CinemaStar",
    user="postgres",
    password="**",
    host="localhost",
    port="5432"
)
cursor = conn.cursor()

# Топ-5 фільмів за сумою продажів
start = time.time()
cursor.execute("SELECT m.title, SUM(f.amount) AS total_sales FROM FactSales f JOIN DimMovie m ON f.movie_id = m.movie_id GROUP BY m.title ORDER BY total_sales DESC LIMIT 5;")
end = time.time()
print(f"Час запиту Star: {end - start:.4f} секунд")

# Продажі по жанрах
start = time.time()
cursor.execute("SELECT m.genre, SUM(f.amount) AS total_sales FROM FactSales f JOIN DimMovie m ON f.movie_id = m.movie_id GROUP BY m.genre ORDER BY total_sales DESC;")
end = time.time()
print(f"Час запиту Star: {end - start:.4f} секунд")

# Продажі по роках
start = time.time()
cursor.execute("SELECT d.purchase_year, SUM(f.amount) AS total_sales FROM FactSales f JOIN DimDate d ON f.date_id = d.date_id GROUP BY d.purchase_year ORDER BY d.purchase_year;")
end = time.time()
print(f"Час запиту Star: {end - start:.4f} секунд")

conn.commit()
cursor.close()
conn.close()


#Snowflake schema
conn = psycopg2.connect(
    dbname="CinemaSnowflake",
    user="postgres",
    password="**",
    host="localhost",
    port="5432"
)
cursor = conn.cursor()

# Топ-5 фільмів за сумою продажів
start = time.time()
cursor.execute("SELECT m.title, SUM(f.amount) AS total_sales FROM FactSales f JOIN DimMovie m ON f.movie_id = m.movie_id JOIN DimGenre g ON m.genre_id = g.genre_id JOIN DimCountry c ON m.country_id = c.country_id GROUP BY m.title, g.genre_name, c.country_name ORDER BY total_sales DESC LIMIT 5;")
end = time.time()
print(f"\nЧас запиту Snowflake: {end - start:.4f} секунд")

# Продажі по жанрах
start = time.time()
cursor.execute("SELECT g.genre_name, SUM(f.amount) AS total_sales FROM FactSales f JOIN DimMovie m ON f.movie_id = m.movie_id JOIN DimGenre g ON m.genre_id = g.genre_id GROUP BY g.genre_name ORDER BY total_sales DESC;")
end = time.time()
print(f"Час запиту Snowflake: {end - start:.4f} секунд")

# Продажі по роках
start = time.time()
cursor.execute("SELECT d.purchase_year, SUM(f.amount) AS total_sales FROM FactSales f JOIN DimDate d ON f.date_id = d.date_id GROUP BY d.purchase_year ORDER BY d.purchase_year;")
end = time.time()
print(f"Час запиту Snowflake: {(end - start):.4f} секунд")


conn.commit()
cursor.close()
conn.close()