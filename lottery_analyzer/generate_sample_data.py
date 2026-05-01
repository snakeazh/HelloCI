"""生成排列五模拟历史数据"""
import json
import os
import random

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")


def generate_pl5_data(num_periods=500):
    """
    生成排列五模拟数据
    排列五规则：5个位置，每位从0-9中选一个数字（可重复）
    """
    records = []
    for i in range(num_periods):
        year = 2024 if i < 365 else 2025
        day_idx = i if i < 365 else i - 365
        period = f"{year}{day_idx + 1:03d}"
        digits = [random.randint(0, 9) for _ in range(5)]
        records.append({"period": period, "digits": digits})
    return records


if __name__ == "__main__":
    os.makedirs(DATA_DIR, exist_ok=True)
    random.seed(42)
    data = generate_pl5_data(500)
    with open(os.path.join(DATA_DIR, "pl5.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"生成排列五模拟数据: {len(data)} 期")
    print(f"示例: {data[-1]}")
