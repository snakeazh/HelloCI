"""排列五号码分布分析引擎"""
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
        """返回所有可用分析规则"""
        return [
            {
                "id": "position_hot_cold",
                "name": "按位冷热号",
                "description": "分析每个位置近N期的号码出现频率，选出各位最热/最冷的号码作为预测",
                "params": [
                    {"name": "window", "type": "int", "default": 20, "description": "观察窗口期数"},
                    {"name": "strategy", "type": "select", "options": ["hot", "cold", "mixed"], "default": "hot", "description": "策略：热号/冷号/混合"},
                ],
            },
            {
                "id": "position_interval",
                "name": "按位遗漏分析",
                "description": "分析每个位置上各号码的遗漏期数，选出遗漏超过阈值即将回补的号码",
                "params": [
                    {"name": "threshold_ratio", "type": "float", "default": 1.5, "description": "超过平均遗漏的倍数阈值"},
                ],
            },
            {
                "id": "sum_value",
                "name": "和值分析",
                "description": "统计五位数字之和的分布区间，预测下期和值范围并反推可能的号码组合",
                "params": [
                    {"name": "window", "type": "int", "default": 30, "description": "观察窗口期数"},
                    {"name": "bins", "type": "int", "default": 5, "description": "和值区间划分数"},
                ],
            },
            {
                "id": "span",
                "name": "跨度分析",
                "description": "分析五位数字中最大值与最小值之差（跨度）的规律",
                "params": [
                    {"name": "window", "type": "int", "default": 30, "description": "观察窗口期数"},
                ],
            },
            {
                "id": "big_small",
                "name": "大小比分析",
                "description": "分析每期大号(5-9)和小号(0-4)的比例规律，预测下期大小比",
                "params": [
                    {"name": "window", "type": "int", "default": 20, "description": "观察窗口期数"},
                ],
            },
            {
                "id": "odd_even",
                "name": "奇偶比分析",
                "description": "分析每期奇数和偶数的比例分布，预测下期奇偶比及各位号码",
                "params": [
                    {"name": "window", "type": "int", "default": 20, "description": "观察窗口期数"},
                ],
            },
            {
                "id": "same_position_repeat",
                "name": "同位重号分析",
                "description": "分析与上一期同位置重复号码的规律，预测哪些位置可能重号",
                "params": [
                    {"name": "window", "type": "int", "default": 30, "description": "观察窗口期数"},
                ],
            },
            {
                "id": "group_pattern",
                "name": "组选形态分析",
                "description": "分析号码的重复形态（豹子/对子/全不同等）规律",
                "params": [
                    {"name": "window", "type": "int", "default": 50, "description": "观察窗口期数"},
                ],
            },
            {
                "id": "trend",
                "name": "走势分析",
                "description": "分析各位号码的升降走势（上升/下降/持平），预测下期走向",
                "params": [
                    {"name": "window", "type": "int", "default": 10, "description": "观察窗口期数"},
                ],
            },
        ]

    def run_analysis(self, rule: str, params: dict) -> dict:
        """执行单次分析"""
        if not self.history:
            return {"error": "暂无历史数据"}

        method = getattr(self, f"_rule_{rule}", None)
        if method is None:
            return {"error": f"未知的分析规则: {rule}"}

        return method(self.history, params)

    def backtest(self, rule: str, params: dict, test_periods: int = 50) -> dict:
        """回测验证：逐期验证预测结果"""
        if len(self.history) < test_periods + 20:
            return {"error": f"历史数据不足，需要至少 {test_periods + 20} 期数据"}

        method = getattr(self, f"_rule_{rule}", None)
        if method is None:
            return {"error": f"未知的分析规则: {rule}"}

        results = []
        total_position_hits = 0
        total_positions = 0
        exact_hits = 0

        for i in range(test_periods):
            end_idx = len(self.history) - test_periods + i
            train_data = self.history[:end_idx]
            actual = self.history[end_idx]

            prediction = method(train_data, params)
            if "error" in prediction:
                continue

            predicted_positions = prediction.get("predicted_positions", [])
            actual_digits = actual["digits"]

            position_hits = []
            period_hit_count = 0
            for pos_pred in predicted_positions:
                pos = pos_pred["position"]
                pred_nums = pos_pred["numbers"]
                actual_num = actual_digits[pos]
                hit = actual_num in pred_nums
                if hit:
                    period_hit_count += 1
                position_hits.append({
                    "position": pos,
                    "predicted": pred_nums,
                    "actual": actual_num,
                    "hit": hit,
                })

            total_position_hits += period_hit_count
            total_positions += len(predicted_positions)
            if period_hit_count == 5:
                exact_hits += 1

            results.append({
                "period": actual.get("period", f"第{end_idx+1}期"),
                "actual_digits": actual_digits,
                "position_hits": position_hits,
                "hit_count": period_hit_count,
                "hit_all": period_hit_count == 5,
            })

        position_accuracy = total_position_hits / total_positions if total_positions > 0 else 0
        avg_hit = total_position_hits / len(results) if results else 0
        periods_with_any_hit = sum(1 for r in results if r["hit_count"] > 0)

        per_position_stats = [0] * 5
        for r in results:
            for ph in r["position_hits"]:
                if ph["hit"]:
                    per_position_stats[ph["position"]] += 1

        return {
            "rule": rule,
            "params": params,
            "test_periods": len(results),
            "position_accuracy": round(position_accuracy, 4),
            "position_accuracy_pct": f"{position_accuracy*100:.1f}%",
            "avg_hit_positions": round(avg_hit, 2),
            "periods_with_any_hit": periods_with_any_hit,
            "any_hit_pct": f"{periods_with_any_hit/len(results)*100:.1f}%" if results else "0%",
            "exact_hits": exact_hits,
            "per_position_accuracy": [
                {"position": i, "name": POSITION_NAMES[i],
                 "hits": per_position_stats[i],
                 "accuracy": f"{per_position_stats[i]/len(results)*100:.1f}%" if results else "0%"}
                for i in range(5)
            ],
            "details": results,
        }

    # ========== 排列五专用分析规则 ==========

    def _rule_position_hot_cold(self, records: list, params: dict) -> dict:
        """按位冷热号分析"""
        window = params.get("window", 20)
        strategy = params.get("strategy", "hot")
        recent = records[-window:]

        predicted_positions = []
        position_details = []

        for pos in range(5):
            numbers = [r["digits"][pos] for r in recent]
            counter = Counter(numbers)
            sorted_nums = sorted(range(10), key=lambda x: counter.get(x, 0), reverse=True)

            if strategy == "hot":
                predicted = sorted_nums[:3]
            elif strategy == "cold":
                predicted = sorted_nums[-3:]
            else:
                predicted = sorted_nums[:2] + sorted_nums[-1:]

            predicted_positions.append({"position": pos, "numbers": predicted})
            position_details.append({
                "position": pos,
                "name": POSITION_NAMES[pos],
                "frequency": [{"number": n, "count": counter.get(n, 0)} for n in range(10)],
                "predicted": predicted,
            })

        return {
            "rule": "position_hot_cold",
            "strategy": strategy,
            "window": window,
            "predicted_positions": predicted_positions,
            "position_details": position_details,
            "description": f"基于近{window}期各位{'热号' if strategy == 'hot' else '冷号' if strategy == 'cold' else '混合'}分析",
        }

    def _rule_position_interval(self, records: list, params: dict) -> dict:
        """按位遗漏分析"""
        threshold_ratio = params.get("threshold_ratio", 1.5)

        predicted_positions = []
        position_details = []

        for pos in range(5):
            last_seen = {}
            intervals = {n: [] for n in range(10)}

            for idx, r in enumerate(records):
                n = r["digits"][pos]
                if n in last_seen:
                    intervals[n].append(idx - last_seen[n])
                last_seen[n] = idx

            total = len(records)
            overdue = []
            for n in range(10):
                current_gap = total - last_seen.get(n, 0)
                avg_iv = np.mean(intervals[n]) if intervals[n] else total
                ratio = current_gap / avg_iv if avg_iv > 0 else 0
                overdue.append({
                    "number": n,
                    "current_gap": current_gap,
                    "avg_interval": round(avg_iv, 1),
                    "ratio": round(ratio, 2),
                })

            overdue.sort(key=lambda x: x["ratio"], reverse=True)
            predicted = [item["number"] for item in overdue if item["ratio"] >= threshold_ratio][:3]
            if not predicted:
                predicted = [overdue[0]["number"]]

            predicted_positions.append({"position": pos, "numbers": predicted})
            position_details.append({
                "position": pos,
                "name": POSITION_NAMES[pos],
                "overdue_data": overdue,
                "predicted": predicted,
            })

        return {
            "rule": "position_interval",
            "threshold_ratio": threshold_ratio,
            "predicted_positions": predicted_positions,
            "position_details": position_details,
            "description": f"各位遗漏超{threshold_ratio}倍平均值的号码",
        }

    def _rule_sum_value(self, records: list, params: dict) -> dict:
        """和值分析"""
        window = params.get("window", 30)
        bins = params.get("bins", 5)
        recent = records[-window:]

        sums = [sum(r["digits"]) for r in recent]
        all_sums = [sum(r["digits"]) for r in records]

        avg_sum = np.mean(sums)
        std_sum = np.std(sums)

        min_s, max_s = 0, 45
        bin_size = (max_s - min_s + 1) / bins
        bin_counts = [0] * bins
        for s in all_sums:
            idx = min(int((s - min_s) / bin_size), bins - 1)
            bin_counts[idx] += 1

        predicted_sum_low = max(0, int(avg_sum - std_sum))
        predicted_sum_high = min(45, int(avg_sum + std_sum))

        target_sum = round(avg_sum)
        predicted_positions = []
        avg_per_pos = target_sum / 5
        for pos in range(5):
            numbers = [r["digits"][pos] for r in recent]
            counter = Counter(numbers)
            candidates = sorted(range(10), key=lambda x: counter.get(x, 0), reverse=True)
            near_avg = sorted(candidates[:5], key=lambda x: abs(x - avg_per_pos))[:3]
            predicted_positions.append({"position": pos, "numbers": near_avg})

        bin_data = []
        for i in range(bins):
            low = int(min_s + i * bin_size)
            high = int(min_s + (i + 1) * bin_size) - 1
            bin_data.append({
                "range": f"{low}-{high}",
                "count": bin_counts[i],
                "frequency": round(bin_counts[i] / len(all_sums), 4),
            })

        return {
            "rule": "sum_value",
            "predicted_positions": predicted_positions,
            "predicted_sum_range": [predicted_sum_low, predicted_sum_high],
            "recent_avg_sum": round(avg_sum, 1),
            "recent_std": round(std_sum, 1),
            "sum_distribution": bin_data,
            "recent_sums": sums[-10:],
            "description": f"预测和值范围 {predicted_sum_low}-{predicted_sum_high}（近{window}期均值{avg_sum:.0f}）",
        }

    def _rule_span(self, records: list, params: dict) -> dict:
        """跨度分析"""
        window = params.get("window", 30)
        recent = records[-window:]

        spans = [max(r["digits"]) - min(r["digits"]) for r in recent]
        all_spans = [max(r["digits"]) - min(r["digits"]) for r in records]

        avg_span = np.mean(spans)
        span_counter = Counter(all_spans)

        most_common_span = span_counter.most_common(5)
        predicted_span = round(avg_span)

        predicted_positions = []
        for pos in range(5):
            numbers = [r["digits"][pos] for r in recent]
            counter = Counter(numbers)
            predicted = sorted(range(10), key=lambda x: counter.get(x, 0), reverse=True)[:3]
            predicted_positions.append({"position": pos, "numbers": predicted})

        return {
            "rule": "span",
            "predicted_positions": predicted_positions,
            "predicted_span": predicted_span,
            "avg_span": round(avg_span, 1),
            "span_distribution": [{"span": s, "count": c} for s, c in sorted(span_counter.items())],
            "most_common_spans": [{"span": s, "count": c} for s, c in most_common_span],
            "recent_spans": spans[-10:],
            "description": f"预测跨度 {predicted_span}（近{window}期平均{avg_span:.1f}）",
        }

    def _rule_big_small(self, records: list, params: dict) -> dict:
        """大小比分析 (0-4小, 5-9大)"""
        window = params.get("window", 20)
        recent = records[-window:]

        ratios = []
        for r in recent:
            big_count = sum(1 for d in r["digits"] if d >= 5)
            ratios.append(big_count)

        avg_big = np.mean(ratios)
        predicted_big = round(avg_big)
        predicted_small = 5 - predicted_big

        ratio_dist = Counter([f"{b}:{5-b}" for b in ratios])

        predicted_positions = []
        for pos in range(5):
            numbers = [r["digits"][pos] for r in recent]
            counter = Counter(numbers)
            big_nums = sorted([n for n in range(5, 10)], key=lambda x: counter.get(x, 0), reverse=True)
            small_nums = sorted([n for n in range(0, 5)], key=lambda x: counter.get(x, 0), reverse=True)

            if pos < predicted_big:
                predicted = big_nums[:3]
            else:
                predicted = small_nums[:3]
            predicted_positions.append({"position": pos, "numbers": predicted})

        return {
            "rule": "big_small",
            "predicted_positions": predicted_positions,
            "predicted_ratio": f"{predicted_big}:{predicted_small}",
            "avg_big_count": round(avg_big, 2),
            "ratio_distribution": dict(ratio_dist),
            "description": f"预测大小比 {predicted_big}大{predicted_small}小",
        }

    def _rule_odd_even(self, records: list, params: dict) -> dict:
        """奇偶比分析"""
        window = params.get("window", 20)
        recent = records[-window:]

        ratios = []
        for r in recent:
            odd_count = sum(1 for d in r["digits"] if d % 2 == 1)
            ratios.append(odd_count)

        avg_odd = np.mean(ratios)
        predicted_odd = round(avg_odd)
        predicted_even = 5 - predicted_odd

        ratio_dist = Counter([f"{o}:{5-o}" for o in ratios])

        predicted_positions = []
        for pos in range(5):
            numbers = [r["digits"][pos] for r in recent]
            counter = Counter(numbers)
            odd_nums = sorted([n for n in range(10) if n % 2 == 1], key=lambda x: counter.get(x, 0), reverse=True)
            even_nums = sorted([n for n in range(10) if n % 2 == 0], key=lambda x: counter.get(x, 0), reverse=True)

            if pos < predicted_odd:
                predicted = odd_nums[:3]
            else:
                predicted = even_nums[:3]
            predicted_positions.append({"position": pos, "numbers": predicted})

        return {
            "rule": "odd_even",
            "predicted_positions": predicted_positions,
            "predicted_ratio": f"{predicted_odd}:{predicted_even}",
            "avg_odd_count": round(avg_odd, 2),
            "ratio_distribution": dict(ratio_dist),
            "description": f"预测奇偶比 {predicted_odd}奇{predicted_even}偶",
        }

    def _rule_same_position_repeat(self, records: list, params: dict) -> dict:
        """同位重号分析"""
        window = params.get("window", 30)
        recent = records[-window:] if len(records) >= window else records

        repeat_stats = []
        for i in range(1, len(recent)):
            prev = recent[i - 1]["digits"]
            curr = recent[i]["digits"]
            repeats = [pos for pos in range(5) if prev[pos] == curr[pos]]
            repeat_stats.append({
                "period": recent[i].get("period", ""),
                "repeat_positions": repeats,
                "repeat_count": len(repeats),
            })

        avg_repeat = np.mean([s["repeat_count"] for s in repeat_stats]) if repeat_stats else 0

        pos_repeat_freq = [0] * 5
        for s in repeat_stats:
            for pos in s["repeat_positions"]:
                pos_repeat_freq[pos] += 1

        pos_repeat_rate = [f / len(repeat_stats) if repeat_stats else 0 for f in pos_repeat_freq]

        last_digits = records[-1]["digits"]
        predicted_positions = []
        for pos in range(5):
            if pos_repeat_rate[pos] > 0.3:
                predicted = [last_digits[pos]]
                numbers = [r["digits"][pos] for r in recent]
                counter = Counter(numbers)
                extras = sorted([n for n in range(10) if n != last_digits[pos]],
                               key=lambda x: counter.get(x, 0), reverse=True)[:2]
                predicted.extend(extras)
            else:
                numbers = [r["digits"][pos] for r in recent]
                counter = Counter(numbers)
                predicted = sorted(range(10), key=lambda x: counter.get(x, 0), reverse=True)[:3]
            predicted_positions.append({"position": pos, "numbers": predicted})

        repeat_count_dist = Counter([s["repeat_count"] for s in repeat_stats])

        return {
            "rule": "same_position_repeat",
            "predicted_positions": predicted_positions,
            "avg_repeat_count": round(avg_repeat, 2),
            "last_digits": last_digits,
            "per_position_repeat_rate": [
                {"position": i, "name": POSITION_NAMES[i], "rate": f"{pos_repeat_rate[i]*100:.1f}%"}
                for i in range(5)
            ],
            "repeat_count_distribution": dict(sorted(repeat_count_dist.items())),
            "description": f"平均每期有{avg_repeat:.1f}个同位重号",
        }

    def _rule_group_pattern(self, records: list, params: dict) -> dict:
        """组选形态分析"""
        window = params.get("window", 50)
        recent = records[-window:]

        def get_pattern(digits):
            unique_count = len(set(digits))
            counter = Counter(digits)
            max_repeat = max(counter.values())
            if unique_count == 1:
                return "五同"
            elif max_repeat == 4:
                return "四同"
            elif max_repeat == 3 and unique_count == 2:
                return "三同+对"
            elif max_repeat == 3:
                return "三同"
            elif unique_count == 3 and max_repeat == 2:
                return "双对"
            elif max_repeat == 2 and unique_count == 4:
                return "一对"
            else:
                return "全不同"

        patterns = [get_pattern(r["digits"]) for r in recent]
        pattern_dist = Counter(patterns)

        most_common = pattern_dist.most_common(1)[0][0] if pattern_dist else "全不同"

        predicted_positions = []
        for pos in range(5):
            numbers = [r["digits"][pos] for r in recent]
            counter = Counter(numbers)
            predicted = sorted(range(10), key=lambda x: counter.get(x, 0), reverse=True)[:3]
            predicted_positions.append({"position": pos, "numbers": predicted})

        return {
            "rule": "group_pattern",
            "predicted_positions": predicted_positions,
            "predicted_pattern": most_common,
            "pattern_distribution": dict(pattern_dist.most_common()),
            "recent_patterns": patterns[-10:],
            "description": f"最常见形态: {most_common}（占比{pattern_dist[most_common]/len(patterns)*100:.0f}%）",
        }

    def _rule_trend(self, records: list, params: dict) -> dict:
        """走势分析（升/降/平）"""
        window = params.get("window", 10)
        recent = records[-window:]

        position_trends = []
        predicted_positions = []

        for pos in range(5):
            values = [r["digits"][pos] for r in recent]
            ups = sum(1 for i in range(1, len(values)) if values[i] > values[i-1])
            downs = sum(1 for i in range(1, len(values)) if values[i] < values[i-1])
            flats = sum(1 for i in range(1, len(values)) if values[i] == values[i-1])

            total_moves = len(values) - 1
            last_val = values[-1]

            if ups > downs:
                trend = "上升"
                candidates = [n for n in range(last_val, 10)]
                if not candidates:
                    candidates = list(range(7, 10))
            elif downs > ups:
                trend = "下降"
                candidates = [n for n in range(0, last_val + 1)]
                if not candidates:
                    candidates = list(range(0, 3))
            else:
                trend = "持平"
                candidates = [last_val, max(0, last_val - 1), min(9, last_val + 1)]

            counter = Counter([r["digits"][pos] for r in recent])
            predicted = sorted(candidates, key=lambda x: counter.get(x, 0), reverse=True)[:3]

            predicted_positions.append({"position": pos, "numbers": predicted})
            position_trends.append({
                "position": pos,
                "name": POSITION_NAMES[pos],
                "trend": trend,
                "ups": ups,
                "downs": downs,
                "flats": flats,
                "last_value": last_val,
                "values": values,
            })

        return {
            "rule": "trend",
            "predicted_positions": predicted_positions,
            "position_trends": position_trends,
            "description": "各位走势: " + " ".join(f"{POSITION_NAMES[i]}{'↑' if t['trend']=='上升' else '↓' if t['trend']=='下降' else '→'}" for i, t in enumerate(position_trends)),
        }
