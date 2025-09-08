import pyodbc

conn = pyodbc.connect(
   'DRIVER={SQL Server};'
   'SERVER=WIN-8SNIO6IEEFI;'
   'DATABASE=OnlineCinema;'
   'UID=sa;'
   'PWD=sa'
)

try:
   cursor = conn.cursor()       
   print("Successful DB connection.")
except pyodbc.Error as e:
   print(f"DB connection error: {e}")


cursor.execute("""
IF OBJECT_ID('Movie', 'U') IS NULL
CREATE TABLE Movie (
   Movie_Id INT PRIMARY KEY IDENTITY,
   Title NVARCHAR(100),
   Genre NVARCHAR(50),
   ReleaseYear INT
);
""")


cursor.execute("""
IF OBJECT_ID('Subscriber', 'U') IS NULL
CREATE TABLE Subscriber (
   Subscriber_ID INT PRIMARY KEY IDENTITY,
   FullName NVARCHAR(100),
   Email NVARCHAR(100) UNIQUE
);
""")


cursor.execute("""
IF OBJECT_ID('Session', 'U') IS NULL
CREATE TABLE Session (
   Session_ID INT PRIMARY KEY IDENTITY,
   Subscriber_ID INT FOREIGN KEY REFERENCES Subscriber (Subscriber_ID),
   Movie_ID INT FOREIGN KEY REFERENCES Movie(Movie_ID),
   WatchDate DATE
);
""")

conn.commit()

"""
cursor.execute("INSERT INTO Subscriber (FullName, Email) VALUES (?, ?)", ("Michael Gerard", "mich84ger@gmail.com"))
cursor.execute("INSERT INTO Subscriber (FullName, Email) VALUES (?, ?)", ("Becky Tyler", "becky569ler@gmail.com"))
cursor.execute("INSERT INTO Subscriber (FullName, Email) VALUES (?, ?)", ("Dominic Ewing", "domi21ewi@gmail.com"))


cursor.execute("INSERT INTO Movie (Title, Genre, ReleaseYear) VALUES (?, ?, ?)", ("Inception", "Science fiction", 2010))
cursor.execute("INSERT INTO Movie (Title, Genre, ReleaseYear) VALUES (?, ?, ?)", ("Schindler's List", "Drama", 1993))
cursor.execute("INSERT INTO Movie (Title, Genre, ReleaseYear) VALUES (?, ?, ?)", ("The Matrix", "Action", 1999))
cursor.execute("INSERT INTO Movie (Title, Genre, ReleaseYear) VALUES (?, ?, ?)", ("Interstellar", "Science fiction", 2014))
cursor.execute("INSERT INTO Movie (Title, Genre, ReleaseYear) VALUES (?, ?, ?)", ("Gladiator", "Action", 2000))
cursor.execute("INSERT INTO Movie (Title, Genre, ReleaseYear) VALUES (?, ?, ?)", ("The Godfather", "Crime", 1972))


cursor.execute("INSERT INTO Session (Subscriber_ID, Movie_ID, WatchDate) VALUES (?, ?, ?)", (1, 1, "2025-08-10"))
cursor.execute("INSERT INTO Session (Subscriber_ID, Movie_ID, WatchDate) VALUES (?, ?, ?)", (2, 2, "2025-08-15"))
cursor.execute("INSERT INTO Session (Subscriber_ID, Movie_ID, WatchDate) VALUES (?, ?, ?)", (3, 3, "2025-08-23"))
cursor.execute("INSERT INTO Session (Subscriber_ID, Movie_ID, WatchDate) VALUES (?, ?, ?)", (1, 5, "2025-08-25"))
cursor.execute("INSERT INTO Session (Subscriber_ID, Movie_ID, WatchDate) VALUES (?, ?, ?)", (1, 6, "2025-08-30"))
cursor.execute("INSERT INTO Session (Subscriber_ID, Movie_ID, WatchDate) VALUES (?, ?, ?)", (3, 4, "2025-08-30"))

conn.commit()
"""


print("Movies list:")
cursor.execute("SELECT Movie_ID, Title, Genre, ReleaseYear FROM Movie")
for row in cursor.fetchall():
   print(row)



cursor.execute("INSERT INTO Movie (Title, Genre, ReleaseYear) VALUES (?, ?, ?)", ("Avatar", "Fantasy", 2009))
conn.commit()


cursor.execute("UPDATE Movie SET Genre=? WHERE Title=?", ("Science fiction", "Avatar"))
conn.commit()


cursor.execute("DELETE FROM Movie WHERE Title=?", ("Avatar",))
conn.commit()


print("\nMovies list:")
cursor.execute("SELECT Movie_ID, Title, Genre, ReleaseYear FROM Movie")
for row in cursor.fetchall():
   print(row)


cursor.close()
conn.close()
