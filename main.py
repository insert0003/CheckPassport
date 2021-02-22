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
import chromedriver_binary  # Adds chromedriver binary to path

from selenium.webdriver.support.select import Select
from selenium.webdriver.chrome.options import Options # オプションを使うために必要
from selenium.webdriver.common.action_chains import ActionChains

def send_email(body):
    #context = ssl.create_default_context()
    msg = MIMEText(body)
    msg['Subject'] = 'Passport available'
	#修改为自己的邮箱
    msg['From'] = 'XXXX@gmail.com'
    #修改为自己的邮箱
    msg['To'] = 'XXXX@qq.com'
    msg['Bcc'] = ''
    msg['Date'] = formatdate()

    smtpobj = smtplib.SMTP_SSL('smtp.gmail.com', 465, timeout=10)
	#修改为自己的邮箱和密码
    smtpobj.login('XXXX@gmail.com', 'XXXX')
    smtpobj.sendmail('XXXX@gmail.com', 'XXXX@qq.com', msg.as_string())
    smtpobj.close()

def get_driver(argument, address):
    # Chrome startup
    option = Options()                          # オプションを用意
    if argument is not None:
        option.add_argument(argument)           # ヘッドレスモードの設定を付与
    driver = webdriver.Chrome(options=option)
    # open "https://ppt.mfa.gov.cn/"
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
	# 修改为自己的档案号
    recordNumber.send_keys('档案号')
	# 修改为自己的问题序号，从上往下顺序+1
    questionObject.select_by_index(2)
	# 修改为自己的问题答案
    questionAnswer.send_keys(u'问题答案')

    # submit
    submit_div = driver.find_element_by_class_name('ui-dialog-buttonset')
    submit_button = submit_div.find_element_by_xpath('//button[@type="button"]')
    # print("submit_button: " + submit_button.text)
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

def start_driver(address, availableDate):
    visible_driver = get_driver(None, address)
    # //*[@id="calendar"]/div/div/table/tbody/tr[4]/td[2]
    calendar = visible_driver.find_element_by_id('calendar')
    # <td class="fc-day fc-mon ui-widget-content fc-future bg_border" data-date="2021-02-22"><div><div class="fc-day-number">22</div><div class="fc-day-content"><div style="position: relative; height: 21px;">&nbsp;</div></div></div></td>
    keyword = '//td[@data-date="{}"]'.format(availableDate[0])
    cell_button = calendar.find_element_by_xpath(keyword)
    ac = ActionChains(visible_driver)
    ac.move_to_element(cell_button).move_by_offset(5, 5).click().perform()

    time.sleep(3)

    # <input type="button" class="button-1" disabled="disabled" value="点击预约" onclick="reservation('2021-2-22T9:0','2021-2-22T11:0','b0baa34cfcf34a21badcc9a45c3971f1','100/100','中华人民共和国驻日本大使馆','/appo','undefined','undefined','16','180','undefined','0','-256','35','0','1','0','1')">
    # //*[@id="itable"]/tbody/tr[2]/td[5]/input
    # itable = visible_driver.find_element_by_id('itable')
    # input_button = itable.find_element_by_xpath('//input[@class="button-1"]')
    # input_button.click()
    # cell_button.click()
    time.sleep(100)
    visible_driver.quit()

def check_reservation(session, addressName):
    # url = 'https://ppt.mfa.gov.cn/appo/service/reservation/data/getReservationDateBean.json?rid=0.025537507514946434'
    # 0.025537507514946434
    # 0.202001513334161375
    rid = "{}{}".format(random.random(), random.randint(100000, 999999))
    url = 'https://ppt.mfa.gov.cn/appo/service/reservation/data/getReservationDateBean.json?rid={}'.format(rid)
    # print("url" + url)
    result = session.post(url,data={"addressName":addressName})
    response = json.loads(result.text)
    status = response['status']

    # response = requests.post('https://ppt.mfa.gov.cn/appo/service/reservation/data/getReservationDateBean.json?rid=0.025537507514946434&addressName=')
    # print(result.status_code)    # HTTPのステータスコード取得
    # print(status)    # レスポンスのHTMLを文字列で取得
    # print(data)    # レスポンスのHTMLを文字列で取得

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
	for retryCount in range(5000):
		print("    Chrome Start >>>>>>")
		# start_driver(2)

		driver = get_driver('--headless', 2)
		session = requests.session()
		#セッションの受け渡し
		for cookie in driver.get_cookies():
			session.cookies.set(cookie["name"], cookie["value"])

		offlineDate, offlineBody = check_reservation(session, "")
		onlineDate, onlineBody = check_reservation(session, "e1be0a00f05e40e6badd079ea4db9a87")
		# close chrome
		driver.quit()

		print("    offline >>>>>")
		print(offlineBody)
		if (offlineDate):
			print(offlineDate)
			send_email(offlineBody)
			start_driver(1, offlineDate)
		print("    offline <<<<<")
		print("    online >>>>>")
		print(onlineBody)
		if (onlineDate):
			print(onlineDate)
			send_email(onlineBody)
			start_driver(2, onlineDate)
		print("    online <<<<<")

		print("    Chrome Quit <<<<<<")
		print("sleeping 180s")
		time.sleep(180)
