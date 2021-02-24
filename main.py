#!/usr/bin/env python
# -*- coding: utf-8 -*-
import time
import requests
import json
import random
import smtplib
import ssl
import os

from email.mime.text import MIMEText
from email.utils import formatdate
from selenium import webdriver
from selenium.webdriver.support.select import Select
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException

def send_email(body):
    print(body)
    msg = MIMEText(body)
    msg['Subject'] = 'Passport Available'
    msg['From'] = FROM
    msg['To'] = TO
    msg['Bcc'] = ''
    msg['Date'] = formatdate()

    smtpobj = smtplib.SMTP_SSL('smtp.gmail.com', 465, timeout=10)
    smtpobj.login(FROM, PASSWORD)
    smtpobj.sendmail(FROM, TO, msg.as_string())
    smtpobj.close()

def get_driver(argument, address):
    # Chrome startup
    option = Options()
    if argument is not None:
        option.add_argument(argument)
    if os.name == 'nt':
        driver = webdriver.Chrome('./driver/chromedriver.exe', options=option)
    else:
        driver = webdriver.Chrome(options=option)
    driver.get("https://ppt.mfa.gov.cn/")

    # continue reservation
    anchor = driver.find_element_by_xpath('//*[@id="body"]/div[2]/div[1]/ul/li[2]/p[2]/span/a')
    anchor.click()
    time.sleep(3)

    # input user information
    recordNumber = driver.find_element_by_id('recordNumberHuifu')
    questionID = driver.find_element_by_id('questionIDHuifu')
    questionObject = Select(questionID)
    questionAnswer = driver.find_element_by_id('answerHuifu')
    recordNumber.send_keys(ID)
    questionObject.select_by_index(QUESTION)
    questionAnswer.send_keys(ANSWER)

    # submit
    submit_div = driver.find_element_by_class_name('ui-dialog-buttonset')
    submit_button = submit_div.find_element_by_xpath('//button[@type="button"]')
    submit_button.click()
    time.sleep(3)

    return driver

def check_reservation(session, addressName):
    # url = 'https://ppt.mfa.gov.cn/appo/service/reservation/data/getReservationDateBean.json?rid=0.025537507514946434'
    rid = "{}{}".format(random.random(), random.randint(100000, 999999))
    url = 'https://ppt.mfa.gov.cn/appo/service/reservation/data/getReservationDateBean.json?rid={}'.format(rid)
    result = session.post(url,data={"addressName":addressName})
    response = json.loads(result.text)
    status = response['status']

    emailBody = ""
    for item in response['data']:
        date = item['date']
        userNumbers = 0
        peopleNumber = 0

        for period in item['periodOfTimeList']:
            userNumbers = userNumbers + int(period['userNumber'])
            peopleNumber = peopleNumber + int(period['peopleNumber'])

        if (userNumbers != peopleNumber):
            body = "    {} is available.  {}/{}".format(date, userNumbers, peopleNumber)
            emailBody = emailBody + body + "\n"
            print(body)
        else:
            print("    {} is full. {}/{}".format(date, userNumbers, peopleNumber))

    return emailBody

if __name__ == '__main__':
    FROM = ""
    TO = ""
    PASSWORD = ""
    ID = ""
    QUESTION = 0
    ANSWER = ""

    try:
        with open("./config.json",'r',encoding='utf-8') as load_f:
            load_dict = json.load(load_f)
            FROM = load_dict['from']
            TO = load_dict['to']
            PASSWORD = load_dict['password']
            ID = load_dict['id']
            QUESTION = int(load_dict['question'])
            ANSWER = load_dict['answer']
    except:
        print(u"请正确设置配置文件")
        exit()
    
    for loopCount in range(500):
        try:
            print(u"开始第{}次尝试...".format(loopCount+1))
            driver = get_driver('--headless', 2)
            session = requests.session()
            for cookie in driver.get_cookies():
                session.cookies.set(cookie["name"], cookie["value"])

            print("    offline >>>>>")
            offlineBody = check_reservation(session, "")
            print("    offline <<<<<")

            print("    online >>>>>")
            onlineBody = check_reservation(session, "e1be0a00f05e40e6badd079ea4db9a87")
            print("    online <<<<<")
            driver.quit()

            if (offlineBody != ""):
                send_email(offlineBody)
                visible_driver = get_driver(None, 1)
                time.sleep(3600)

            if (onlineBody != ""):
                send_email(onlineBody)
                visible_driver = get_driver(None, 2)
                time.sleep(3600)

            print(u"第{}次尝试结束，休息3分钟．".format(loopCount+1))
            time.sleep(180)

        except NoSuchElementException as e:
            print(u"没有该元素: {}".format(e))
            time.sleep(1)
            continue
