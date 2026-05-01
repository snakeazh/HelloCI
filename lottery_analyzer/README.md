# 🎯 排列五号码分布分析工具

自定义分析规则，回测验证你的选号思路正确率。

## 功能特性

- **按位号码分布** — 万/千/百/十/个位 0-9 出现频率可视化
- **9种分析规则** — 冷热号、遗漏、和值、跨度、大小比、奇偶比、同位重号、组选形态、走势
- **回测验证** — 用历史数据逐期验证，输出单位正确率和各位命中率
- **排列五专用** — 完全针对排列五5位×0-9的特性设计

## 快速开始

```bash
# 安装依赖
pip install -r requirements.txt

# 生成示例数据（500期模拟数据）
python3 generate_sample_data.py

# 启动应用
python3 app.py
```

打开浏览器访问 http://localhost:5000

## 数据格式

```json
{"period": "2024001", "digits": [1, 2, 3, 4, 5]}
```

- `period`: 期号
- `digits`: 5位数字数组 [万位, 千位, 百位, 十位, 个位]，每位取值0-9

## 分析规则

| 规则 | 说明 |
|------|------|
| 按位冷热号 | 各位近N期出现频率，选热号/冷号 |
| 按位遗漏分析 | 各位号码遗漏期数，找回补号 |
| 和值分析 | 五位数字之和的分布规律 |
| 跨度分析 | 最大值-最小值的跨度规律 |
| 大小比分析 | 大号(5-9)/小号(0-4)比例 |
| 奇偶比分析 | 奇数/偶数比例规律 |
| 同位重号分析 | 与上期同位置重复号码 |
| 组选形态分析 | 号码重复形态(全不同/一对/双对等) |
| 走势分析 | 各位升降趋势 |

## API 接口

- `GET /api/history` — 获取历史数据
- `GET /api/distribution?position=0-4` — 按位号码分布（-1为全部）
- `GET /api/rules` — 获取可用分析规则
- `POST /api/analyze` — 执行分析 `{rule, params}`
- `POST /api/backtest` — 回测验证 `{rule, params, test_periods}`
- `POST /api/upload_history` — 上传真实历史数据

## 如何导入真实数据

通过 API 上传：

```bash
curl -X POST http://localhost:5000/api/upload_history \
  -H "Content-Type: application/json" \
  -d '{"records": [{"period": "24001", "digits": [3,5,7,2,9]}, ...]}'
```

或直接编辑 `data/pl5.json` 文件后重启应用。
