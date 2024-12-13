#import <Foundation/Foundation.h>
#import <CoreWLAN/CoreWLAN.h>
#import <CoreLocation/CoreLocation.h>

@interface WifiConnector : NSObject <CLLocationManagerDelegate>

@property (strong, nonatomic) CLLocationManager *locationManager;

- (void)requestLocationPermission;
- (void)connectToWifiWithBSSID:(NSString *)bssid password:(NSString *)password;

@end

@implementation WifiConnector

// 请求定位服务权限
- (void)requestLocationPermission {
    self.locationManager = [[CLLocationManager alloc] init];
    self.locationManager.delegate = self;

    // 在 macOS 中，您可以请求 `whenInUse` 或 `always` 权限，通常使用 `whenInUse` 权限即可
    [self.locationManager requestWhenInUseAuthorization];
}

// 连接到 Wi-Fi 网络
- (void)connectToWifiWithBSSID:(NSString *)bssid password:(NSString *)password {
    // 获取 Wi-Fi 客户端
    CWWiFiClient *wifiClient = [CWWiFiClient sharedWiFiClient];
    CWInterface *wifiInterface = [wifiClient interface];

    if (!wifiInterface) {
        printf("No Wi-Fi interface found.\n");
        return;
    }

    // 扫描所有网络
    NSError *error = nil;
    NSSet<CWNetwork *> *networkSet = [wifiInterface scanForNetworksWithSSID:nil error:&error];
    if (!networkSet || [networkSet count] == 0) {
        printf("Failed to scan networks. Error: %s\n", [[error localizedDescription] UTF8String]);
        return;
    }

    // 打印扫描结果
    CWNetwork *targetNetwork = nil;
    for (CWNetwork *network in networkSet) {
        printf("SSID: %s, BSSID: %s\n",
               network.ssid ? [network.ssid UTF8String] : "(null)",
               network.bssid ? [network.bssid UTF8String] : "(null)");
        if ([network.bssid isEqualToString:bssid]) {
            targetNetwork = network;
            break;
        }
    }

    if (!targetNetwork) {
        printf("No network found with BSSID: %s\n", [bssid UTF8String]);
        return;
    }

    // 连接到目标网络
    BOOL success = [wifiInterface associateToNetwork:targetNetwork password:password error:&error];
    if (success) {
        printf("Successfully connected to network with BSSID: %s\n", [bssid UTF8String]);
    } else {
        printf("Failed to connect to network with BSSID: %s. Error: %s\n", [bssid UTF8String], [[error localizedDescription] UTF8String]);
    }
}

@end

int main(int argc, const char * argv[]) {
    @autoreleasepool {
        if (argc < 3) {
            printf("Usage: wifi_connect_bssid <BSSID> <PASSWORD>\n");
            return 1;
        }

        NSString *bssid = [NSString stringWithUTF8String:argv[1]];
        NSString *password = [NSString stringWithUTF8String:argv[2]];

        WifiConnector *connector = [[WifiConnector alloc] init];

        // 请求定位权限
        [connector requestLocationPermission];

        // 延迟一小段时间，等待用户授权（根据实际情况可以调整）
        [NSThread sleepForTimeInterval:2.0];

        // 连接到指定的 Wi-Fi 网络
        [connector connectToWifiWithBSSID:bssid password:password];
    }
    return 0;
}
