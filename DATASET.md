# Personal timeline dataset

This dataset is a sample of ~2 months of one of our own member’s personal digital services data self-collected and anonymized. The digital services include:

* Books: Amazon Kindle and Libby, 93 records in total
* Purchase: Amazon, 95 records in total
* Streaming: Spotify, 111 records in total
* Exercise: Apple Watch, 33 records in total
* Photos: Google Photos, 325 records in total
* Places: Geo locations (lat/long and addresses) from the Google photos metadata, 467 records in total

All raw data were downloaded from the service providers following our data importer instructions. 

## How we anonymize the data

* *Books, purchase, streaming*: we reviewed each individual records
* *Places (all location, address data)*: We anonymize near-home location data by a distance-preserving random project to a high-dimensional space then project back the points to 2D. We use reverse geo-coding to label the addresses of those points. For locations that are not near-home, we verified that all addresses are public space.
* *Images*: We anonymize photos by replacing them with images generated using an AI-generation tool, DALL-E. We use object and place detection to generate captions of the raw images, and use the caption as the image generation prompt (e.g., “A realistic photo for egg tart in the kitchen”). We manually removed all images with people from the output.

## How this dataset can be used

We intend to use this dataset to demostrate question-answer systems over digital service data. With the underlying data, the QA system, such as a personalized version of ChatGPT, should be able to answer questions such as:
* “When was the last time I visited Japan”,
* “Show me some photos of plants in my neighborhood”,
* “How many times I exercise during the month X”, etc.

## Example records

Books:

| time               | book_name           | img_url                                                                                       | id       |
|--------------------|---------------------|-----------------------------------------------------------------------------------------------|----------|
| 2022-12-19 4:37:00 | I Am a Strange Loop | https://img1.od-cdn.com/ImageType-100/0887-1/{A6AA81F6-9242-4793-8AB0-A5C8B5DBDB66}Img100.jpg | books_26 |

Exercise: 

| start_time                | end_time                  | textDescription           | duration    | distance | calories | outdoor | temperature | id          |
|---------------------------|---------------------------|---------------------------|-------------|----------|----------|---------|-------------|-------------|
| 2019-03-02 08:00:34-08:00 | 2019-03-02 08:39:59 -0800 | 08:00: running 39 minutes | 39.40743217 | 0        | 0        | 1       |             | exercise_35 |

Photos:

| start_time                | end_time                  | textDescription   | address                                                                   | lat     | long     | details                                                                                                                                                                                                                                    | img_url                                                                                              |
|---------------------------|---------------------------|-------------------|---------------------------------------------------------------------------|---------|----------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------|
| 2019-03-28 20:38:13+09:00 | 2019-03-28 20:38:13+09:00 | from Google Photo | Asahi Shokudo, 龍土町美術館通り, Roppongi, Minato, Tokyo, 106-0033, Japan | 35.6644 | 139.7301 | {'objects': ['Tsukudani', 'Scroll', 'Document', 'Receipt', 'Homework', 'paper', 'menu', 'date', 'sheet, flat solid', 'shoji'], 'places': ['restaurant', 'hotel room', 'archive', 'sushi bar', 'restaurant kitchen'], 'tags': ['document']} | digital_data/images/google_photos/part 2/Google Photos/Photos from 2019/IMG_6955.HEIC.compressed.jpg |

Purchase:

| time                | purchase_id         | productName                                             | productPrice | productQuantity | id         |
|---------------------|---------------------|---------------------------------------------------------|--------------|-----------------|------------|
| 2022-07-26 16:29:16 | 114-9774413-4401831 | Dr. Earth 713 Organic 9 Fruit Tree Fertilizer, 12-Pound | 22.53        | 1               | purchase_0 |
| 2022-07-26 16:28:27 | 114-9230659-7782623 | Miracle-Gro Citrus, Avocado, & Mango Food, 20 lb.       | 15.4         | 1               | purchase_1 |

Streaming:

| start_time          | end_time            | artist              | track                                                              | playtimeMs | spotify_link | id          |
|---------------------|---------------------|---------------------|--------------------------------------------------------------------|------------|--------------|-------------|
| 2022-05-31 11:35:00 | 2022-05-31 11:35:00 | Lex Fridman Podcast | #282 – David Buss: Sex, Dating, Relationships, and Sex Differences | 18000      |              | streaming_0 |

Places:

| start_time | end_time | TextDescription | start_address | start_lat | start_long | end_address | end_lat | end_long | id |
|------------|----------|-----------------|---------------|-----------|------------|-------------|---------|----------|----|
| 2019-04-20 13:02:58-07:00 | 2019-04-20 13:02:58-07:00 | Texas Home on Greg Street | 2966, Greg Street, Randall County, Texas, 79015, United States | 35.03744471122455 | -101.90857274320028 | 2966, Greg Street, Randall County, Texas, 79015, United States | 35.03744471122455 | -101.90857274320028 | places_27422 |
