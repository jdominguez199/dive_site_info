from openmeteopy import OpenMeteo
from openmeteopy.hourly import HourlyMarine
from openmeteopy.options import MarineOptions

import logging


class location_info:
    longitude = None
    latitude =None
    logger_object=None
    site_name = None
    manager_objects = {
        "swell_period": None,
        "swell_direction" : None,
        "wave_height": None,
        "wave_direction": None,
        "wave_period": None
    }
    ideal_values = {
        "swell_period": None,
        "swell_direction" : None,
        "wave_height": None,
        "wave_direction": None,
        "wave_period": None
    }
    swell_parameters={
        "ideal_loc_max": 1,
        "med_loc_max": 2,
        "high_loc_max":3
    }
    weight_of_items={
        "wave_height":4,
        "wave_period":4,
        "wave_direction":3,
    }
    wind_directions={"SW":[247,203], "W":[248,292],"NW":[293,337],"N":[22, 338], "NE":[23,67],"E":[68,112],"SE":[113,157], "S":[158,202]}
    wave_total_weight=[]
    breakdown_days=[]
    def __init__(self, longitude, latitude, logger_obj, site_name):
        self.longitude = longitude
        self.latitude = latitude
        self.logger_object=logger_obj
        self.site_name=site_name

    def update_data(self):
        #marine info
        hourly = HourlyMarine()
        options = MarineOptions(self.longitude,self.latitude)
        mgr = OpenMeteo(options, hourly.all())
    
        # Download data
        meteo = mgr.get_dict()
        # self.manager_objects["swell_period"]= meteo["swell_wave_period"]
        # self.manager_objects["swell_direction"] = meteo["swell_wave_direction"]
        self.manager_objects["wave_height"] = meteo["hourly"]["wave_height"]
        self.manager_objects["wave_direction"] = meteo["hourly"]["wave_direction"]
        self.manager_objects["wave_period"] = meteo["hourly"]["wave_period"]
    
    def calc_site_weight(self):
        added_total_calc_weight=0
        val_mul_sum=0
        ideal_index_val=0
        true_wind_direction_str=""
        for item in self.weight_of_items.keys():
            added_total_calc_weight+=self.weight_of_items[item]
        # print(self.manager_objects)
        for index_val, name in enumerate(self.manager_objects["wave_height"]):
            for item in self.weight_of_items.keys():
                print(index_val)
                print(item)
                if(type(self.ideal_values[item])==str):
                    for  key in self.wind_directions.keys():
                        direction_degrees=self.wind_directions[key]
                        if(self.manager_objects[item][index_val]>= direction_degrees[0] and self.manager_objects[item][index_val]<= direction_degrees[1]):
                            true_wind_direction_str=key
                    print(self.wind_directions[self.ideal_values[item]])
                    self.wave_total_weight.append(self.wind_directions[self.ideal_values[item]]-self.wind_directions[true_wind_direction_str])
                else:
                    if(self.manager_objects[item][index_val] > self.ideal_values[item]):
                        val_mul_sum+=self.ideal_values[item]-self.manager_objects[item][index_val]
                    else:
                        val_mul_sum=0
                self.wave_total_weight.append(val_mul_sum/added_total_calc_weight)

        print(self.wave_total_weight)


    def set_ideal_max(self, item,value):
        self.ideal_values[item]=value


logger = logging.getLogger(__name__)
logging.basicConfig(filename='weather_data_app.log', level=logging.INFO)

location_list=[]

temp_loc=location_info(42.604408, -70.676550,logger, "halfmoon") # half moon beach
temp_loc.set_ideal_max("wave_height",1)
temp_loc.set_ideal_max("wave_period",3)
temp_loc.set_ideal_max("wave_direction","NE")

location_list.append(temp_loc)

for location in location_list:
    location.update_data()
    location.calc_site_weight()


# longitude = 42.275
# latitude = -70.035

# hourly = HourlyMarine()
# options = MarineOptions(longitude,latitude)

# mgr = OpenMeteo(options, hourly.all())

# # Download data
# meteo = mgr.get_dict()

# print(meteo