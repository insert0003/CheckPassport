#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 必要なライブラリのインポート
import time
import requests
import json
import random
import smtplib
import ssl

from email.mime.text import MIMEText
from email.utils import formatdate
from selenium import webdriver
from selenium.webdriver.support.select import Select
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import NoSuchElementException

def send_email(body):
    msg = MIMEText(body)
    msg['Subject'] = 'Passport available'
    msg['From'] = FROM
    msg['To'] = TO
    msg['Bcc'] = ''
    msg['Date'] = formatdate()

    smtpobj = smtplib.SMTP_SSL('smtp.gmail.com', 465, timeout=10)
    smtpobj.login(FROM, PASSWORD)
    smtpobj.sendmail(FROM, TO, msg.as_string())
    smtpobj.close()

def get_driver(argument, address):
    option = Options()
    if argument is not None:
        option.add_argument(argument)
    driver = webdriver.Chrome(options=option)
    driver.get("https://ppt.mfa.gov.cn/")

    # continue reservation
    anchor = driver.find_element_by_xpath('//*[@id="body"]/div[2]/div[1]/ul/li[2]/p[2]/span/a')
    anchor.click()
    time.sleep(5)

    # input user infor
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
    time.sleep(5)

    # <input type="button" name="myButton" id="myButton" class="button" value="进入预约">
    in_button = driver.find_element_by_xpath('//*[@id="myButton"]')
    in_button.click()
    time.sleep(5)

    # <button type="button" class="ui-button ui-widget ui-state-default ui-corner-all ui-button-text-only" role="button" aria-disabled="false"><span class="ui-button-text">确认</span></button>
    ok_button = driver.find_element_by_xpath('/html/body/div[6]/div[3]/div/button')
    ok_button.click()
    time.sleep(5)

    # <select id="address" style="width: 250px;"><option value="">日本到馆办理（东京）</option><option value="e1be0a00f05e40e6badd079ea4db9a87" title="1">日本不见面办理</option></select>
    add_select = driver.find_element_by_xpath('//*[@id="address"]')
    add_object = Select(add_select)
    add_object.select_by_index(address)

    return driver

def check_reservation(session, addressName):
    rid = "{}{}".format(random.random(), random.randint(100000, 999999))
    url = 'https://ppt.mfa.gov.cn/appo/service/reservation/data/getReservationDateBean.json?rid={}'.format(rid)
    result = session.post(url,data={"addressName":addressName})
    response = json.loads(result.text)
    status = response['status']

    emailBody = ''
    availableDate = []

    for item in response['data']:
        date = item['date']
        userNumbers = 0
        peopleNumber = 0

        for period in item['periodOfTimeList']:
            userNumbers = userNumbers + int(period['userNumber'])
            peopleNumber = peopleNumber + int(period['peopleNumber'])
        if (userNumbers != peopleNumber):
            emailBody = emailBody + "    {} is available.  {}/{}\n".format(date, userNumbers, peopleNumber)
            availableDate.append(date)
        else:
            emailBody = emailBody + "    {} is full. {}/{}\n".format(date, userNumbers, peopleNumber)

    return availableDate, emailBody

if __name__ == '__main__':
    FROM = ""
    TO = ""
    PASSWORD = ""
    ID = ""
    QUESTION = 0
    ANSWER = ""
    LOOP = 0
    SLEEP = 0

    try:
        with open("./config.json",'r') as load_f:
            load_dict = json.load(load_f)
            FROM = load_dict['from']
            TO = load_dict['to']
            PASSWORD = load_dict['password']
            ID = load_dict['id']
            QUESTION = int(load_dict['question'])
            ANSWER = load_dict['answer']
            LOOP = int(load_dict['loop'])
            SLEEP = int(load_dict['sleep'])
            for loopCount in range(LOOP):
                print(u"开始第{}次尝试...".format(loopCount+1))

                driver = get_driver("--headless", 2)
                session = requests.session()
                for cookie in driver.get_cookies():
                    session.cookies.set(cookie["name"], cookie["value"])

                offlineDate, offlineBody = check_reservation(session, "")
                onlineDate, onlineBody = check_reservation(session, "e1be0a00f05e40e6badd079ea4db9a87")
                driver.quit()

                print("    offline >>>>>")
                print(offlineBody)
                if (offlineDate):
                    print(offlineDate)
                    send_email(offlineBody)
                    get_driver(None, 1)
                print("    offline <<<<<")
                print("    online >>>>>")
                print(onlineBody)
                if (onlineDate):
                    print(onlineDate)
                    send_email(onlineBody)
                    get_driver(None, 2)
                print("    online <<<<<")
                print(u"第{}次尝试结束，休息{}秒．".format(loopCount+1, SLEEP))
                time.sleep(SLEEP)

    except NoSuchElementException as e:
        print(u"没有该元素: {}".format(e))
    except:
        print(u"请正确设置配置文件")