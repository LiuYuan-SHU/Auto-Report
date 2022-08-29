# Selenium组件
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver import ChromeOptions
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
# 标准库组件
import logging          # 日志
import json             # JSON文件操作
import os               # 判断文件是否存在
import sys              # quit
import re               # 正则表达式
from time import sleep  # 程序等待

# logging configuration
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s: %(message)s')

# selenium configuration
# headless mode
options = ChromeOptions()
options.add_argument('--headless')
# browser
browser = webdriver.Chrome(options=options)
browser.set_window_size(1920, 1080)

# 每日一报URL
report_history_url = 'https://selfreport.shu.edu.cn/ReportHistory.aspx'

# 登录
# 登录界面需要在10s之内加载完毕，否则会抛出TimeoutException
# 如果出现这样的情况，提醒检查网络状态并退出程序
# 如果输入了错误的账号和密码，那么也会退出程序
def login(username, password):
    try:
        browser.get(report_history_url)
        wait = WebDriverWait(browser, 10)
        # get input element to input username
        input_username = wait.until(EC.presence_of_element_located((By.XPATH, './/input[@id="username"]')))
        # get input element to input password
        input_password = browser.find_element(By.XPATH, './/input[@id="password"]')
        # get button element
        button_login = browser.find_element(By.CLASS_NAME, 'submit-button')
        input_username.send_keys(username)
        input_password.send_keys(password)
        button_login.click()
    except TimeoutException:
        logging.error('requests time out. please check your network status')
        sys.exit()

    # wrong password or ID
    try:
        button_wrong_password = browser.find_element(By.XPATH, './/button[contains(text(), "ok")]')
        logging.error('wrong password, exit')
        sys.exit()
    except NoSuchElementException:
        logging.info('login successfully')        

    return

# return reversed href list
# 需要注意的是，如果超时，那么就会默认所有每日一报已经完成，那么就会结束程序
def get_item_list():
    logging.info('scraping reports list')
    item_list = []

    try:
        wait = WebDriverWait(browser, 3)
        item_list = wait.until(EC.presence_of_all_elements_located((By.XPATH, './/a[@class="f-datalist-item-inner" and contains(text(), "未填报")]')))
        item_list = [item.get_attribute('href') for item in item_list]
    except TimeoutException:
        logging.info('all reports submitted, exit')
        sys.exit()

    return item_list[::-1]

# get WebElement
# 根据传入的XPath返回元素
def get_element(xpath):
    return browser.find_element(By.XPATH, xpath)

# 填写每日一报
def submit_info():
    # 检索文件data.json是否存在
    if os.path.exists('./data.json'):
        json_data = json.load(open('data.json', encoding='utf-8')) 
    else:
        logging.error('json file data.json not found, fatal error, exit')
        sys.exit()

    wait = WebDriverWait(browser, 10)
    # promise button
    button_promise = wait.until(EC.presence_of_element_located((By.XPATH, '/html/body/form/div[5]/div/div[2]/div[1]/div[1]/div[2]/div/div/i')))
    if button_promise.get_attribute('class').find('f-checked') == -1:
        button_promise.click()

    # in_Shanghai
    in_Shanghai_index = json_data["in_Shanghai_index"]
    button_in_Shanghai = get_element('/html/body/form/div[5]/div/div[2]/div[1]/div[9]/div/div/div[2]/div[2]/div/table/tr[{index}]/td/div/div[2]/div/div/i'.format(index = in_Shanghai_index))
    if button_in_Shanghai.get_attribute('class').find('f-checked') == -1:
        button_in_Shanghai.click()
    
    # special case handling
    if in_Shanghai_index == 1:
        button_zone = get_element('/html/body/form/div[5]/div/div[2]/div[1]/div[9]/div/div/div[3]/div[2]/div/table/tr/td[{index}]/div/div[2]/div/div/i'.format(index = json_data["in_Shanghai"].get('zone'))) 
        if button_zone.get_attribute('class').find('f-checked') == -1:
            button_zone.click()
        button_campus = get_element('/html/body/form/div[5]/div/div[2]/div[1]/div[9]/div/div/div[4]/div[2]/div/table/tr/td[{index}]/div/div[2]/div/div/i'.format(index = json_data["in_Shanghai"].get('campus'))) 
        if button_campus.get_attribute('class').find('f-checked') == -1:
            button_campus.click()

    # is_home
    button_is_home = get_element('/html/body/form/div[5]/div/div[2]/div[1]/div[28]/div[2]/div/table/tr/td[{index}]/div/div[2]/div/div/i'.format(index = json_data["is_home_address"]))
    if button_is_home.get_attribute('class').find('f-checked') == -1:
        button_is_home.click()

    # high risk zone
    button_high_risk = get_element('/html/body/form/div[5]/div/div[2]/div[1]/div[29]/div[2]/div/table/tr[1]/td/div/div[2]/div/div/i')
    if button_high_risk.get_attribute('class').find('f-checked') == -1:
        button_high_risk.click()
    # touch
    button_touch = get_element('/html/body/form/div[5]/div/div[2]/div[1]/div[30]/div[2]/div/table/tr/td[2]/div/div[2]/div/div/i')
    if button_touch.get_attribute('class').find('f-checked') == -1:
        button_touch.click()
    # isolate
    button_isolate = get_element('/html/body/form/div[5]/div/div[2]/div[1]/div[31]/div[2]/div/table/tr/td[2]/div/div[2]/div/div/i')
    if button_isolate.get_attribute('class').find('f-checked') == -1:
        button_isolate.click()

    # submit
    button_submit = get_element('/html/body/form/div[5]/div/div[2]/div[2]/div/div/a[1]')
    button_submit.click()

    button_YES = wait.until(EC.presence_of_element_located((By.ID, 'fineui_39')))
    button_YES.click()
    # 防止点击过快造成的表单提交失败
    sleep(1.5)

def main(username, password):
    if username == None:
        username = input('please input your student ID in SHU: ')
        password = input("please input your student password in SHU(Don't worry, the program won't record your ID & Password):")
    login(username, password)

    # get datalist
    item_list = get_item_list()

    for item in item_list:
        logging.info(item)
        browser.get(item)
        submit_info()

if __name__ == '__main__':
    try:
        username = None
        password = None
        if len(sys.argv) == 3:
            username = sys.argv[1]
            password = sys.argv[2]
        main(username, password)
        
        logging.info('all reportsfinished, exit')
    finally:
        browser.close()
