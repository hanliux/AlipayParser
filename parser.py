# -*- coding: utf-8 -*-
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders
from email.utils import formatdate, COMMASPACE
import smtplib
import time
import os
import random


def send_email(server, fr, to, subject, text, files=[]):
    msg = MIMEMultipart()
    msg['From'] = fr
    msg['To'] = to
    msg['Subject'] = subject
    msg['Date'] = formatdate(localtime=True)
    msg.attach(MIMEText(text))

    for file in files:
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(open(file, "rb").read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', 'attachment; filename="%s"' % os.path.basename(file))
        msg.attach(part)

    smtp = smtplib.SMTP_SSL(server['name'])
    smtp.login(server['user'], server['password'])
    smtp.sendmail(fr, to, msg.as_string())
    smtp.close()


def email_notify():
    server_name = "smtp.qq.com"
    user_name = "xxxxxx@qq.com"
    password = "xxxxxxxxxxxxx"
    subject = "你的支付宝进程崩溃了啊！"
    text = "还不赶快去修？"
    server = {
        "name": server_name,
        "user": user_name,
        "password": password
    }
    send_email(server, user_name, user_name, subject, text)


def parse_bills(alipay_user_name="xxxxxx@xxx.com", password=""):
    """
    从支付宝获取所有的订单
    并返回
    :return: 所有的订单的 list
    """
    driver = webdriver.Chrome()
    try:
        driver.set_window_size(2, 2)
        driver.get("https://authzui.alipay.com/login/index.htm")
        user_name_area = WebDriverWait(driver, 10, 1).until(
            ec.presence_of_element_located((By.ID, "J-input-user"))
        )
        pass_word_area = WebDriverWait(driver, 10, 1).until(
            ec.presence_of_element_located((By.ID, "password_rsainput"))
        )
        login_btn = WebDriverWait(driver, 10, 1).until(
            ec.presence_of_element_located((By.ID, "J-login-btn"))
        )
        if user_name_area and pass_word_area and login_btn:
            user_name_area.send_keys(alipay_user_name)
            time.sleep(random.uniform(0.1, 1))
            pass_word_area.click()
            pass_word_area.send_keys(password)
            time.sleep(random.randint(1, 5))  # 加入一些随机数，模拟真实点击
            login_btn.click()
            driver.implicitly_wait(10)
            time.sleep(random.uniform(1, 2))
            # 转到所有订单页面
            driver.get("https://consumeprod.alipay.com/record/advanced.htm")
            driver.implicitly_wait(10)

            # 确认是否转到了订单页面
            time.sleep(2)
            if not driver.title == "我的账单 - 支付宝":
                # 如果没有成功转到支付宝账单页面，那么用邮件通知
                # 取消注释下一行来启用
                # email_notify()
                return []

            # 找到所有订单并解析内容
            parsed_bills = []
            consumes = driver.find_elements(By.CLASS_NAME, "J-item")
            for consume in consumes:
                # 日期
                time_d = consume.find_element(By.CLASS_NAME, "time").find_element(By.CLASS_NAME, "time-d").text
                # 时间
                time_h = consume.find_element(By.CLASS_NAME, "time").find_element(By.CLASS_NAME, "time-h").text
                # 名称
                consume_title = consume.find_element(By.CLASS_NAME, "consume-title").text
                # 订单号
                trade_no = consume.find_element(By.CLASS_NAME, "tradeNo").find_element(By.TAG_NAME, "p").text
                # 对方
                other_name = consume.find_element(By.CLASS_NAME, "other").find_element(By.CLASS_NAME, "name").text
                # 金额
                amount_pay = consume.find_element(By.CLASS_NAME, "amount-pay").text
                # 交易状态
                status = consume.find_element(By.CLASS_NAME, "status").find_element_by_tag_name("p").text
                parsed_bills.append({
                    "day": time_d,
                    "time": time_h,
                    "title": consume_title,
                    "trade_no": trade_no,
                    "other_name": other_name,
                    "amount_pay": amount_pay,
                    "status": status
                })
            return parsed_bills
        else:
            return []
    except Exception:
        return []
    finally:
        driver.quit()  # 确保浏览器进程退出


if __name__ == "__main__":
    success_times = 0
    while True:
        parsed_bills = parse_bills(password="xxxxxxxxxxxx")
        success_times += 1
        if len(parsed_bills) <= 0:
            break
