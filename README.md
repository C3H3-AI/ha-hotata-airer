# Hotata Airer (好太太智能晾衣机)

[![GitHub Release](https://img.shields.io/github/v/release/C3H3-AI/ha-hotata-airer?style=flat-square)](https://github.com/C3H3-AI/ha-hotata-airer/releases)
[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5?style=flat-square)](https://github.com/hacs/integration)

Home Assistant 自定义集成，支持好太太智能晾衣机的完整控制。

## 功能特性

| 功能 | 说明 |
|------|------|
| 晾衣架升降 | cover 实体，支持开/关/停 |
| 照明控制 | light 实体，支持开关和亮度调节 |
| 电源状态 | binary_sensor 实体，实时监测 |
| 烘干/风干/消毒/负离子 | switch 实体，独立控制 |
| 定时提醒 | sensor 实体，显示剩余时间 |
| 在线状态 | binary_sensor 实体，设备连接状态 |
| 自动 Token 刷新 | 无需手动刷新，长期稳定运行 |

## 安装方式

### 方式一：HACS (推荐)

1. 安装 [HACS](https://hacs.xyz/)
2. HACS → 集成 → 右上角三点菜单 → 添加自定义存储库
3. 仓库地址: `https://github.com/C3H3-AI/ha-hotata-airer`
4. 搜索并安装 **Hotata Airer**
5. 重启 Home Assistant

### 方式二：手动安装

```bash
# 克隆仓库
git clone https://github.com/C3H3-AI/ha-hotata-airer.git

# 复制到 HA 自定义组件目录
cp -r custom_components/hotata_airer /path/to/your/ha/config/custom_components/

# 重启 HA
```

## 配置

集成通过 UI 配置，无需编辑 YAML。

1. **配置 → 设备与服务 → 添加集成**
2. 搜索 **Hotata Airer**
3. 填入从微信好太太小程序抓包获取的 **refreshToken**

### 配置参数说明

| 参数 | 说明 |
|------|------|
| refreshToken | 必填，从微信好太太小程序抓包获取 |
| 名称 | 可选，设备显示名称 |

> **提示**: 只需提供 refreshToken，其他参数会自动获取。

## 实体列表

### binary_sensor (状态传感器)

| 实体 ID | 中文名称 | 说明 |
|---------|---------|------|
| `binary_sensor.hotata_airer_online_status` | 在线状态 | 设备是否在线 |
| `binary_sensor.hao_tai_tai_liang_yi_ji_dian_yuan_kai_guan` | 电源开关 | 电源是否开启 |

### cover (晾衣架)

| 实体 ID | 中文名称 | 说明 |
|---------|---------|------|
| `cover.hao_tai_tai_liang_yi_ji` | 晾衣机 | 晾衣架升降控制 |

### light (照明)

| 实体 ID | 中文名称 | 说明 |
|---------|---------|------|
| `light.hao_tai_tai_liang_yi_ji_zhao_ming` | 照明 | 灯光开关和亮度控制 |

### sensor (传感器)

| 实体 ID | 中文名称 | 说明 |
|---------|---------|------|
| `sensor.hao_tai_tai_liang_yi_ji_position` | 位置 | 当前晾衣架位置 |
| `sensor.hao_tai_tai_liang_yi_ji_light_remaining_time` | 照明剩余时间 | 照明定时剩余分钟数 |
| `sensor.hao_tai_tai_liang_yi_ji_disinfection_remaining_time` | 消毒剩余时间 | 消毒定时剩余分钟数 |
| `sensor.hao_tai_tai_liang_yi_ji_drying_remaining_time` | 烘干剩余时间 | 烘干定时剩余分钟数 |
| `sensor.hao_tai_tai_liang_yi_ji_air_drying_remaining_time` | 风干剩余时间 | 风干定时剩余分钟数 |
| `sensor.hao_tai_tai_liang_yi_ji_ions_remaining_time` | 负离子剩余时间 | 负离子定时剩余分钟数 |
| `sensor.hao_tai_tai_liang_yi_ji_motor_control_mode` | 电机模式 | 当前运行模式 |

### switch (开关)

| 实体 ID | 中文名称 | 说明 |
|---------|---------|------|
| `switch.hao_tai_tai_liang_yi_ji_dian_yuan` | 电源 | 总电源开关 |
| `switch.hao_tai_tai_liang_yi_ji_hong_gan` | 烘干 | 烘干功能开关 |
| `switch.hao_tai_tai_liang_yi_ji_feng_gan` | 风干 | 风干功能开关 |
| `switch.hao_tai_tai_liang_yi_ji_xiao_du` | 消毒 | 消毒功能开关 |
| `switch.hao_tai_tai_liang_yi_ji_fu_li_zi` | 负离子 | 负离子功能开关 |

## 故障排查

| 问题 | 解决方案 |
|------|----------|
| 实体不出现 | 重启 HA，检查 refreshToken 是否正确 |
| 设备离线 | 检查网络连接，确认 token 未过期 |
| 控制无响应 | 检查 HA 日志查看错误信息 |

## 版本历史

- **v2.1.0**: 同步本地最新版本，优化 Token 刷新机制
- **v2.0.0**: 初始公开版本

## License

[CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/)

---

Made with ❤️ by [C3H3-AI](https://github.com/C3H3-AI)
