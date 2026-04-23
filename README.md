# Hotata Airer (好太太智能晾衣机)

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![License](https://img.shields.io/github/license/C3H3-AI/ha-hotata-airer.svg)](LICENSE)

Home Assistant 自定义集成，用于控制好太太（Hotata）智能晾衣机。

## 功能特性

- ✅ 晾衣架升降控制 (Cover)
- ✅ 照明灯开关与亮度调节 (Light)
- ✅ 电源、烘干、风干、消毒、负离子开关 (Switch)
- ✅ 位置、剩余时间等传感器 (Sensor)
- ✅ 设备在线状态监测 (Binary Sensor)
- ✅ 自动 Token 刷新
- ✅ 5秒轮询实时同步状态

## 支持的设备

- 好太太智能晾衣机（需支持 Keyoo 云平台）

## 安装

### 方法 1: HACS (推荐)

1. 打开 HACS → 自定义存储库
2. 添加存储库: `https://github.com/C3H3-AI/ha-hotata-airer`
3. 类别选择: **Integration**
4. 安装后重启 Home Assistant

### 方法 2: 手动安装

1. 下载最新 Release
2. 将 `custom_components/hotata_airer` 复制到 HA 的 `custom_components/` 目录
3. 重启 Home Assistant

## 配置

### 配置步骤

1. 进入 **设置** → **设备与服务** → **添加集成**
2. 搜索 "Hotata Airer"
3. 输入配置参数

## 实体说明

| 实体 | 类型 | 说明 |
|------|------|------|
| `cover.hotata_airer_airer` | Cover | 晾衣架升降控制 |
| `light.hotata_airer_light` | Light | 照明灯开关/亮度 |
| `switch.hotata_airer_power` | Switch | 电源开关 |
| `switch.hotata_airer_drying` | Switch | 烘干功能 |
| `switch.hotata_airer_air_drying` | Switch | 风干功能 |
| `switch.hotata_airer_disinfection` | Switch | 消毒功能 |
| `switch.hotata_airer_ions` | Switch | 负离子功能 |
| `sensor.hotata_airer_position` | Sensor | 晾衣架位置 (%) |
| `sensor.hotata_airer_light_remaining_time` | Sensor | 照明剩余时间 (分钟) |
| `sensor.hotata_airer_disinfection_remaining_time` | Sensor | 消毒剩余时间 (分钟) |
| `binary_sensor.hotata_airer_online_status` | Binary Sensor | 设备在线状态 |

## 技术信息

- **API 端点**: `saas.keyoo.com/app-api/v2.0/`
- **轮询间隔**: 5 秒
- **Token 有效期**: 约 30 天（自动刷新）

## 注意事项

1. **refresh_token 是一次性的**，不要同时在多个地方刷新
2. 如果集成显示 `unavailable`，可能是 token 过期，需要重新配置
3. 设备断电后会显示离线状态

## 故障排除

### 实体显示 unavailable

1. 检查设备是否正常通电
2. 检查 token 是否过期（查看在线状态实体）
3. 重新配置集成，使用新的 token

### 无法控制设备

1. 确认设备在线
2. 检查 HA 日志是否有 API 错误
3. 尝试重启 Home Assistant

## 免责声明

本集成为非官方开发，使用好太太开放 API。作者不对设备损坏或数据丢失负责。

## 许可证

[MIT](LICENSE) © C3H3-AI
