import Foundation
import CoreWLAN

/// Wi-Fi 连接工具
class WifiConnector {
    /// 使用 BSSID 和密码连接 Wi-Fi 网络
    /// - Parameters:
    ///   - bssid: 目标网络的 BSSID
    ///   - password: Wi-Fi 密码
    func connectToWifi(bssid: String, password: String) {
        // 获取 Wi-Fi 客户端和硬件接口
        let wifiClient = CWWiFiClient.shared()
        guard let wifiInterface = wifiClient.interface() else {
            print("❌ 无法获取 Wi-Fi 硬件接口")
            return
        }

        print("当前接口: \(wifiInterface.interfaceName ?? "未知接口")")

        // 扫描并匹配 BSSID
        do {
            // 扫描所有网络
            let networks = try wifiInterface.scanForNetworks(withSSID: nil)
            
            print("🔍 扫描到的网络:")
            for network in networks {
                print("SSID: \(network.ssid ?? "未知"), BSSID: \(network.bssid ?? "未知")")
            }

            // 查找目标网络
            guard let targetNetwork = networks.first(where: { $0.bssid == bssid }) else {
                print("❌ 未找到目标 BSSID: \(bssid)")
                return
            }

            print("🔗 正在尝试连接到网络: \(targetNetwork.ssid ?? "未知")")
            try wifiInterface.associate(to: targetNetwork, password: password)
            print("✅ 成功连接到网络: \(targetNetwork.ssid ?? "未知") (BSSID: \(bssid))")
        } catch let error as NSError {
            print("❌ 连接过程中发生错误: \(error.localizedDescription)")
        }

    }
}

// 命令行处理逻辑
if CommandLine.argc < 3 {
    print("Usage: wifi_connect <BSSID> <PASSWORD>")
    exit(1)
}

let bssid = CommandLine.arguments[1]
let password = CommandLine.arguments[2]

let connector = WifiConnector()
connector.connectToWifi(bssid: bssid, password: password)
