#!/usr/bin/env python3
import os
import requests
import paramiko
import socket
from datetime import datetime
import pytz
import re

# 预先定义的常量
url = '你检测的地址，参考下一行注释'
# 测试URL 这个URL是个凉了的 url = 'https://edwgiz.serv00.net/'
ssh_info = {
    'host': 's3.serv00.com',    # 主机地址
    'port': 22,
    'username': '你的用户名',       # 你的用户名，别写错了
    'password': '你的SSH密码'       # 你注册的时候收到的密码或者你自己改了的密码
}

# 获取当前脚本文件的绝对路径
script_dir = os.path.dirname(os.path.abspath(__file__))

# 日志文件将保存在脚本所在的目录中
log_file_path = os.path.join(script_dir, 'Auto_connect_SSH.log')
flush_log_message = []

# 写入日志的函数
def write_log(log_message):
    global flush_log_message
    if not os.path.exists(log_file_path):
        open(log_file_path, 'a').close()
        os.chmod(log_file_path, 0o644)
    log_info = f"{log_message}"
    flush_log_message.append(log_info)

# 把所有的日志信息写入日志文件
def flush_log():
    global flush_log_message
    username = ssh_info['username']
    system_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    beijing_time = datetime.now(pytz.timezone('Asia/Shanghai')).strftime('%Y-%m-%d %H:%M:%S')
    current_day = datetime.now(pytz.timezone('Asia/Shanghai')).weekday()
    weekdays = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
    current_weekday_name = weekdays[current_day]
    flush_log_messages = f"{system_time} - {beijing_time} - {current_weekday_name} - {url} - {username} - {' - '.join(flush_log_message)}"
    with open(log_file_path, "a", encoding="utf-8") as log_file:
        log_file.write(flush_log_messages + '\n')
    flush_log_message.clear()

# 尝试通过SSH连接的函数
def ssh_connect():
    try:
        transport = paramiko.Transport((ssh_info['host'], ssh_info['port']))
        transport.connect(username=ssh_info['username'], password=ssh_info['password'])
        ssh_status = "SSH连接成功"
        print("SSH连接成功。")
    except Exception as e:
        ssh_status = f"SSH连接失败，错误信息: {e}"
        print(f"SSH连接失败: {e}")
    finally:
        transport.close()
        write_log(f"{ssh_status}")

# 检查是否为每月的1号或15号
def is_first_day_of_month():
    now = datetime.now(pytz.timezone('Asia/Shanghai'))
    print("本来应该是系统时间，但是我要改成北京时间增强辨识度：", now)
    current_day = now.day
    return current_day == 1 or current_day == 15

# 返回当前的天、月和一年中的第几天
def get_day_info():
    now = datetime.now(pytz.timezone('Asia/Shanghai'))
    print("北京时间：", now)
    current_day = now.day
    current_month = now.month
    current_year_day = now.timetuple().tm_yday
    current_weekday = now.weekday()
    weekdays = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
    current_weekday_name = weekdays[current_weekday]
    return current_day, current_month, current_year_day, current_weekday_name

# 检查URL状态和DNS的函数
def check_url_status_and_dns():
    try:
        host = socket.gethostbyname(url.split('/')[2])
        print(f"解析成功，IP地址为: {host}")
        write_log(f"{host}")
    except socket.gaierror as e:
        write_log(f"Error: {e}")
        print(f"DNS解析失败: {e}")
        return

    try:
        response = requests.get(url, timeout=10)
        status_code = response.status_code
        write_log(f"主机状态码: {status_code}")
        print(f"主机状态码: {status_code}")
    except requests.RequestException as e:
        write_log(f"请求失败: {e}")
        print(f"请求失败: {e}")

# 新增的登录功能
def login(username, password, panel):
    try:
        if isinstance(panel, (int, str)) and str(panel).isdigit():
            login_url = f"https://panel{panel}.serv00.com/login"
        elif isinstance(panel, str) and "." in panel:
            login_url = f"https://{panel}/login"
        else:
            raise ValueError(f"无效的panel格式: {panel}")

        response = requests.post(login_url, data={
            "username": username,
            "password": password
        })
        
        if response.status_code == 200:
            print(f"登录成功：{username} 到 {login_url}")
            return True
        else:
            print(f"登录失败：{username} 到 {login_url}，状态码：{response.status_code}")
            return False
    except Exception as e:
        print(f"登录异常：{username}，错误：{str(e)}")
        return False

def parse_panel(panel_info):
    if isinstance(panel_info, (int, str)) and str(panel_info).isdigit():
        return panel_info
    elif isinstance(panel_info, str):
        match = re.search(r'\d+', panel_info)
        if match:
            return match.group()
        elif "." in panel_info:
            return panel_info
    raise ValueError(f"无法解析panel信息: {panel_info}")

if __name__ == '__main__':
    # 每月一次检查提醒
    if is_first_day_of_month():
        current_day, current_month, current_year_day, current_weekday_name = get_day_info()
        print(f"今天是{current_month}月{current_day}日({current_weekday_name})，本月的第{current_day}天，今年的第{current_year_day}天")
        ssh_connect()

    # 检查URL状态和DNS
    check_url_status_and_dns()

    # 新增的登录功能示例
    users = [
        {"username": "qishihuang", "password": "zhanghao", "panelnum": "3"},
        {"username": "bb405", "password": "Bbylw521", "panel": "panel.ct8.pl"},
        {"username": "user3", "password": "pass3", "panel": "panel5"},
        {"username": "user4", "password": "pass4", "panelnum": 7}
    ]

    for user in users:
        panel = user.get("panel") or user.get("panelnum")
        try:
            parsed_panel = parse_panel(panel)
            login(user["username"], user["password"], parsed_panel)
        except ValueError as e:
            print(f"错误：{str(e)}")

    # 所有日志信息已经收集完成，写入日志文件
    flush_log()
