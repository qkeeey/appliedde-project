New York City Airbnb Open Data
Airbnb listings and metrics in NYC, NY, USA (2019)

About Dataset
Context
Since 2008, guests and hosts have used Airbnb to expand on traveling possibilities and present more unique, personalized way of experiencing the world. This dataset describes the listing activity and metrics in NYC, NY for 2019.

Content
This data file includes all needed information to find out more about hosts, geographical availability, necessary metrics to make predictions and draw conclusions.

Acknowledgements
This public dataset is part of Airbnb, and the original source can be found on this website.

Inspiration
What can we learn about different hosts and areas?
What can we learn from predictions? (ex: locations, prices, reviews, etc)
Which hosts are the busiest and why?
Is there any noticeable difference of traffic among different areas and what could be the reason for it?
We have only one csv file as dataset:
/kaggle/input/datasets/dgomonov/new-york-city-airbnb-open-data/AB_NYC_2019.csv


====================================================================================================
DATASET SHAPE
====================================================================================================
Number of rows: 48895
Number of columns: 16

====================================================================================================
HEADER ROW / COLUMN NAMES
====================================================================================================
id, name, host_id, host_name, neighbourhood_group, neighbourhood, latitude, longitude, room_type, price, minimum_nights, number_of_reviews, last_review, reviews_per_month, calculated_host_listings_count, availability_365

====================================================================================================
COLUMN DATA TYPES
====================================================================================================
id: int64
name: object
host_id: int64
host_name: object
neighbourhood_group: object
neighbourhood: object
latitude: float64
longitude: float64
room_type: object
price: int64
minimum_nights: int64
number_of_reviews: int64
last_review: object
reviews_per_month: float64
calculated_host_listings_count: int64
availability_365: int64

====================================================================================================
FIRST 3 ROWS
====================================================================================================
  id                                name  host_id host_name neighbourhood_group neighbourhood  latitude  longitude       room_type  price  minimum_nights  number_of_reviews last_review  reviews_per_month  calculated_host_listings_count  availability_365
2539  Clean & quiet apt home by the park     2787      John            Brooklyn    Kensington  40.64749  -73.97237    Private room    149               1                  9  2018-10-19               0.21                               6               365
2595               Skylit Midtown Castle     2845  Jennifer           Manhattan       Midtown  40.75362  -73.98377 Entire home/apt    225               1                 45  2019-05-21               0.38                               2               355
3647 THE VILLAGE OF HARLEM....NEW YORK !     4632 Elisabeth           Manhattan        Harlem  40.80902  -73.94190    Private room    150               3                  0         NaN                NaN                               1               365

====================================================================================================
MIDDLE 3 ROWS
====================================================================================================
      id                                              name  host_id host_name neighbourhood_group      neighbourhood  latitude  longitude    room_type  price  minimum_nights  number_of_reviews last_review  reviews_per_month  calculated_host_listings_count  availability_365
19677221 Private, Spacious Brooklyn Room in Prime Location 88351271    Jordan            Brooklyn           Bushwick  40.69817  -73.92819 Private room     45               3                 14  2018-08-02               0.58                               1                 0
19677284                              Room in Williamsburg 63336737      Juan            Brooklyn       Williamsburg  40.70994  -73.95243 Private room     50               4                  3  2018-08-13               0.12                               1                 0
19677579          Sunny room in historic Bedstuy, Brooklyn   124171    Miguel            Brooklyn Bedford-Stuyvesant  40.68533  -73.94231 Private room     60               1                  1  2018-07-08               0.08                               1                 0

====================================================================================================
LAST 3 ROWS
====================================================================================================
      id                                              name  host_id     host_name neighbourhood_group  neighbourhood  latitude  longitude       room_type  price  minimum_nights  number_of_reviews last_review  reviews_per_month  calculated_host_listings_count  availability_365
36485431           Sunny Studio at Historical Neighborhood 23492952 Ilgar & Aysel           Manhattan         Harlem  40.81475  -73.94867 Entire home/apt    115              10                  0         NaN                NaN                               1                27
36485609              43rd St. Time Square-cozy single bed 30985759           Taz           Manhattan Hell's Kitchen  40.75751  -73.99112     Shared room     55               1                  0         NaN                NaN                               6                 2
36487245 Trendy duplex in the very heart of Hell's Kitchen 68119814    Christophe           Manhattan Hell's Kitchen  40.76404  -73.98933    Private room     90               7                  0         NaN                NaN                               1                23

====================================================================================================
MISSING VALUES PER COLUMN
====================================================================================================
id: 0
name: 16
host_id: 0
host_name: 21
neighbourhood_group: 0
neighbourhood: 0
latitude: 0
longitude: 0
room_type: 0
price: 0
minimum_nights: 0
number_of_reviews: 0
last_review: 10052
reviews_per_month: 10052
calculated_host_listings_count: 0
availability_365: 0