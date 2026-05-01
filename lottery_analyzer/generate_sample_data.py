"""生成示例历史数据（基于真实双色球/大乐透号码规则的模拟数据）"""
import json
import os
import random

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")


def generate_ssq_data(num_periods=200):
    """生成双色球模拟数据：6个红球(1-33) + 1个蓝球(1-16)"""
    records = []
    for i in range(num_periods):
        period = f"2024{(i // 3 + 1):03d}"
        red = sorted(random.sample(range(1, 34), 6))
        blue = random.randint(1, 16)
        records.append({"period": period, "red": red, "blue": [blue]})
    return records


def generate_dlt_data(num_periods=200):
    """生成大乐透模拟数据：5个红球(1-35) + 2个蓝球(1-12)"""
    records = []
    for i in range(num_periods):
        period = f"2024{(i // 3 + 1):03d}"
        red = sorted(random.sample(range(1, 36), 5))
        blue = sorted(random.sample(range(1, 13), 2))
        records.append({"period": period, "red": red, "blue": blue})
    return records


if __name__ == "__main__":
    os.makedirs(DATA_DIR, exist_ok=True)

    random.seed(42)

    ssq_data = generate_ssq_data(200)
    with open(os.path.join(DATA_DIR, "ssq.json"), "w", encoding="utf-8") as f:
        json.dump(ssq_data, f, ensure_ascii=False, indent=2)
    print(f"生成双色球数据: {len(ssq_data)} 期")

    dlt_data = generate_dlt_data(200)
    with open(os.path.join(DATA_DIR, "dlt.json"), "w", encoding="utf-8") as f:
        json.dump(dlt_data, f, ensure_ascii=False, indent=2)
    print(f"生成大乐透数据: {len(dlt_data)} 期")
