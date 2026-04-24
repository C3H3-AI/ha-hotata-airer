# 好太太晾衣机抓包教程

本文档说明如何获取配置好太太晾衣机集成所需的 `refreshToken`。

## 准备工作

1. 手机安装好太太智家小程序
2. 电脑安装抓包工具（任选其一）：
   - Charles Proxy
   - Fiddler
   - mitmproxy

## 抓包步骤

### 1. 配置手机代理

1. 确保手机和电脑在同一局域网
2. 查看电脑 IP：
   ```bash
   # Windows
   ipconfig

   # macOS/Linux
   ifconfig
   ```
3. 手机设置 → WLAN → 当前WiFi → 代理设置 → 手动
4. 服务器填电脑 IP，端口填抓包工具监听端口（默认 8888）

### 2. 安装抓包证书

**Charles/Fiddler**: 按提示在手机安装证书

**mitmproxy**:
1. 访问 `http://mitm.it`
2. 选择对应系统下载证书
3. 安装证书并设置为信任

### 3. 开启抓包并登录

1. 开启抓包工具监听
2. 打开好太太智家小程序
3. 点击「登录/注册」，完成登录
4. 等待登录完成

### 4. 查找 refreshToken

在抓包工具中筛选以下请求：

**Charles**: Filter 输入 `refreshToken`
**Fiddler**: Find 搜索 `refreshToken`
**mitmproxy**: 搜索 `refreshToken`

找到类似以下的请求：

```
POST /app-api/v2.0/login/spLogin/refreshToken
```

在请求体或响应体中查找：

```json
{
  "refreshToken": "这里是refreshToken的值",
  "accessToken": "这里是accessToken的值",
  "userId": "用户ID",
  "iotId": "设备ID"
}
```

**注意**：需要复制完整的 `refreshToken` 字符串。

## 验证 Token

如果你不确定抓到的 Token 是否正确，可以复制 `refreshToken` 后在集成配置中测试。如果配置成功，说明 Token 有效。

## 常见问题

### Q: Token 过期了怎么办？
A: 重新抓包获取新的 refreshToken，然后在 HA 中重新配置集成。

### Q: 抓不到请求怎么办？
A:
1. 检查手机代理是否设置正确
2. 检查证书是否安装并信任
3. 确保手机和电脑在同一网络
4. 尝试关闭 VPN

### Q: refreshToken 和 accessToken 的区别？
A:
- `accessToken`: 短期令牌，用于日常 API 调用
- `refreshToken`: 长期令牌，用于刷新 accessToken

本集成会自动处理 Token 刷新，你只需提供 `refreshToken`。

## 安全提示

- 抓包获得的 Token 请妥善保管
- 不要在公共场合分享你的 Token
- 如发现异常登录，及时修改好太太账号密码
