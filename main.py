#!/usr/bin/env python
# -*- coding: utf-8 -*-
import datetime
import time
import requests
import json
import random
import os

from selenium import webdriver
from selenium.webdriver.support.select import Select
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException
from pygame import mixer

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import *

def play_sound():
    mixer.init()
    mixer.music.load("music.mp3")
    mixer.music.play()

def send_email(body):
    print(body)
    message = Mail()
    for num in range(len(TOS)):
        message.to = To(TOS[num], TOS[num], p = num)
    message.from_email = From(FROM, 'PassportCheck')
    message.subject = Subject('护照有名额')
    message.content = Content(MimeType.text, body)
    message.content = Content(MimeType.html, '<strong>{}</strong><br/>'.format(body))
    message.header = Header('X-Sent-Using', 'SendGrid-API')
        
    # メール送信を行い、レスポンスを表示
    sendgrid_client = SendGridAPIClient(APIKEY)
    response = sendgrid_client.send(message = message)
    print(response.status_code)
    print(response.body)
    print(response.headers)

def get_driver():
    # Chrome startup
    option = Options()
    if VISIBLE == "0":
        option.add_argument('--headless')

    if os.name == 'nt':
        driver = webdriver.Chrome('./driver/chromedriver.exe', options=option)
    else:
        driver = webdriver.Chrome('./driver/chromedriver', options=option)
    driver.get("https://ppt.mfa.gov.cn/")

    # 通知 - 我已知晓
    confirm = driver.find_element_by_xpath('//*[@id="body"]/div[9]/div[3]/div/button')
    confirm.click()
    time.sleep(2)

    # 继续未完成的预约
    anchor = driver.find_element_by_xpath('//*[@id="body"]/div[2]/div[1]/ul/li[2]/p[2]/span/a')
    anchor.click()
    time.sleep(2)

    # 输入用户信息
    recordNumber = driver.find_element_by_id('recordNumberHuifu')
    questionID = driver.find_element_by_id('questionIDHuifu')
    questionObject = Select(questionID)
    questionAnswer = driver.find_element_by_id('answerHuifu')
    recordNumber.send_keys(ID)
    questionObject.select_by_index(QUESTION)
    questionAnswer.send_keys(ANSWER)

    # 提交
    submit_div = driver.find_element_by_class_name('ui-dialog-buttonset')
    submit_button = submit_div.find_element_by_xpath('//button[@type="button"]')
    submit_button.click()
    time.sleep(2)

    # <input type="button" name="myButton" id="myButton" class="button" value="进入预约">
    in_button = driver.find_element_by_xpath('//*[@id="myButton"]')
    in_button.click()
    time.sleep(2)

    # <button type="button" class="ui-button ui-widget ui-state-default ui-corner-all ui-button-text-only" role="button" aria-disabled="false"><span class="ui-button-text">确认</span></button>
    ok_button = driver.find_element_by_xpath('/html/body/div[6]/div[3]/div/button')
    ok_button.click()

    session = requests.session()
    for cookie in driver.get_cookies():
        session.cookies.set(cookie["name"], cookie["value"])

    return driver, session

def check_reservation(driver, session, addressName):
    # <select id="address" style="width: 250px;"><option value="">日本到馆办理（东京）</option><option value="e1be0a00f05e40e6badd079ea4db9a87" title="1">日本不见面办理</option></select>
    add_select = driver.find_element_by_xpath('//*[@id="address"]')
    add_object = Select(add_select)
    if (addressName == "e1be0a00f05e40e6badd079ea4db9a87"):
        add_object.select_by_index(1)
    else:
        add_object.select_by_index(2)

    # url = 'https://ppt.mfa.gov.cn/appo/service/reservation/data/getReservationDateBean.json?rid=0.025537507514946434'
    rid = "{}{}".format(random.random(), random.randint(100000, 999999))
    url = 'https://ppt.mfa.gov.cn/appo/service/reservation/data/getReservationDateBean.json?rid={}'.format(rid)
    result = session.post(url,data={"addressName":addressName})
    response = json.loads(result.text)
    status = response['status']

    emailBody = ''
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

        if (DEBUG == "1"):
            if date == "2021-08-05":
                body = "    {} is available.  {}/{}".format(date, userNumbers, peopleNumber)
                emailBody = emailBody + body + "\n"

    return emailBody

if __name__ == '__main__':
    FROM = ""
    TOS = []
    APIKEY = ""
    ID = ""
    QUESTION = 0
    ANSWER = ""
    DEBUG = ""
    VISIBLE = ""


    try:
        if os.name == 'nt':
            load_f = open("./config.json", 'r',encoding='utf-8')
        else:
            load_f = open("./config.json", 'r')

        load_dict = json.load(load_f)
        print(load_dict)
        FROM = load_dict['from']
        TOS = load_dict['to'].split(',')
        APIKEY = load_dict['apikey']
        ID = load_dict['id']
        QUESTION = int(load_dict['question'])
        ANSWER = load_dict['answer']
        DEBUG = load_dict['debug']
        VISIBLE = load_dict['visible']

    except:
        print(u"请正确设置配置文件")
        exit()

    driver, session = get_driver()

    for loopCount in range(10000):
        if ((loopCount+1) % 2 == 0):
            driver.quit()
            driver, session = get_driver()

        try:
            print(u"{} >>> 开始第{}次尝试...".format(datetime.datetime.now(), loopCount+1))
            offlineBody = check_reservation(driver, session, "0c50854c36c04e309bcdf607a1739bb2")

            if (offlineBody != ""):
                driver.quit()
                # play_sound()
                send_email(offlineBody)
                VISIBLE = "1"
                visible_driver, session = get_driver()
                time.sleep(3600)
                visible_driver.quit()

            print(u"{} >>> 第{}次尝试结束，休息3分钟．".format(datetime.datetime.now(), loopCount+1))
            onlineBody = check_reservation(driver, session, "e1be0a00f05e40e6badd079ea4db9a87")
            time.sleep(180)

        except NoSuchElementException as e:
            print(u"没有该元素: {}".format(e))
            time.sleep(180)
            continue

    driver.quit()
