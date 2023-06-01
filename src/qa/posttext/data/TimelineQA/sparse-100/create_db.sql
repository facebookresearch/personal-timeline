create table annual_medical_care_log(eid TEXT PRIMARY KEY,date TEXT,for_whom TEXT,type_of_care TEXT);
create table daily_chat_log(eid TEXT PRIMARY KEY,date TEXT,timeofday TEXT,howlong INTEGER,friends TEXT);
create table daily_exercise_log(eid TEXT PRIMARY KEY,date TEXT,exercise TEXT,heart_rate INTEGER);
create table daily_meal_log(eid TEXT PRIMARY KEY,date TEXT,mealtype TEXT,foodtype TEXT,people_string TEXT);
create table daily_read_log(eid TEXT PRIMARY KEY,date TEXT,readtype TEXT,howlong INTEGER);
create table daily_watchtv_log(eid TEXT PRIMARY KEY,date TEXT,watchtype TEXT,howlong INTEGER);
create table marriages_log(eid TEXT PRIMARY KEY,married_date TEXT,partner_name TEXT,location TEXT);
create table monthly_pet_care_log(eid TEXT PRIMARY KEY,date TEXT,pet_care_type TEXT);
create table moves_log(eid TEXT PRIMARY KEY,date TEXT,type_of_move TEXT, destination TEXT);
create table travel_log(eid TEXT PRIMARY KEY,start_date TEXT,end_date TEXT,city TEXT,people TEXT);
create table travel_dining_log(eid TEXT PRIMARY KEY,start_date TEXT,end_date TEXT,city TEXT,dining_date TEXT,food_type TEXT,food_location TEXT,place_visit_date TEXT,place TEXT,people TEXT,action TEXT,emotion TEXT);
create table travel_places_visited_log(eid TEXT PRIMARY KEY,start_date TEXT,end_date TEXT,city TEXT,place_visit_date TEXT,place TEXT, people TEXT,action TEXT,emotion TEXT);
create table weekly_bakeorcook_log(eid TEXT PRIMARY KEY,date TEXT,cuisine TEXT,location TEXT,people TEXT);
create table weekly_dating_log(eid TEXT PRIMARY KEY,date TEXT,people_string TEXT,location TEXT);
create table weekly_grocery_log(eid TEXT PRIMARY KEY,date TEXT,fruits TEXT,drinks TEXT,toiletries TEXT,people_string TEXT);
create table weekly_hobby_log(eid TEXT PRIMARY KEY,date TEXT,hobbies TEXT,people_string TEXT);

.mode csv
.import annual_medical_care-log.csv annual_medical_care_log --skip 1
.import daily_meal-log.csv  daily_meal_log --skip 1
.import marriages-log.csv  marriages_log --skip 1
.import travel_places_visited-log.csv  travel_places_visited_log --skip 1
.import weekly_dating-log.csv  weekly_dating_log --skip 1
.import daily_chat-log.csv  daily_chat_log --skip 1
.import daily_read-log.csv  daily_read_log --skip 1
.import monthly_pet_care-log.csv  monthly_pet_care_log --skip 1 
.import travel-log.csv  travel_log --skip 1
.import weekly_grocery-log.csv  weekly_grocery_log --skip 1
.import daily_exercise-log.csv  daily_exercise_log --skip 1
.import daily_watchtv-log.csv  daily_watchtv_log --skip 1
.import moves-log.csv   moves_log --skip 1
.import travel_dining-log.csv   travel_dining_log --skip 1
.import weekly_bakeorcook-log.csv   weekly_bakeorcook_log --skip 1   
.import weekly_hobby-log.csv   weekly_hobby_log --skip 1


