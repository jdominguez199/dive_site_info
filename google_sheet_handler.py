import gspread
from oauth2client.service_account import ServiceAccountCredentials
from site_info import Site_Info
class Google_sheet_handler:
    client = None
    sheet_name=None
    # Define the scope
    scope = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]

    def __init__(self, credentials_file, google_sheet_name):
        '''
        For the google sheet handler to be created the file containing the credentials has to be proved as well as name of the sheet where the data should be placed

        credentials_file: The file where the credentials for accessing the sheet is defined

        google_sheet_name: The name of the workbook where the data should the read or written to
        '''
        # Authenticate with credentials
        credentials = ServiceAccountCredentials.from_json_keyfile_name(credentials_file, self.scope)
        self.client = gspread.authorize(credentials)

        self.sheet_name = google_sheet_name

    def write_hourly_data_sheet(self, data):
        ''' 
        This will cause the data being given to write the data to the sheet specifically the first sheet

        data: The data that should be placed in the google sheet
        '''
        # Open the Google Sheet
        sheet = self.client.open(self.sheet_name).worksheet("hourly_values")

        sheet.update([data.columns.values.tolist()] + data.values.tolist())

    def write_daily_data_sheet(self, data):
        ''' 
        This will cause the data being given to write the data to the sheet specifically the first sheet

        data: The data that should be placed in the google sheet
        '''
        # Open the Google Sheet
        sheet = self.client.open(self.sheet_name).worksheet("daily_values")

        sheet.update([data.columns.values.tolist()] + data.values.tolist())

    def read_site_info_sheet(self):
        ''' 
        This will cause the data being given to write the data to the sheet specifcally the first sheet

        data: The data that should be placed in the google sheet
        '''
        # Open the Google Sheet
        sheet = self.client.open(self.sheet_name).worksheet("site_info")

        all_items = sheet.get_all_values()

        site_info_dict = self.convert_list_to_dict(all_items)

        return site_info_dict

    def convert_list_to_dict(self, data_list):
        site_info_list=[]
        for index,item in enumerate(data_list):
            if(index>1):
                new_site = Site_Info(item[0],item[1], item[2])
                new_site.set_wave_height(item[3],item[4])
                new_site.set_wave_period(item[5],item[6])
                new_site.set_wind_direction(item[7],item[8],item[9])
                new_site.set_wind_speed(item[10],item[11])
                site_info_list.append(new_site)

        return site_info_list