import openmeteo_requests
import requests_cache
from retry_requests import retry
from datetime import datetime, timezone, timedelta
from suntime import Sun
import statistics
import pandas as pd

class Location_info:
    longitude = []
    latitude =[]
    site_name_list = []
    site_info_dicts = []
    resulting_string=""
    low_tide_height = 0
    wave_total_weight=[]
    breakdown_days=[]
    timezone="America/New_York"

    current_data=None
    
    def create_new_site(self, latitude, longitude, site_name, data_obj):
        self.longitude.append(longitude)
        self.latitude.append(latitude)
        self.site_name_list.append(site_name)
        self.site_info_dicts.append(data_obj)

    # grabbing the direction the wind is coming from
    def convert_num_dir_to_simple_string_dir(self,degree):
        int_degree = int(degree)
        # This was made taking a circle splitting it 8 ways
        wind_directions={"SW":[247,203], "W":[248,292],"NW":[293,337],"N":[22, 338], "NE":[23,67],"E":[68,112],"SE":[113,157], "S":[158,202]}
        for key in wind_directions.keys():
            min_max_degree = wind_directions[key]
            # North needs a special case it is a little weird since the range is 338 to 22
            if key == "S":
                if(int_degree <= min_max_degree[0] and int_degree >= 0) or (int_degree >= min_max_degree[1] and int_degree <= 360):
                    return key
            else:
                if (int_degree <= min_max_degree[0] and int_degree >= min_max_degree[1]) or (int_degree >= min_max_degree[0] and int_degree <= min_max_degree[1]):
                    return key
        
        print(f"something is wrong unable to find direction given degree: {degree}" )

    def update_hourly_marine_data(self):
        ## string format
        ## site_name, date, time
        #marine info /wave_height, wave period, wave direction

        # Setup the Open-Meteo API client with cache and retry on error
        cache_session = requests_cache.CachedSession('.cache', expire_after = 3600)
        retry_session = retry(cache_session, retries = 5, backoff_factor = 0.2)
        openmeteo = openmeteo_requests.Client(session = retry_session)
        openmeteo = openmeteo_requests.Client()

        # Make sure all required weather variables are listed here
        # The order of variables in hourly or daily is important to assign them correctly below
        url = "https://marine-api.open-meteo.com/v1/marine"
        params = {
            "latitude": self.latitude,
            "longitude": self.longitude,
            "hourly": ["wave_height", "wave_direction", "wave_period", "sea_level_height_msl"],
            "timezone": self.timezone,
            "length_unit": "imperial",
        }
        responses = openmeteo.weather_api(url, params=params)

        holding_data_frame=pd.DataFrame()
        # Process first location. Add a for-loop for multiple locations or weather models
        for response_index, response in enumerate(responses):
            print("grabbing marine data")
            print(f"Coordinates: {response.Latitude()}°N {response.Longitude()}°E")
            print(f"Elevation: {response.Elevation()} m asl")
            print(f"Timezone: {response.Timezone()}{response.TimezoneAbbreviation()}")
            print(f"Timezone difference to GMT+0: {response.UtcOffsetSeconds()}s")

            # Process hourly data. The order of variables needs to be the same as requested.
            hourly = response.Hourly()
            print(hourly.Variables)
            hourly_wave_height = hourly.Variables(0).ValuesAsNumpy()
            hourly_wave_direction = hourly.Variables(1).ValuesAsNumpy()
            hourly_wave_period = hourly.Variables(2).ValuesAsNumpy()
            hourly_sea_level_height_msl = hourly.Variables(3).ValuesAsNumpy()
            
            hourly_data = {"date": pd.date_range(
                start = pd.to_datetime(hourly.Time() + response.UtcOffsetSeconds(), unit = "s", utc = True),
                end =  pd.to_datetime(hourly.TimeEnd() + response.UtcOffsetSeconds(), unit = "s", utc = True),
                freq = pd.Timedelta(seconds = hourly.Interval()),
                inclusive = "left"
            ).strftime("%Y-%m-%d %H:%M")}
            site_name =[]
            location =[]
            for index, date in enumerate(hourly_data["date"]):
                site_name.append(self.site_name_list[response_index]) #tag all the items with link their data to a site
                location.append(f"{self.latitude[response_index]}, {self.longitude[response_index]}")

            hourly_data["site_name"] =  site_name
            hourly_data["location"] = location
            hourly_data["wave_height"] = hourly_wave_height
            wave_height_score = []
            for height in hourly_data["wave_height"]:
                wave_height_score.append(self.site_info_dicts[response_index].get_wave_height_score(height))
            hourly_data["wave_height_score"] = wave_height_score
            hourly_data["wave_direction"] = hourly_wave_direction
            hourly_data["wave_direction_str"] = [self.convert_num_dir_to_simple_string_dir(x) for x in hourly_data["wave_direction"]]
            #wave direction score will be calculated once wind direction is gathered
            hourly_data["wave_period"] = hourly_wave_period
            wave_period_score=[]
            for period in hourly_data["wave_period"]:
                wave_period_score.append(self.site_info_dicts[response_index].get_wave_period_score(period))
            hourly_data["wave_period_score"] = wave_period_score
            hourly_data["sea_level_height_msl"] = hourly_sea_level_height_msl
            min_wave_height= abs(min(hourly_data["sea_level_height_msl"]))
            hourly_data["sea_level_height_msl"] = [x + min_wave_height for x in hourly_data["sea_level_height_msl"]]

            hourly_data = self.update_hourly_land_data(hourly_data, response.Latitude(), response.Longitude())
            total_score=[]
            for index, period in enumerate(hourly_data["wave_period"]):
                total_score.append(hourly_data["wave_period_score"][index] + hourly_data["wave_direction_score"][index]+hourly_data["wave_height_score"][index]+hourly_data["wind_speed_score"][index]+hourly_data["wind_direction_score"][index])
            hourly_data["total_score_hourly"] = total_score

            hourly_dataframe = pd.DataFrame(data = hourly_data)
            if(holding_data_frame.empty):
                holding_data_frame = hourly_dataframe
            else:
                holding_data_frame = pd.concat([holding_data_frame, hourly_dataframe], ignore_index=True)
        return holding_data_frame
    
    def daily_am_pm_breakdown(self, hourly_data):
        '''
        This will take in a list of hourly data with the time being a string of format YYYY-MM-DD HH:mm and break down the average if you go diving 
        in the morning or towards the evening sunrise to noon and noon to sunset
        '''
        working_on_date=datetime(1999,1,2) # This is an old time used in order string format is able to produce the hour and date as needed
        site_name = ""
        data_lists={}
        am_pm_list=["am", "pm"] # This is used so we can iterate over the bigger dict and add rows as needed

        daily_list=self.create_new_daily_data()
        sun_rise_time=None
        sun_set_time=None
        new_timezone = timezone(timedelta(hours=-4))
        for data in hourly_data.itertuples(index=False):
            split_location = data.location.split(", ")
            row_time=datetime.strptime(data.date, "%Y-%m-%d %H:%M")
            #Moving onto a differnt date store the data from the laast day
            if(working_on_date != row_time.date()):
                if(working_on_date.year != 1999 ):                        
                    for time_period in am_pm_list:
                        new_row = self.create_new_daily_data(working_on_date.strftime("%Y-%m-%d"), site_name, time_period, data_lists)
                        if(daily_list.empty):
                            daily_list=new_row
                        else:
                            daily_list=pd.concat([daily_list,new_row])
        
                #converted_dt = aware_dt.astimezone(new_timezone)# sun_rise_time=sun_time.get_sunrise_time()
                sun_time=Sun(float(split_location[0]), float(split_location[1]))
                sun_rise_time=sun_time.get_sunrise_time()
                sun_set_time=sun_time.get_sunset_time()
                sun_rise_time = sun_rise_time.astimezone(new_timezone)# sun_rise_time=sun_time.get_sunrise_time()
                sun_set_time = sun_set_time.astimezone(new_timezone)# sun_rise_time=sun_time.get_sunrise_time()
                data_lists.clear()
                site_name=data.site_name
            working_on_date=row_time.date()
            noon_time = datetime(row_time.year, row_time.month, row_time.day, 12, 0)
            if(row_time.hour > sun_rise_time.hour and row_time <= noon_time):
                data_lists = self.append_new_data_am_pm_list(data_lists, "am", data)
            elif(row_time.hour < sun_set_time.hour and row_time > noon_time):
                data_lists = self.append_new_data_am_pm_list(data_lists, "pm", data)
        #Add the data from the most recent day and site
        for time_period in am_pm_list:
            new_row = self.create_new_daily_data(working_on_date.strftime("%Y-%m-%d"), site_name, time_period, data_lists)
            daily_list=pd.concat([daily_list,new_row])
        
 
        return daily_list


    def create_new_daily_data(self,day=None, site_name=None, time_period=None, data_dict=None):
        if(data_dict == None):
            return pd.DataFrame({"date":[], "site":[], "time_period":[],\
                                    "Overall Score":[], \
                                    "wave_direction":[],\
                                    "wave_height(ft)":[],\
                                    "wave_period(s)":[],\
                                    "wind_speed(kn)":[],\
                                    "wind_direction":[],\
                                    "air temp(F)":[]})
        else:
            return pd.DataFrame({"date": [day], "site":[site_name], "time_period":time_period, \
                                    "Overall Score": [statistics.mean(data_dict[f"{time_period}_list"])], \
                                    "wave_direction": [self.convert_num_dir_to_simple_string_dir(statistics.mean(data_dict[f"{time_period}_wave_direction"]))],\
                                    "wave_height(ft)":[statistics.mean(data_dict[f"{time_period}_wave_height_list"])],\
                                    "wave_period(s)":[statistics.mean(data_dict[f"{time_period}_wave_period_list"])],\
                                    "wind_speed(kn)":[statistics.mean(data_dict[f"{time_period}_wind_speed_list"])],\
                                    "wind_direction": [self.convert_num_dir_to_simple_string_dir(statistics.mean(data_dict[f"{time_period}_wind_direction_list"]))],\
                                    "air temp(F)":[statistics.mean(data_dict[f"{time_period}_temp_list"])]})

    def append_new_data_am_pm_list(self, orginal_dict, time_period, new_data):
        appended_dict=orginal_dict
        # is the dict does not have the time period list in it create the needed items for the time period
        if(f"{time_period}_list" not in orginal_dict):
            appended_dict[f"{time_period}_list"]=[]
            appended_dict[f"{time_period}_wave_direction"]=[]
            appended_dict[f"{time_period}_wave_height_list"]=[]
            appended_dict[f"{time_period}_wave_period_list"]=[]
            appended_dict[f"{time_period}_wind_speed_list"]=[]
            appended_dict[f"{time_period}_wind_direction_list"]=[]
            appended_dict[f"{time_period}_temp_list"]=[]
            appended_dict[f"{time_period}_precipitation_probability_list"]=[]
        # add the data
        appended_dict[f"{time_period}_list"].append(new_data.total_score_hourly)
        appended_dict[f"{time_period}_wave_direction"].append(new_data.wave_direction)
        appended_dict[f"{time_period}_wave_height_list"].append(new_data.wave_height)
        appended_dict[f"{time_period}_wave_period_list"].append(new_data.wave_period)
        appended_dict[f"{time_period}_wind_speed_list"].append(new_data.wind_speed)
        appended_dict[f"{time_period}_wind_direction_list"].append(new_data.wind_direction)
        appended_dict[f"{time_period}_temp_list"].append(new_data.air_temperature)

        return appended_dict

    def update_hourly_land_data(self, initial_list, latitude, longitude):
        modifiable_list=initial_list
        # Setup the Open-Meteo API client with cache and retry on error
        cache_session = requests_cache.CachedSession('.cache', expire_after = 3600)
        retry_session = retry(cache_session, retries = 5, backoff_factor = 0.2)
        openmeteo = openmeteo_requests.Client(session = retry_session)

        # Make sure all required weather variables are listed here
        # The order of variables in hourly or daily is important to assign them correctly below
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "hourly": ["temperature_2m", "wind_speed_10m", "wind_direction_10m"],
            "timezone": self.timezone,
            "wind_speed_unit": "kn",
            "temperature_unit": "fahrenheit",
            "models": "gfs_seamless"
        }
        responses = openmeteo.weather_api(url, params = params)

        # Process first location. Add a for-loop for multiple locations or weather models
        for response_index, response in enumerate(responses):
            print("grabbing land data")
            print(f"Coordinates: {response.Latitude()}°N {response.Longitude()}°E")
            print(f"Elevation: {response.Elevation()} m asl")
            print(f"Timezone: {response.Timezone()}{response.TimezoneAbbreviation()}")
            print(f"Timezone difference to GMT+0: {response.UtcOffsetSeconds()}s")

            # Process hourly data. The order of variables needs to be the same as requested.
            hourly = response.Hourly()
            hourly_temperature_2m = hourly.Variables(0).ValuesAsNumpy()
            hourly_wind_speed_10m = hourly.Variables(1).ValuesAsNumpy()
            hourly_wind_direction_10m = hourly.Variables(2).ValuesAsNumpy()

            modifiable_list["air_temperature"] = hourly_temperature_2m
            modifiable_list["wind_speed"] = hourly_wind_speed_10m
            wind_speed_score = []
            for height in modifiable_list["wind_speed"]:
                wind_speed_score.append(self.site_info_dicts[response_index].get_wind_speed_score(height))
            modifiable_list["wind_speed_score"] = wind_speed_score
            modifiable_list["wind_direction"] = hourly_wind_direction_10m
            modifiable_list["wind_direction_str"] = [self.convert_num_dir_to_simple_string_dir(x) for x in modifiable_list["wind_direction"]]
            wind_direction_score=[]
            for direction in modifiable_list["wind_direction_str"]:
                wind_direction_score.append(self.site_info_dicts[response_index].get_wind_dir_score(direction))
            modifiable_list["wind_direction_score"] = wind_direction_score
            wave_direction_score=[]
            for index, direction in enumerate(modifiable_list["wave_direction_str"]):
                wave_direction_score.append(self.site_info_dicts[response_index].get_wave_direction_score(direction, modifiable_list["wind_direction_str"][index]))
            modifiable_list["wave_direction_score"] = wave_direction_score

            return modifiable_list