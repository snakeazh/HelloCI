"""彩票分析引擎 - 核心逻辑"""
import json
import os
from collections import Counter
from typing import Any

import numpy as np
import pandas as pd

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")


LOTTERY_CONFIG = {
    "ssq": {
        "name": "双色球",
        "red_range": (1, 33),
        "red_count": 6,
        "blue_range": (1, 16),
        "blue_count": 1,
    },
    "dlt": {
        "name": "大乐透",
        "red_range": (1, 35),
        "red_count": 5,
        "blue_range": (1, 12),
        "blue_count": 2,
    },
}


class LotteryAnalyzer:
    def __init__(self):
        self.history = {}
        self._load_data()

    def _load_data(self):
        """加载历史数据"""
        for lottery_type in LOTTERY_CONFIG:
            filepath = os.path.join(DATA_DIR, f"{lottery_type}.json")
            if os.path.exists(filepath):
                with open(filepath, "r", encoding="utf-8") as f:
                    self.history[lottery_type] = json.load(f)
            else:
                self.history[lottery_type] = []

    def _save_data(self, lottery_type):
        """保存数据到文件"""
        os.makedirs(DATA_DIR, exist_ok=True)
        filepath = os.path.join(DATA_DIR, f"{lottery_type}.json")
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.history[lottery_type], f, ensure_ascii=False, indent=2)

    def get_lottery_types(self) -> list[dict]:
        return [
            {"id": k, "name": v["name"], "config": v}
            for k, v in LOTTERY_CONFIG.items()
        ]

    def get_history(self, lottery_type: str) -> dict:
        records = self.history.get(lottery_type, [])
        return {"lottery_type": lottery_type, "count": len(records), "records": records}

    def add_history(self, lottery_type: str, records: list[dict]) -> dict:
        if lottery_type not in LOTTERY_CONFIG:
            return {"success": False, "error": "不支持的彩票类型"}
        if lottery_type not in self.history:
            self.history[lottery_type] = []
        self.history[lottery_type].extend(records)
        self.history[lottery_type].sort(key=lambda x: x.get("period", ""))
        self._save_data(lottery_type)
        return {"success": True, "total_records": len(self.history[lottery_type])}

    def get_distribution(self, lottery_type: str, zone: str = "red") -> dict:
        """获取号码出现频率分布"""
        records = self.history.get(lottery_type, [])
        if not records:
            return {"error": "暂无历史数据"}

        config = LOTTERY_CONFIG[lottery_type]
        if zone == "red":
            num_range = config["red_range"]
            numbers = []
            for r in records:
                numbers.extend(r.get("red", []))
        else:
            num_range = config["blue_range"]
            numbers = []
            for r in records:
                blues = r.get("blue", [])
                if isinstance(blues, list):
                    numbers.extend(blues)
                else:
                    numbers.append(blues)

        counter = Counter(numbers)
        total_draws = len(records)
        distribution = []
        for num in range(num_range[0], num_range[1] + 1):
            count = counter.get(num, 0)
            distribution.append({
                "number": num,
                "count": count,
                "frequency": round(count / total_draws, 4) if total_draws > 0 else 0,
            })

        return {
            "lottery_type": lottery_type,
            "zone": zone,
            "total_draws": total_draws,
            "distribution": distribution,
        }

    def get_available_rules(self) -> list[dict]:
        """返回所有可用的分析规则"""
        return [
            {
                "id": "hot_cold",
                "name": "冷热号分析",
                "description": "根据近N期出现频率判断号码冷热状态，预测下期可能出现的热号或冷号回补",
                "params": [
                    {"name": "window", "type": "int", "default": 10, "description": "观察窗口期数"},
                    {"name": "strategy", "type": "select", "options": ["hot", "cold", "mixed"], "default": "hot", "description": "策略：选热号/选冷号/混合"},
                    {"name": "zone", "type": "select", "options": ["red", "blue"], "default": "red", "description": "分析区域"},
                ],
            },
            {
                "id": "interval",
                "name": "间隔期数分析",
                "description": "分析每个号码的出现间隔规律，预测即将到期出现的号码",
                "params": [
                    {"name": "zone", "type": "select", "options": ["red", "blue"], "default": "red", "description": "分析区域"},
                    {"name": "threshold_ratio", "type": "float", "default": 1.5, "description": "超过平均间隔的倍数阈值"},
                ],
            },
            {
                "id": "sum_range",
                "name": "和值范围分析",
                "description": "统计红球和值的分布区间，预测下期和值区间范围",
                "params": [
                    {"name": "bins", "type": "int", "default": 6, "description": "和值区间划分数量"},
                ],
            },
            {
                "id": "odd_even",
                "name": "奇偶比分析",
                "description": "分析历史奇偶比例分布，预测下期奇偶比",
                "params": [
                    {"name": "window", "type": "int", "default": 20, "description": "观察窗口期数"},
                ],
            },
            {
                "id": "consecutive",
                "name": "连号分析",
                "description": "分析连号出现的规律和频率",
                "params": [
                    {"name": "window", "type": "int", "default": 30, "description": "观察窗口期数"},
                ],
            },
            {
                "id": "zone_ratio",
                "name": "区间比分析",
                "description": "将号码按区间划分，分析各区间出号比例",
                "params": [
                    {"name": "zones", "type": "int", "default": 3, "description": "区间数量"},
                    {"name": "window", "type": "int", "default": 30, "description": "观察窗口期数"},
                ],
            },
            {
                "id": "repeat",
                "name": "重号分析",
                "description": "分析与上期重复号码的规律",
                "params": [
                    {"name": "window", "type": "int", "default": 50, "description": "观察窗口期数"},
                ],
            },
        ]

    def run_analysis(self, lottery_type: str, rule: str, params: dict) -> dict:
        """执行单次分析"""
        records = self.history.get(lottery_type, [])
        if not records:
            return {"error": "暂无历史数据"}

        method = getattr(self, f"_rule_{rule}", None)
        if method is None:
            return {"error": f"未知的分析规则: {rule}"}

        return method(records, LOTTERY_CONFIG[lottery_type], params)

    def backtest(self, lottery_type: str, rule: str, params: dict, test_periods: int = 50) -> dict:
        """回测验证：用历史数据前N-test_periods期做分析，逐期验证预测结果"""
        records = self.history.get(lottery_type, [])
        if len(records) < test_periods + 10:
            return {"error": f"历史数据不足，需要至少 {test_periods + 10} 期数据"}

        method = getattr(self, f"_rule_{rule}", None)
        if method is None:
            return {"error": f"未知的分析规则: {rule}"}

        config = LOTTERY_CONFIG[lottery_type]
        results = []
        hits = 0

        for i in range(test_periods):
            end_idx = len(records) - test_periods + i
            train_data = records[:end_idx]
            actual = records[end_idx]

            prediction = method(train_data, config, params)
            if "error" in prediction:
                continue

            predicted_numbers = prediction.get("predicted_numbers", [])
            zone = params.get("zone", "red")

            if zone == "red":
                actual_numbers = set(actual.get("red", []))
            else:
                blue = actual.get("blue", [])
                actual_numbers = set(blue if isinstance(blue, list) else [blue])

            hit_numbers = set(predicted_numbers) & actual_numbers
            hit = len(hit_numbers) > 0

            if hit:
                hits += 1

            results.append({
                "period": actual.get("period", f"第{end_idx+1}期"),
                "predicted": sorted(predicted_numbers),
                "actual": sorted(actual_numbers),
                "hit_numbers": sorted(hit_numbers),
                "hit_count": len(hit_numbers),
                "hit": hit,
            })

        accuracy = hits / len(results) if results else 0
        avg_hit_count = sum(r["hit_count"] for r in results) / len(results) if results else 0

        return {
            "lottery_type": lottery_type,
            "rule": rule,
            "params": params,
            "test_periods": len(results),
            "hits": hits,
            "accuracy": round(accuracy, 4),
            "accuracy_pct": f"{accuracy*100:.1f}%",
            "avg_hit_count": round(avg_hit_count, 2),
            "details": results,
        }

    # ========== 分析规则实现 ==========

    def _rule_hot_cold(self, records: list, config: dict, params: dict) -> dict:
        """冷热号分析"""
        window = params.get("window", 10)
        strategy = params.get("strategy", "hot")
        zone = params.get("zone", "red")

        recent = records[-window:]

        if zone == "red":
            num_range = config["red_range"]
            pick_count = config["red_count"]
            numbers = []
            for r in recent:
                numbers.extend(r.get("red", []))
        else:
            num_range = config["blue_range"]
            pick_count = config["blue_count"]
            numbers = []
            for r in recent:
                blues = r.get("blue", [])
                if isinstance(blues, list):
                    numbers.extend(blues)
                else:
                    numbers.append(blues)

        counter = Counter(numbers)
        all_nums = list(range(num_range[0], num_range[1] + 1))

        sorted_by_freq = sorted(all_nums, key=lambda x: counter.get(x, 0), reverse=True)

        if strategy == "hot":
            predicted = sorted_by_freq[:pick_count]
        elif strategy == "cold":
            predicted = sorted_by_freq[-pick_count:]
        else:
            half = pick_count // 2
            predicted = sorted_by_freq[:half] + sorted_by_freq[-(pick_count - half):]

        freq_data = [{"number": n, "count": counter.get(n, 0)} for n in all_nums]

        return {
            "rule": "hot_cold",
            "strategy": strategy,
            "window": window,
            "zone": zone,
            "predicted_numbers": sorted(predicted),
            "frequency_data": freq_data,
            "description": f"基于近{window}期{'热号' if strategy == 'hot' else '冷号' if strategy == 'cold' else '混合'}策略",
        }

    def _rule_interval(self, records: list, config: dict, params: dict) -> dict:
        """间隔期数分析"""
        zone = params.get("zone", "red")
        threshold_ratio = params.get("threshold_ratio", 1.5)

        if zone == "red":
            num_range = config["red_range"]
            pick_count = config["red_count"]
        else:
            num_range = config["blue_range"]
            pick_count = config["blue_count"]

        last_seen = {}
        intervals = {n: [] for n in range(num_range[0], num_range[1] + 1)}

        for idx, r in enumerate(records):
            if zone == "red":
                nums = r.get("red", [])
            else:
                blues = r.get("blue", [])
                nums = blues if isinstance(blues, list) else [blues]

            for n in nums:
                if n in last_seen:
                    intervals[n].append(idx - last_seen[n])
                last_seen[n] = idx

        current_gap = {}
        total_periods = len(records)
        for n in range(num_range[0], num_range[1] + 1):
            current_gap[n] = total_periods - last_seen.get(n, 0)

        avg_intervals = {}
        for n, ivs in intervals.items():
            avg_intervals[n] = np.mean(ivs) if ivs else total_periods

        overdue = []
        for n in range(num_range[0], num_range[1] + 1):
            ratio = current_gap[n] / avg_intervals[n] if avg_intervals[n] > 0 else 0
            if ratio >= threshold_ratio:
                overdue.append({"number": n, "current_gap": current_gap[n], "avg_interval": round(avg_intervals[n], 1), "ratio": round(ratio, 2)})

        overdue.sort(key=lambda x: x["ratio"], reverse=True)
        predicted = [item["number"] for item in overdue[:pick_count]]

        return {
            "rule": "interval",
            "zone": zone,
            "threshold_ratio": threshold_ratio,
            "predicted_numbers": sorted(predicted),
            "overdue_numbers": overdue,
            "description": f"超过平均间隔{threshold_ratio}倍的号码",
        }

    def _rule_sum_range(self, records: list, config: dict, params: dict) -> dict:
        """和值范围分析"""
        bins = params.get("bins", 6)

        sums = [sum(r.get("red", [])) for r in records]
        if not sums:
            return {"error": "无数据"}

        min_sum = min(sums)
        max_sum = max(sums)
        bin_size = (max_sum - min_sum) / bins

        bin_counts = [0] * bins
        for s in sums:
            bin_idx = min(int((s - min_sum) / bin_size), bins - 1)
            bin_counts[bin_idx] += 1

        recent_sums = sums[-10:]
        recent_avg = np.mean(recent_sums)

        most_common_bin = np.argmax(bin_counts)
        predicted_range = (
            round(min_sum + most_common_bin * bin_size),
            round(min_sum + (most_common_bin + 1) * bin_size),
        )

        bin_data = []
        for i in range(bins):
            low = round(min_sum + i * bin_size)
            high = round(min_sum + (i + 1) * bin_size)
            bin_data.append({
                "range": f"{low}-{high}",
                "count": bin_counts[i],
                "frequency": round(bin_counts[i] / len(sums), 4),
            })

        red_count = config["red_count"]
        red_range = config["red_range"]
        avg_num = (predicted_range[0] + predicted_range[1]) / 2 / red_count
        predicted_numbers = []
        step = (red_range[1] - red_range[0]) / (red_count + 1)
        for i in range(red_count):
            n = int(round(red_range[0] + step * (i + 1) + np.random.uniform(-2, 2)))
            n = max(red_range[0], min(red_range[1], n))
            predicted_numbers.append(n)
        predicted_numbers = sorted(set(predicted_numbers))[:red_count]

        return {
            "rule": "sum_range",
            "predicted_sum_range": predicted_range,
            "predicted_numbers": predicted_numbers,
            "recent_average": round(recent_avg, 1),
            "bin_data": bin_data,
            "description": f"预测和值区间 {predicted_range[0]}-{predicted_range[1]}",
        }

    def _rule_odd_even(self, records: list, config: dict, params: dict) -> dict:
        """奇偶比分析"""
        window = params.get("window", 20)
        recent = records[-window:]

        ratios = []
        for r in recent:
            reds = r.get("red", [])
            odd_count = sum(1 for n in reds if n % 2 == 1)
            ratios.append(odd_count)

        avg_odd = np.mean(ratios)
        red_count = config["red_count"]
        predicted_odd = round(avg_odd)
        predicted_even = red_count - predicted_odd

        red_range = config["red_range"]
        odds = [n for n in range(red_range[0], red_range[1] + 1) if n % 2 == 1]
        evens = [n for n in range(red_range[0], red_range[1] + 1) if n % 2 == 0]

        all_numbers = []
        for r in recent:
            all_numbers.extend(r.get("red", []))
        counter = Counter(all_numbers)

        hot_odds = sorted(odds, key=lambda x: counter.get(x, 0), reverse=True)[:predicted_odd]
        hot_evens = sorted(evens, key=lambda x: counter.get(x, 0), reverse=True)[:predicted_even]
        predicted_numbers = sorted(hot_odds + hot_evens)

        ratio_dist = Counter([f"{o}:{red_count - o}" for o in ratios])

        return {
            "rule": "odd_even",
            "predicted_ratio": f"{predicted_odd}:{predicted_even}",
            "predicted_numbers": predicted_numbers,
            "ratio_distribution": dict(ratio_dist),
            "avg_odd_count": round(avg_odd, 2),
            "description": f"预测奇偶比 {predicted_odd}:{predicted_even}",
        }

    def _rule_consecutive(self, records: list, config: dict, params: dict) -> dict:
        """连号分析"""
        window = params.get("window", 30)
        recent = records[-window:]

        consecutive_stats = []
        for r in recent:
            reds = sorted(r.get("red", []))
            consecutive_pairs = []
            for i in range(len(reds) - 1):
                if reds[i + 1] - reds[i] == 1:
                    consecutive_pairs.append((reds[i], reds[i + 1]))
            consecutive_stats.append({
                "period": r.get("period", ""),
                "count": len(consecutive_pairs),
                "pairs": consecutive_pairs,
            })

        has_consecutive_ratio = sum(1 for s in consecutive_stats if s["count"] > 0) / len(consecutive_stats)
        all_consecutive_nums = []
        for s in consecutive_stats:
            for pair in s["pairs"]:
                all_consecutive_nums.extend(pair)

        counter = Counter(all_consecutive_nums)
        red_range = config["red_range"]
        red_count = config["red_count"]

        hot_consecutive = sorted(counter.keys(), key=lambda x: counter[x], reverse=True)
        predicted_numbers = sorted(hot_consecutive[:red_count]) if hot_consecutive else []

        return {
            "rule": "consecutive",
            "predicted_numbers": predicted_numbers,
            "has_consecutive_probability": round(has_consecutive_ratio, 4),
            "hot_consecutive_numbers": [{"number": n, "count": counter[n]} for n in hot_consecutive[:10]],
            "description": f"近{window}期中{has_consecutive_ratio*100:.0f}%含连号",
        }

    def _rule_zone_ratio(self, records: list, config: dict, params: dict) -> dict:
        """区间比分析"""
        zones_count = params.get("zones", 3)
        window = params.get("window", 30)
        recent = records[-window:]

        red_range = config["red_range"]
        red_count = config["red_count"]
        zone_size = (red_range[1] - red_range[0] + 1) / zones_count

        zone_counts = [0] * zones_count
        total_nums = 0

        for r in recent:
            for n in r.get("red", []):
                zone_idx = min(int((n - red_range[0]) / zone_size), zones_count - 1)
                zone_counts[zone_idx] += 1
                total_nums += 1

        zone_ratios = [round(c / total_nums, 4) if total_nums > 0 else 0 for c in zone_counts]
        predicted_per_zone = [round(r * red_count) for r in zone_ratios]

        diff = red_count - sum(predicted_per_zone)
        if diff != 0:
            max_zone = np.argmax(zone_ratios)
            predicted_per_zone[max_zone] += diff

        predicted_numbers = []
        for z_idx in range(zones_count):
            zone_start = red_range[0] + int(z_idx * zone_size)
            zone_end = red_range[0] + int((z_idx + 1) * zone_size) - 1
            zone_nums = list(range(zone_start, zone_end + 1))

            all_zone_nums = []
            for r in recent:
                for n in r.get("red", []):
                    if zone_start <= n <= zone_end:
                        all_zone_nums.append(n)
            counter = Counter(all_zone_nums)
            hot = sorted(zone_nums, key=lambda x: counter.get(x, 0), reverse=True)
            predicted_numbers.extend(hot[:predicted_per_zone[z_idx]])

        zone_data = []
        for i in range(zones_count):
            zone_start = red_range[0] + int(i * zone_size)
            zone_end = red_range[0] + int((i + 1) * zone_size) - 1
            zone_data.append({
                "zone": f"{zone_start}-{zone_end}",
                "count": zone_counts[i],
                "ratio": zone_ratios[i],
                "predicted_count": predicted_per_zone[i],
            })

        return {
            "rule": "zone_ratio",
            "predicted_numbers": sorted(predicted_numbers)[:red_count],
            "zone_data": zone_data,
            "description": f"按{zones_count}区间分配号码",
        }

    def _rule_repeat(self, records: list, config: dict, params: dict) -> dict:
        """重号分析"""
        window = params.get("window", 50)
        recent = records[-window:] if len(records) >= window else records

        repeat_stats = []
        for i in range(1, len(recent)):
            prev_reds = set(recent[i - 1].get("red", []))
            curr_reds = set(recent[i].get("red", []))
            repeats = prev_reds & curr_reds
            repeat_stats.append({
                "period": recent[i].get("period", ""),
                "repeat_count": len(repeats),
                "repeat_numbers": sorted(repeats),
            })

        avg_repeat = np.mean([s["repeat_count"] for s in repeat_stats]) if repeat_stats else 0
        last_reds = records[-1].get("red", [])

        all_repeats = []
        for s in repeat_stats:
            all_repeats.extend(s["repeat_numbers"])
        repeat_freq = Counter(all_repeats)

        predicted_count = round(avg_repeat)
        predicted_from_last = sorted(last_reds, key=lambda x: repeat_freq.get(x, 0), reverse=True)[:predicted_count]

        repeat_dist = Counter([s["repeat_count"] for s in repeat_stats])

        return {
            "rule": "repeat",
            "predicted_numbers": sorted(predicted_from_last),
            "avg_repeat_count": round(avg_repeat, 2),
            "last_period_numbers": sorted(last_reds),
            "repeat_distribution": dict(sorted(repeat_dist.items())),
            "description": f"平均每期与上期有{avg_repeat:.1f}个重号",
        }
