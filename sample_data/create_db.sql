create table books(book_name TEXT, img_url TEXT, id TEXT PRIMARY KEY, date TEXT, time TEXT);
create table purchase(purchase_id TEXT,productName TEXT,productPrice REAL,productQuantity REAL,id TEXT PRIMARY KEY,date TEXT,time TEXT);
create table exercise(textDescription TEXT,duration REAL,distance REAL,calories REAL,outdoor INTEGER,temperature TEXT, id TEXT PRIMARY KEY,start_date TEXT,start_time TEXT,end_date TEXT,end_time TEXT);
create table photos(textDescription TEXT,adddress TEXT,lat REAL,long REAL,details TEXT,img_url TEXT,id TEXT PRIMARY KEY,start_date TEXT,start_time TEXT,end_date TEXT,end_time TEXT);
create table streaming(artist TEXT,track TEXT,playtimeMs INTEGER,spotify_link TEXT,id TEXT PRIMARY KEY,start_date TEXT,start_time TEXT,end_date TEXT,end_time TEXT);
create table places(textDescription TEXT,start_address TEXT,start_lat REAL,start_long REAL,end_address TEXT,end_lat REAL,end_long REAL,id TEXT PRIMARY KEY,start_date TEXT,start_time TEXT,end_date TEXT,end_time TEXT);
create table trips(textDescription TEXT,country TEXT,states_provinces TEXT,cities_towns TEXT,places TEXT,id TEXT PRIMARY KEY,start_date TEXT,start_time TEXT,end_date TEXT,end_time TEXT);

.mode csv
.import books.csv books --skip 1
.import purchase.csv purchase --skip 1
.import exercise.csv exercise --skip 1
.import photos.csv photos --skip 1
.import streaming.csv streaming --skip 1
.import places.csv places --skip 1
.import trips.csv trips --skip 1
