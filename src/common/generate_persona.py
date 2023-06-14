# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.

# This source code is licensed under the license found in the
# LICENSE file in the root directory of this source tree.
import numpy as np

#Need real databases in place of the ones below

HOBBIES_DB = ["fishing", "boating", "cooking"]
EXERCISE_DB = ["running", "swimming", "weight lifting", "golf", "soccer"]
MALE_NAMES_DB = ["Lambert", "Nathan", "Alon"]
FEMALE_NAMES_DB = ["Marieh", "Jane", "Wang-Chiew"]

# generate a name for the college the person went to TODO
def generate_college(p):
    return ("University of Washington")

# generate a name for the graduate school  the person went to TODO
def generate_graduate_school(p):
    return ("University of Wisconsin")

# generate a major for the college the person went to TODO
def generate_college_major(p):
    return ("Philosophy")

# generate a major for the graduate school the person went to TODO
def generate_graduate_school_major(p):
    return ("Astrophysics")

#draw a value from a probability distribution
def flip(values, probs):
    return (np.random.choice(values, 1, p=probs))[0]

def generate_persona():

    persona = {}
#Determine date of birth and age
    persona["age_years"] = np.random.randint(low=18, high=75, size=None)
    persona["birth_year"] = 2022 - persona["age_years"]
    persona["birth_month"] = np.random.randint(low=1, high=12, size=None)
    persona["birth_day"] = np.random.randint(low=0, high=28, size=None)

#Determine gender
    gender = np.random.randint(low=0, high=51, size=None)
    if gender == 0:
        persona["gender"] = "female"
    else:
        persona["gender"] = "male"


#Graduating from K, elementary school, middle school, high school, college,
# You graduate from K at either age 5 or 6, take either 5 or 6 years in elementary school, 3 years in middle school and 3-5 years in high school.

    values = [5,6]
    probs = [0.5,  0.5]

    persona["k_graduation"] =  flip([5,6], [0.5,  0.5]) + persona["birth_year"]

    persona["e_graduation"] = persona["k_graduation"] + flip([5,6,7], [0.1, 0.8, 0.1])
    persona["m_graduation"] = persona["e_graduation"] + 3
    persona["h_graduation"] = persona["m_graduation"] + flip([3,4,5], [0.1, 0.8, 0.1])

#College, yes or no
    persona["college"] = flip([1,0], [0.5,  0.5])
    if persona["college"] == 1:
        persona["college_graduation"] = persona["h_graduation"] + flip([3,4,5], [0.1, 0.8, 0.1])
        persona["college_location"] = generate_college(persona)
        persona["college_major"] = generate_college_major(persona)
        persona["graduate_school"] = flip([1,0], [0.2,  0.8])
        if persona["graduate_school"] == 1:
            persona["graduate_school_graduation"] = persona["college_graduation"] + flip([3,4,5,6,7], [0.2, 0.2, 0.4, 0.1, 0.1])
            persona["graduate_school_location"] = generate_graduate_school(persona)
            persona["graduate_school_major"] = generate_graduate_school_major(persona)

# Marriages.
# First generate the number of marriages, and then insert the appropriate years. The probability of number of marriages depends a bit on age.



    marriage_probs = [0.3, 0.4, 0.2, 0.07, 0.03]
    if  persona["age_years"] < 40:
        marriage_probs = [0.3, 0.4, 0.2, 0.1, 0.0]
    if  persona["age_years"] < 25:
         marriage_probs = [0.8, 0.2, 0.0, 0.0, 0.0]

    num_marriages = flip([0,1,2,3,4], marriage_probs)
    persona["num_marriages"] = num_marriages
    first_marriage_age = np.random.randint(low=20, high=35, size=None)
    current_age = first_marriage_age
    persona["married"] = []
    persona["divorced"] = []
    for marriage in range(0, num_marriages):
        if marriage in range(1,  num_marriages):
            persona["divorced"].append(current_age + length)
            current_age = current_age + length + time_till_next
            
        persona["married"].append(current_age)
        length = np.random.randint(low=2, high=15, size=None)
        time_till_next = np.random.randint(low=2, high=7, size=None)
# Can't plan for the future. If your age is less than what it takes you to complete your marriages and divorces, we don't let you do it.

        if current_age + length + time_till_next > persona["age_years"]:
            break
#children
    kids_probs = [0.2, 0.2, 0.2, 0.2, 0.2]
    if  persona["age_years"] < 30:
        kids_probs = [0.3, 0.3, 0.3, 0.1, 0.0]
    if  persona["age_years"] < 25:
        kids_probs = [0.7, 0.3, 0.0, 0.0, 0.0]
    num_kids = flip([0,1,2,3,4], kids_probs)
    persona["num_kids"] = num_kids
    time_between_kids_probs = [0.25, 0.20, 0.15, 0.20, 0.1, 0.1]
    age_at_first_kid = np.random.randint(low=20, high=30, size=None)
    persona["kids"] = []
    if age_at_first_kid > persona["age_years"]:
        age_at_first_kid = persona["age_years"]
    curr_age = age_at_first_kid
    for kid in range(num_kids):
        persona["kids"].append(curr_age)
        curr_age = curr_age + flip([1,2,3,4,5,6], time_between_kids_probs)
        if curr_age > persona["age_years"]:
            break
        

#jobs
    jobs_probs = [0.2, 0.4, 0.2, 0.1, 0.1]
    if  persona["age_years"] < 40:
        jobs_probs = [0.05, 0.3, 0.3, 0.2, 0.15]
    if  persona["age_years"] < 25:
        jobs_probs = [0.4, 0.3, 0.2, 0.1, 0.0]

    num_jobs = flip([0,1,2,3,4], jobs_probs)
    persona["num_jobs"] = num_jobs
    first_job_age = np.random.randint(low=20, high=25, size=None)
    current_age = first_job_age
    persona["started_job"] = []
    persona["quit_job"] = []
    for job in range(0, num_jobs):

        if job in range(1,  num_jobs):
            persona["quit_job"].append(current_age + length)
            current_age = current_age + length + time_till_next
            
        persona["started_job"].append(current_age)
        length = np.random.randint(low=2, high=15, size=None)
        time_till_next = np.random.randint(low=0, high=2, size=None)
# Can't plan for the future. If your age is less than what it takes you to complete your job transitions, we don't let you do it.
        if current_age + length + time_till_next > persona["age_years"]:
            break
# exercise, hobbies, verboseness, travel

    # This is the number of trips the person takes per year. It includes local, regional and international trips
    persona["trips_per_year"] = np.random.randint(low=0, high=6, size=None)

    # This is the expected number of daily or weekly events that the person is likely to record in their DB. 
    persona["verboseness"] = np.random.randint(low=0, high=20, size=None)

#name people 

        
    return (persona)


print (generate_persona())
