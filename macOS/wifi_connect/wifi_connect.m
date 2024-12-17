// clang -arch arm64 -framework Foundation -framework CoreWLAN -framework CoreLocation -o wifi_connect
#import <Foundation/Foundation.h>
#import <CoreWLAN/CoreWLAN.h>

int main(int argc, const char * argv[]) {
    @autoreleasepool {
        // 获取系统默认 Wi-Fi 接口
        CWInterface *wifiInterface = [[CWWiFiClient sharedWiFiClient] interface];
        
        if (!wifiInterface) {
            NSLog(@"无法找到可用的 Wi-Fi 接口");
            return 1;
        }
        
        // 设置要连接的网络 SSID
        NSString *targetSSID = @"406";
        
        // 设置网络密码
        NSString *password = @"88888888";
        
        // 扫描可用网络
        NSError *scanError = nil;
        NSSet *networks = [wifiInterface scanForNetworksWithName:targetSSID error:&scanError];
        
        if (scanError) {
            NSLog(@"网络扫描错误: %@", scanError);
            return 1;
        }
        
        // 选择目标网络
        CWNetwork *targetNetwork = [networks anyObject];
        
        if (!targetNetwork) {
            NSLog(@"未找到指定的网络: %@", targetSSID);
            return 1;
        }
        
        // 连接网络
        NSError *connectionError = nil;
        BOOL success = [wifiInterface connectToNetwork:targetNetwork
                                          password:password
                                             error:&connectionError];
        
        if (success) {
            NSLog(@"成功连接到网络: %@", targetSSID);
        } else {
            NSLog(@"连接网络失败: %@", connectionError);
            return 1;
        }
        
        // 等待连接完成（简单的延迟）
        [[NSRunLoop currentRunLoop] runUntilDate:[NSDate dateWithTimeIntervalSinceNow:5]];
    }
    return 0;
}