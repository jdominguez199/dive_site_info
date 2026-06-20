#This is define a object to help store info related to a dive site as well a process data related data becompred to the dive site
# The scores related to what the default values should be
class Site_Info:
    site_name=""
    latitude=0
    longitude=0
    wave_direction={"ideal":[], "suboptimal":[], "not_feasable":[]}
    wave_height={"calm_starting_0":1, "moderate":3}
    wave_period={"choppy_starting_0":3,"potential_discomfort":7}
    wind_direction={"ideal":[], "suboptimal":[], "not_feasable":[]}
    wind_speed={"light_starting_0":7, "moderate":16}
    def __init__(self, site_name, latitude, longitude):
        '''
        Initial information to set up the object for the site

        :param site_name: Name of the site
        :type site_name: string
        :param latitude: Latitude coordinates of the site must be in the water
        :type latitude: int
        :param not_feasable: Longitude coordinates of the site must be in the water
        :type not_feasable: int
        '''
        self.site_name=site_name
        self.latitude =latitude
        self.longitude=longitude
    
    def set_wave_direction(self, ideal, suboptimal, not_feasable):
        '''
        Set the wave direction in this class

        :param ideal: A comma separated list of directions that are ideal
        :type ideal: string
        :param suboptimal: A comma separated list of directions that are suboptimal
        :type suboptimal: string
        :param not_feasable: A comma separated list of directions that are not_feasable
        :type not_feasable: string
        '''
        self.wave_direction["ideal"]=self.str2list(ideal)
        self.wave_direction["suboptimal"]=self.str2list(suboptimal)
        self.wave_direction["not_feasable"]=self.str2list(not_feasable)
    
    def set_wave_height(self, calm_starting_0, moderate):
        '''
        Set the wave direction in this class. Anything above the moderate 
        height is considered to high and will get the highest score

        :param calm_starting_0: Max height considered calm
        :type ideal: int
        :param moderate: Max height considered moderate
        :type moderate: int
        '''
        if(not calm_starting_0==""):
            self.wave_height["calm_starting_0"]=calm_starting_0
        if(not moderate==""):
            self.wave_height["moderate"]=moderate

    def set_wave_period(self, choppy_starting_0, potential_discomfort):
        '''
        Set the wave period setting for when the water is too choppy or to will cause some discomfort

        :param choppy_starting_0: Max value for the period that is considered making the water choppy
        :type ideal: int
        :param potential_discomfort: Max value for the period that is considered making the water a little uncomfortable
        :type potential_discomfort: int
        '''
        if(not choppy_starting_0==""):
            self.wave_period["choppy_starting_0"]=choppy_starting_0
        if(not potential_discomfort==""):
            self.wave_period["potential_discomfort"]=potential_discomfort

    def set_wind_direction(self, ideal, suboptimal, not_feasable):
        '''
        Set the wind direction for this site of what is considered  good to making this site not feasable

        :param ideal: A comma separated list of directions that are ideal
        :type ideal: string
        :param suboptimal: A comma separated list of directions that are suboptimal
        :type suboptimal: string
        :param not_feasable: A comma separated list of directions that are not_feasible
        :type not_feasable: string
        '''
        self.wind_direction["ideal"]=self.str2list(ideal)
        self.wind_direction["suboptimal"]=self.str2list(suboptimal)
        self.wind_direction["not_feasable"]=self.str2list(not_feasable)

    def set_wind_speed(self, light_starting_0, moderate):
        '''
        Set the wind speed for the wind being to strong or divisible

        :param light_starting_0: Max wind speed for being considered light
        :type ideal: int
        :param moderate: Max wind speed for being considered moderate
        :type moderate: int
        '''
        if(not light_starting_0==""):
            self.wind_speed["light_starting_0"]=light_starting_0
        if(not moderate==""):
            self.wind_speed["moderate"]=moderate


    def str2list(self, input_str):
        '''
        Convert a comma separated string into a list with spaces removed

        :param input_str: The string to be separated
        :type input_str: string
        :return: A list of the value that were separated by commas from the input string
        '''
        results_list=[]
        split_list=input_str.split(",")
        for item in split_list:
            results_list.append(item.replace(" ",""))
        return results_list
    

    def get_wave_height_score(self,wave_height):
        '''
        Get a score based on wave height

        :param wave_height: The wave height to be checked
        :type wave_height: int
        :return: The score based on the wave height
        '''
        wave_height_score=5 # Score it is not moderate or calm
        if(self.wave_height["calm_starting_0"] >= wave_height):
            wave_height_score=0
        elif(self.wave_height["moderate"] >= wave_height):
            wave_height_score=1
        return wave_height_score
    
    def get_wave_direction_score(self,wave_direction, wind_direction):
        '''
        Get a score based on wave direction based on if the wind and the wave are conflicting

        :param wave_direction: The wave direction to be checked
        :param wind_direction: The direction of the wind uesd to check if waves are the opposite direction
        :type wave_direction: string
        :return: The score based on the wave direction
        '''
        opposite_direction={"N":"S","NE":"SW", "E":"W", "SE":"NW", "S":"N", "SW":"NE", "W":"E", "NW":"SE"}
        if(opposite_direction[wind_direction] == wave_direction):
            wave_direction_score=2 # score is direction is wrong
        else:
            wave_direction_score=0
        return wave_direction_score
    
    def get_wave_period_score(self,wave_period):
        '''
        Get a score based on wave period

        :param wave_period: The wave period to be checked
        :type wave_period: int
        :return: The score based on the wave period
        '''
        wave_period_score=0 # Score it is not choppy or profit discomfort
        if(self.wave_period["choppy_starting_0"] >= wave_period):
            wave_period_score=2
        elif(self.wave_period["potential_discomfort"] >= wave_period):
            wave_period_score=1
        return wave_period_score
    
    def get_wind_speed_score(self, wind_speed):
        '''
        Get a score based on wind speed

        :param wind_speed: The wave speed to be checked
        :type wind_speed: int
        :return: The score based on the wave speed
        '''
        wind_speed_score=2 # Score it is not moderate or calm
        if(self.wind_speed["light_starting_0"] >= wind_speed):
            wind_speed_score=0
        elif(self.wind_speed["moderate"] >= wind_speed):
            wind_speed_score=1
        return wind_speed_score
    
    def get_wind_dir_score(self, wind_direction):
        '''
        Get a score based on wind direction

        :param wind_direction: The wind direction to be checked
        :type wind_direction: string
        :return: The score based on the wind direction
        '''
        wind_direction_score=5
        if(wind_direction in self.wind_direction["ideal"] ):
            wind_direction_score=0
        elif(wind_direction in self.wind_direction["suboptimal"]):
            wind_direction_score=2
        return wind_direction_score