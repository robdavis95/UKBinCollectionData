import urllib.request
from datetime import datetime

import pandas as pd
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.wait import WebDriverWait

from uk_bin_collection.uk_bin_collection.common import *
from uk_bin_collection.uk_bin_collection.get_bin_data import AbstractGetBinDataClass


class CouncilClass(AbstractGetBinDataClass):
    """
    Concrete classes have to implement all abstract operations of the base
    class. They can also override some operations with a default
    implementation.
    """

    def parse_data(self, page: str, **kwargs) -> dict:
        driver = None
        try:
            """
            Parse council provided CSVs to get the latest bin collections for address
            """

            user_uprn = kwargs.get("uprn")
            user_postcode = kwargs.get("postcode")
            web_driver = kwargs.get("web_driver")
            headless = kwargs.get("headless")
            check_uprn(user_uprn)
            check_postcode(user_postcode)
            # Create Selenium webdriver
            page = f"https://www.leeds.gov.uk/residents/bins-and-recycling/check-your-bin-day"

            driver = create_webdriver(web_driver, headless, None, __name__)
            driver.get(page)

            wait = WebDriverWait(driver, 60)
            postcode_box = wait.until(
                EC.element_to_be_clickable(
                    (
                        By.ID,
                        "ctl00_ctl48_g_eea1a8ba_4306_488e_96f2_97f22038e29f_ctl00_txtPostCode",
                    )
                )
            )
            postcode_box.send_keys(user_postcode)
            postcode_btn_present = wait.until(
                EC.presence_of_element_located(
                    (
                        By.ID,
                        "ctl00_ctl48_g_eea1a8ba_4306_488e_96f2_97f22038e29f_ctl00_btnSearchAddress",
                    )
                )
            )
            postcode_btn = wait.until(
                EC.element_to_be_clickable(
                    (
                        By.XPATH,
                        '//*[@id="ctl00_ctl48_g_eea1a8ba_4306_488e_96f2_97f22038e29f_ctl00_btnSearchAddress"]',
                    )
                )
            )

            postcode_btn.send_keys(Keys.ENTER)

            dropdown_present = wait.until(
                EC.presence_of_element_located(
                    (
                        By.XPATH,
                        '//*[@id="ctl00_ctl48_g_eea1a8ba_4306_488e_96f2_97f22038e29f_ctl00_ddlAddressList"]/option',
                    )
                )
            )
            address_dropdown = wait.until(
                EC.element_to_be_clickable(
                    (
                        By.ID,
                        "ctl00_ctl48_g_eea1a8ba_4306_488e_96f2_97f22038e29f_ctl00_ddlAddressList",
                    )
                )
            )

            dropdown_present.click()

            dropdownSelect = Select(address_dropdown)
            dropdownSelect.select_by_value(str(user_uprn))
            results = wait.until(
                EC.presence_of_element_located(
                    (
                        By.ID,
                        "ctl00_ctl48_g_eea1a8ba_4306_488e_96f2_97f22038e29f_ctl00_BinResultsDetails",
                    )
                )
            )

            data = {"bins": []}  # dictionary for data
            soup = BeautifulSoup(driver.page_source, "html.parser")

            bin_types = soup.find_all("ul", class_="binCollectionTimesList")

            for bin_collection_dates in bin_types:

                bin_collection_list = bin_collection_dates.find_all("li")

                if bin_collection_list:
                    collection_dates = [
                        date.text.strip() for date in bin_collection_list
                    ]

                    # Convert the collection dates to the desired format
                    formatted_dates = [
                        datetime.strptime(date, "%A %d %b %Y").strftime(date_format)
                        for date in collection_dates
                    ]

                    # Extract the type of bin from the header
                    bin_type = bin_collection_dates.find_previous("h3").text.split()[0]

                    # Adding data to the 'bins' dictionary for each date
                    for date in formatted_dates:
                        dict_data = {"type": bin_type, "collectionDate": date}
                        data["bins"].append(dict_data)
        except Exception as e:
            # Here you can log the exception if needed
            print(f"An error occurred: {e}")
            # Optionally, re-raise the exception if you want it to propagate
            raise
        finally:
            # This block ensures that the driver is closed regardless of an exception
            if driver:
                driver.quit()
        return data
