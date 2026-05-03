from collect_site_data import Location_info
from csv_handler import Handle_csv
from google_sheet_handler import Google_sheet_handler
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(filename='weather_data_app.log', level=logging.INFO)
location_class = Location_info()
csv_class = Handle_csv()
google_class = Google_sheet_handler("credentials.json", "dive site info")
site_list = google_class.read_site_info_sheet()
for info in site_list:
    location_class.create_new_site(info.latitude, info.longitude, info.site_name, info)
location_list=[]


updated_data = location_class.update_hourly_marine_data()
daily_list_scores = location_class.daily_am_pm_breakdown(updated_data)
google_class.write_hourly_data_sheet(updated_data)
google_class.write_daily_data_sheet(daily_list_scores)
#csv_class.create_data_csv(updated_data, "result.csv")