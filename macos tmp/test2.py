import tkinter as tk
from tkinter import simpledialog

def get_user_selection(wifi_networks):
    root = tk.Tk()
    root.withdraw()  # 隐藏主窗口

    # 构建选择菜单文本
    menu_text = "可用WiFi网络：\n"
    for i, network in enumerate(wifi_networks, 1):
        menu_text += f"{i}. {network}\n"
    
    # 显示输入对话框
        selection = simpledialog.askinteger(
        "WiFi选择", 
        menu_text + "\n请输入网络序号:", 
        minvalue=1, 
        maxvalue=len(wifi_networks)
    
                )
    
    return selection - 1 if selection is not None else None

# 使用示例
wifi_networks = ['HomeNet', 'OfficeWiFi', 'PublicNet']
selected_index = get_user_selection(wifi_networks)

if selected_index is not None:
    print(f"你选择了: {wifi_networks[selected_index]}")
