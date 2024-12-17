// wifi_connect.c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

int main(int argc, char *argv[]) {
    if (argc != 4) {
        fprintf(stderr, "Usage: %s <interface> <ssid> <password>\n", argv[0]);
        return 1;
    }

    char *interface = argv[1];
    char *ssid = argv[2];
    char *password = argv[3];

    // macOS networksetup命令连接WiFi
    char command[512];
    snprintf(command, sizeof(command), 
        "/usr/sbin/networksetup -setairportnetwork %s \"%s\" \"%s\"", 
        interface, ssid, password);

    // 执行命令并返回结果
    int result = system(command);

    if (result == 0) {
        printf("WiFi connected successfully\n");
        return 0;
    } else {
        fprintf(stderr, "WiFi connection failed\n");
        return 1;
    }
}