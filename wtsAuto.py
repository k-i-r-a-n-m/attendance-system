from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException

import pyperclip
import time
import selenium
from noQR.config import CHROME_PROFILE_PATH
from datetime import datetime

def runMsg():

    options = webdriver.ChromeOptions()
    options.add_argument(CHROME_PROFILE_PATH)

    browser = webdriver.Chrome(
        executable_path='C:/chromedriver/chromedriver',options=options)

    browser.maximize_window()

    browser.get('https://web.whatsapp.com/')



    now = datetime.now()
    date = now.strftime("%d-%m-%Y")

    with open(f'attendance-{date}.csv', 'r', encoding='utf8') as f:
        presentRoll = [row.split(',') for row in f.readlines()]


    # with open('absent.csv','r' ,encoding='utf8') as f:
    #     absentRoll = [[row.strip()] for row in f.readlines()]


    # with open('msg.txt', 'r', encoding='utf8') as f:
    #     msg = f.read()

    def sendMsg(msg,row):
        # print(row)
        # print("hello")
        search_xpath = '//div[@contenteditable="true"][@data-tab="3"]'

        search_box = WebDriverWait(browser, 500).until(
            EC.presence_of_element_located((By.XPATH, search_xpath))
        )

        search_box.clear()

        time.sleep(1)

        pyperclip.copy(row[0].strip())

        search_box.send_keys(Keys.CONTROL + "v")  # Keys.CONTROL + "v"

        time.sleep(2)


        group_xpath = f'//span[@title="{row[0].strip()}"]'


        try:
            group_title = browser.find_element(by=By.XPATH, value=group_xpath)


            group_title.click()

            time.sleep(1)

            # input_xpath = '//div[@contenteditable="true"][@data-tab="1"]'
            input_xpath = '// *[ @ id = "main"] / footer / div[1] / div / span[2] / div / div[2] / div[1] / div / div[2]'
            # // *[ @ id = "main"] / footer / div[1] / div / span[2] / div / div[2] / div[1] / div
            # // *[ @ id = "main"] / footer / div[1] / div / span[2] / div / div[2] / div[1] / div / div[2]
            input_box = browser.find_element(by=By.XPATH, value=input_xpath)

            pyperclip.copy(msg)
            input_box.send_keys(Keys.CONTROL + "v")  # Keys.CONTROL + "v"
            input_box.send_keys(Keys.ENTER)

            time.sleep(2)
        except NoSuchElementException:
           pass

    for row in presentRoll:
        msg = \
        f'''
            ATTENDANCE SUMMARY
            PERIOD | STATUS
            1st    | {row[1]}
            2nd    | {row[2]}
            3rd    | {row[3]}
            4th    | {row[4]}
            5th    | {row[5]}
        '''
        # print(row)
        sendMsg(msg,row)

    browser.quit()

#
# for row in absentRoll:
#     msg = \
#         f'''
#            ATTENDANCE SUMMARY
#            PERIOD | STATUS
#            1st    | A
#            2nd    | A
#            3rd    | A
#            4th    | A
#            5th    | A
#        '''
#
#     sendMsg(msg,row)










