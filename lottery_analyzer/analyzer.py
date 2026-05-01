"""排列五号码分布分析引擎 - 预测任意3个号码"""
import json
import os
from collections import Counter
from itertools import combinations

import numpy as np

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

POSITION_NAMES = ["万位", "千位", "百位", "十位", "个位"]


class LotteryAnalyzer:
    def __init__(self):
        self.history = []
        self._load_data()

    def _load_data(self):
        """加载排列五历史数据"""
        filepath = os.path.join(DATA_DIR, "pl5.json")
        if os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8") as f:
                self.history = json.load(f)

    def _save_data(self):
        """保存数据"""
        os.makedirs(DATA_DIR, exist_ok=True)
        filepath = os.path.join(DATA_DIR, "pl5.json")
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.history, f, ensure_ascii=False, indent=2)

    def get_history(self) -> dict:
        return {"count": len(self.history), "records": self.history}

    def add_history(self, records: list[dict]) -> dict:
        """添加历史数据，格式: [{"period": "24001", "digits": [1,2,3,4,5]}, ...]"""
        self.history.extend(records)
        self.history.sort(key=lambda x: x.get("period", ""))
        self._save_data()
        return {"success": True, "total_records": len(self.history)}

    def get_distribution(self, position: int = -1) -> dict:
        """获取号码分布。position=-1 表示全部位置汇总，0-4 表示指定位"""
        if not self.history:
            return {"error": "暂无历史数据"}

        total_draws = len(self.history)

        if position == -1:
            result = {"total_draws": total_draws, "positions": []}
            for pos in range(5):
                numbers = [r["digits"][pos] for r in self.history]
                counter = Counter(numbers)
                dist = [{"number": n, "count": counter.get(n, 0),
                         "frequency": round(counter.get(n, 0) / total_draws, 4)}
                        for n in range(10)]
                result["positions"].append({
                    "position": pos,
                    "name": POSITION_NAMES[pos],
                    "distribution": dist,
                })
            return result
        else:
            numbers = [r["digits"][position] for r in self.history]
            counter = Counter(numbers)
            dist = [{"number": n, "count": counter.get(n, 0),
                     "frequency": round(counter.get(n, 0) / total_draws, 4)}
                    for n in range(10)]
            return {
                "total_draws": total_draws,
                "position": position,
                "name": POSITION_NAMES[position],
                "distribution": dist,
            }

    def get_available_rules(self) -> list[dict]:
        """返回所有可用分析规则（预测任意3个号码模式）"""
        return [
            {
                "id": "pick3_frequency",
                "name": "频率选号",
                "description": "统计近N期所有位置出现的数字频率，选出现最多的3个号码",
                "params": [
                    {"name": "window", "type": "int", "default": 20, "description": "观察窗口期数"},
                    {"name": "strategy", "type": "select", "options": ["hot", "cold", "mixed"], "default": "hot", "description": "选热号/冷号/混合"},
                ],
            },
            {
                "id": "pick3_overdue",
                "name": "遗漏回补",
                "description": "找出长期未出现的号码，认为它们即将回补出现",
                "params": [
                    {"name": "threshold", "type": "int", "default": 5, "description": "遗漏期数阈值"},
                ],
            },
            {
                "id": "pick3_neighbor",
                "name": "邻号跟随",
                "description": "基于上期开奖号码的邻号（+1/-1）出现概率高的规律",
                "params": [
                    {"name": "range_size", "type": "int", "default": 1, "description": "邻号范围(±N)"},
                ],
            },
            {
                "id": "pick3_repeat",
                "name": "重号策略",
                "description": "上期出现的5个号码中，选出最可能在下期重复出现的3个",
                "params": [
                    {"name": "window", "type": "int", "default": 30, "description": "观察窗口期数"},
                ],
            },
            {
                "id": "pick3_combo_hot",
                "name": "热门组合",
                "description": "统计历史上哪些3个数字的组合最经常同时出现在同一期",
                "params": [
                    {"name": "window", "type": "int", "default": 100, "description": "观察窗口期数"},
                ],
            },
            {
                "id": "pick3_trend_follow",
                "name": "趋势跟踪",
                "description": "分析近期号码走势，选出持续上升或持续活跃的3个号码",
                "params": [
                    {"name": "window", "type": "int", "default": 10, "description": "观察窗口期数"},
                ],
            },
            {
                "id": "pick3_odd_even_balance",
                "name": "奇偶均衡",
                "description": "根据近期奇偶出现比例，选出最可能出现的2奇1偶或2偶1奇组合",
                "params": [
                    {"name": "window", "type": "int", "default": 20, "description": "观察窗口期数"},
                ],
            },
            {
                "id": "pick3_section",
                "name": "分区选号",
                "description": "将0-9分为3区(0-3/4-6/7-9)，每区选出最活跃的1个号码",
                "params": [
                    {"name": "window", "type": "int", "default": 20, "description": "观察窗口期数"},
                ],
            },
            {
                "id": "pick3_gap_pattern",
                "name": "间距规律",
                "description": "分析相邻期号码间距规律，预测下期可能出现在特定间距的号码",
                "params": [
                    {"name": "window", "type": "int", "default": 15, "description": "观察窗口期数"},
                ],
            },
        ]

    def run_analysis(self, rule: str, params: dict) -> dict:
        """执行单次分析，返回预测的3个号码"""
        if not self.history:
            return {"error": "暂无历史数据"}

        method = getattr(self, f"_rule_{rule}", None)
        if method is None:
            return {"error": f"未知的分析规则: {rule}"}

        return method(self.history, params)

    def backtest(self, rule: str, params: dict, test_periods: int = 50) -> dict:
        """回测验证：预测3个号码，判断是否全部出现在开奖的5位数字中"""
        if len(self.history) < test_periods + 30:
            return {"error": f"历史数据不足，需要至少 {test_periods + 30} 期数据"}

        method = getattr(self, f"_rule_{rule}", None)
        if method is None:
            return {"error": f"未知的分析规则: {rule}"}

        results = []
        all3_hits = 0
        at_least2_hits = 0
        at_least1_hits = 0

        for i in range(test_periods):
            end_idx = len(self.history) - test_periods + i
            train_data = self.history[:end_idx]
            actual = self.history[end_idx]

            prediction = method(train_data, params)
            if "error" in prediction:
                continue

            predicted_3 = prediction.get("predicted_numbers", [])[:3]
            actual_digits = actual["digits"]
            actual_set = set(actual_digits)

            hit_numbers = [n for n in predicted_3 if n in actual_set]
            hit_count = len(hit_numbers)

            if hit_count == 3:
                all3_hits += 1
            if hit_count >= 2:
                at_least2_hits += 1
            if hit_count >= 1:
                at_least1_hits += 1

            results.append({
                "period": actual.get("period", f"第{end_idx+1}期"),
                "predicted": predicted_3,
                "actual_digits": actual_digits,
                "actual_set": sorted(actual_set),
                "hit_numbers": hit_numbers,
                "hit_count": hit_count,
                "all_hit": hit_count == 3,
            })

        total = len(results)
        all3_rate = all3_hits / total if total > 0 else 0
        at_least2_rate = at_least2_hits / total if total > 0 else 0
        at_least1_rate = at_least1_hits / total if total > 0 else 0
        avg_hit = sum(r["hit_count"] for r in results) / total if total > 0 else 0

        return {
            "rule": rule,
            "params": params,
            "test_periods": total,
            "all3_hits": all3_hits,
            "all3_rate": round(all3_rate, 4),
            "all3_rate_pct": f"{all3_rate*100:.1f}%",
            "at_least2_hits": at_least2_hits,
            "at_least2_rate_pct": f"{at_least2_rate*100:.1f}%",
            "at_least1_hits": at_least1_hits,
            "at_least1_rate_pct": f"{at_least1_rate*100:.1f}%",
            "avg_hit_count": round(avg_hit, 2),
            "details": results,
        }

    # ========== 预测任意3个号码 - 分析规则 ==========

    def _rule_pick3_frequency(self, records: list, params: dict) -> dict:
        """频率选号：统计所有位置出现频率最高/最低的3个号码"""
        window = params.get("window", 20)
        strategy = params.get("strategy", "hot")
        recent = records[-window:]

        all_digits = []
        for r in recent:
            all_digits.extend(r["digits"])
        counter = Counter(all_digits)

        sorted_nums = sorted(range(10), key=lambda x: counter.get(x, 0), reverse=True)

        if strategy == "hot":
            predicted = sorted_nums[:3]
        elif strategy == "cold":
            predicted = sorted_nums[-3:]
        else:
            predicted = [sorted_nums[0], sorted_nums[-1], sorted_nums[4]]

        freq_data = [{"number": n, "count": counter.get(n, 0)} for n in range(10)]

        return {
            "rule": "pick3_frequency",
            "predicted_numbers": predicted,
            "frequency_data": freq_data,
            "strategy": strategy,
            "description": f"近{window}期{'最热' if strategy == 'hot' else '最冷' if strategy == 'cold' else '混合'}3个号码: {predicted}",
        }

    def _rule_pick3_overdue(self, records: list, params: dict) -> dict:
        """遗漏回补：找长期未在任何位置出现的号码"""
        threshold = params.get("threshold", 5)

        last_seen = {n: -1 for n in range(10)}
        for idx, r in enumerate(records):
            for d in r["digits"]:
                last_seen[d] = idx

        total = len(records)
        gaps = []
        for n in range(10):
            gap = total - 1 - last_seen[n] if last_seen[n] >= 0 else total
            gaps.append({"number": n, "gap": gap})

        gaps.sort(key=lambda x: x["gap"], reverse=True)
        predicted = [g["number"] for g in gaps if g["gap"] >= threshold][:3]

        if len(predicted) < 3:
            predicted = [g["number"] for g in gaps[:3]]

        return {
            "rule": "pick3_overdue",
            "predicted_numbers": predicted,
            "gap_data": gaps,
            "threshold": threshold,
            "description": f"遗漏≥{threshold}期的号码: {predicted}",
        }

    def _rule_pick3_neighbor(self, records: list, params: dict) -> dict:
        """邻号跟随：上期号码的±N邻号出现概率高"""
        range_size = params.get("range_size", 1)

        last_digits = set(records[-1]["digits"])
        neighbors = set()
        for d in last_digits:
            for offset in range(-range_size, range_size + 1):
                n = d + offset
                if 0 <= n <= 9:
                    neighbors.add(n)

        all_digits = []
        for r in records[-20:]:
            all_digits.extend(r["digits"])
        counter = Counter(all_digits)

        candidates = sorted(neighbors, key=lambda x: counter.get(x, 0), reverse=True)
        predicted = candidates[:3]

        return {
            "rule": "pick3_neighbor",
            "predicted_numbers": predicted,
            "last_digits": sorted(last_digits),
            "all_neighbors": sorted(neighbors),
            "description": f"上期{sorted(last_digits)}的±{range_size}邻号: {predicted}",
        }

    def _rule_pick3_repeat(self, records: list, params: dict) -> dict:
        """重号策略：上期5个号码中选最可能重复出现的3个"""
        window = params.get("window", 30)
        recent = records[-window:]

        repeat_freq = Counter()
        for i in range(1, len(recent)):
            prev_set = set(recent[i - 1]["digits"])
            curr_set = set(recent[i]["digits"])
            repeats = prev_set & curr_set
            repeat_freq.update(repeats)

        last_digits = records[-1]["digits"]
        last_set = set(last_digits)

        scored = [(n, repeat_freq.get(n, 0)) for n in last_set]
        scored.sort(key=lambda x: x[1], reverse=True)
        predicted = [s[0] for s in scored[:3]]

        if len(predicted) < 3:
            all_counter = Counter()
            for r in recent:
                all_counter.update(r["digits"])
            extras = sorted([n for n in range(10) if n not in predicted],
                          key=lambda x: all_counter.get(x, 0), reverse=True)
            predicted.extend(extras[:3 - len(predicted)])

        avg_repeat_count = sum(
            len(set(recent[i-1]["digits"]) & set(recent[i]["digits"]))
            for i in range(1, len(recent))
        ) / (len(recent) - 1)

        return {
            "rule": "pick3_repeat",
            "predicted_numbers": predicted,
            "last_digits": sorted(last_set),
            "avg_repeat_digits": round(avg_repeat_count, 2),
            "description": f"上期号码{sorted(last_set)}中最可能重复的: {predicted}",
        }

    def _rule_pick3_combo_hot(self, records: list, params: dict) -> dict:
        """热门组合：统计哪3个数字最经常同时出现"""
        window = params.get("window", 100)
        recent = records[-window:]

        combo_counter = Counter()
        for r in recent:
            unique_digits = set(r["digits"])
            for combo in combinations(sorted(unique_digits), 3):
                combo_counter[combo] += 1

        if not combo_counter:
            for r in recent:
                for combo in combinations(sorted(r["digits"]), 3):
                    combo_counter[combo] += 1

        top_combos = combo_counter.most_common(10)
        predicted = list(top_combos[0][0]) if top_combos else [0, 1, 2]

        return {
            "rule": "pick3_combo_hot",
            "predicted_numbers": predicted,
            "top_combinations": [{"combo": list(c), "count": cnt} for c, cnt in top_combos[:10]],
            "description": f"近{window}期最热门组合: {predicted}（出现{top_combos[0][1] if top_combos else 0}次）",
        }

    def _rule_pick3_trend_follow(self, records: list, params: dict) -> dict:
        """趋势跟踪：选近期出现频率持续上升的号码"""
        window = params.get("window", 10)
        recent = records[-window:]

        half = window // 2
        first_half = recent[:half]
        second_half = recent[half:]

        first_counter = Counter()
        for r in first_half:
            first_counter.update(r["digits"])

        second_counter = Counter()
        for r in second_half:
            second_counter.update(r["digits"])

        trend_score = {}
        for n in range(10):
            first_freq = first_counter.get(n, 0) / (half * 5) if half > 0 else 0
            second_freq = second_counter.get(n, 0) / ((window - half) * 5) if (window - half) > 0 else 0
            trend_score[n] = second_freq - first_freq

        sorted_by_trend = sorted(range(10), key=lambda x: trend_score[x], reverse=True)
        predicted = sorted_by_trend[:3]

        trend_data = [{"number": n, "first_half": first_counter.get(n, 0),
                       "second_half": second_counter.get(n, 0),
                       "trend": round(trend_score[n], 4)} for n in range(10)]

        return {
            "rule": "pick3_trend_follow",
            "predicted_numbers": predicted,
            "trend_data": sorted(trend_data, key=lambda x: x["trend"], reverse=True),
            "description": f"近{window}期趋势上升最快: {predicted}",
        }

    def _rule_pick3_odd_even_balance(self, records: list, params: dict) -> dict:
        """奇偶均衡：根据近期奇偶比例选号"""
        window = params.get("window", 20)
        recent = records[-window:]

        all_digits = []
        for r in recent:
            all_digits.extend(r["digits"])
        counter = Counter(all_digits)

        odd_nums = sorted([n for n in range(10) if n % 2 == 1],
                         key=lambda x: counter.get(x, 0), reverse=True)
        even_nums = sorted([n for n in range(10) if n % 2 == 0],
                          key=lambda x: counter.get(x, 0), reverse=True)

        odd_total = sum(counter.get(n, 0) for n in range(10) if n % 2 == 1)
        even_total = sum(counter.get(n, 0) for n in range(10) if n % 2 == 0)

        if odd_total >= even_total:
            predicted = odd_nums[:2] + even_nums[:1]
        else:
            predicted = even_nums[:2] + odd_nums[:1]

        return {
            "rule": "pick3_odd_even_balance",
            "predicted_numbers": predicted,
            "odd_count": odd_total,
            "even_count": even_total,
            "top_odds": odd_nums[:5],
            "top_evens": even_nums[:5],
            "description": f"奇{odd_total}偶{even_total}，选号: {predicted}",
        }

    def _rule_pick3_section(self, records: list, params: dict) -> dict:
        """分区选号：0-9分3区，每区选最热的1个"""
        window = params.get("window", 20)
        recent = records[-window:]

        sections = [(0, 3), (4, 6), (7, 9)]
        section_names = ["低区0-3", "中区4-6", "高区7-9"]

        all_digits = []
        for r in recent:
            all_digits.extend(r["digits"])
        counter = Counter(all_digits)

        predicted = []
        section_details = []
        for (low, high), name in zip(sections, section_names):
            section_nums = list(range(low, high + 1))
            best = max(section_nums, key=lambda x: counter.get(x, 0))
            predicted.append(best)
            section_details.append({
                "section": name,
                "numbers": {n: counter.get(n, 0) for n in section_nums},
                "selected": best,
            })

        return {
            "rule": "pick3_section",
            "predicted_numbers": predicted,
            "section_details": section_details,
            "description": f"三区各选1号: {predicted}",
        }

    def _rule_pick3_gap_pattern(self, records: list, params: dict) -> dict:
        """间距规律：分析号码间距模式"""
        window = params.get("window", 15)
        recent = records[-window:]

        all_digits = []
        for r in recent:
            all_digits.extend(r["digits"])
        counter = Counter(all_digits)

        sorted_nums = sorted(range(10), key=lambda x: counter.get(x, 0), reverse=True)

        last_unique = sorted(set(records[-1]["digits"]))
        if len(last_unique) >= 2:
            avg_gap = np.mean([last_unique[i+1] - last_unique[i] for i in range(len(last_unique)-1)])
        else:
            avg_gap = 3

        base = sorted_nums[0]
        predicted = [base]
        step = max(1, round(avg_gap))
        next_num = (base + step) % 10
        predicted.append(next_num)
        next_num2 = (next_num + step) % 10
        if next_num2 in predicted:
            next_num2 = sorted_nums[1] if sorted_nums[1] not in predicted else sorted_nums[2]
        predicted.append(next_num2)

        predicted = predicted[:3]

        return {
            "rule": "pick3_gap_pattern",
            "predicted_numbers": predicted,
            "avg_gap": round(avg_gap, 1),
            "frequency_data": [{"number": n, "count": counter.get(n, 0)} for n in range(10)],
            "description": f"平均间距{avg_gap:.1f}，选号: {predicted}",
        }
