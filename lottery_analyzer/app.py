"""彩票号码分布分析工具 - 主应用"""
import json
from flask import Flask, render_template, request, jsonify
from analyzer import LotteryAnalyzer

app = Flask(__name__)
analyzer = LotteryAnalyzer()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/lottery_types", methods=["GET"])
def get_lottery_types():
    """获取支持的彩票类型"""
    return jsonify(analyzer.get_lottery_types())


@app.route("/api/history/<lottery_type>", methods=["GET"])
def get_history(lottery_type):
    """获取历史数据"""
    data = analyzer.get_history(lottery_type)
    return jsonify(data)


@app.route("/api/upload_history", methods=["POST"])
def upload_history():
    """上传历史数据"""
    data = request.json
    lottery_type = data.get("lottery_type")
    records = data.get("records", [])
    result = analyzer.add_history(lottery_type, records)
    return jsonify(result)


@app.route("/api/distribution/<lottery_type>", methods=["GET"])
def get_distribution(lottery_type):
    """获取号码分布统计"""
    zone = request.args.get("zone", "red")
    data = analyzer.get_distribution(lottery_type, zone)
    return jsonify(data)


@app.route("/api/analyze", methods=["POST"])
def analyze():
    """执行自定义分析规则"""
    data = request.json
    lottery_type = data.get("lottery_type")
    rule = data.get("rule")
    params = data.get("params", {})
    result = analyzer.run_analysis(lottery_type, rule, params)
    return jsonify(result)


@app.route("/api/backtest", methods=["POST"])
def backtest():
    """回测验证分析思路的正确率"""
    data = request.json
    lottery_type = data.get("lottery_type")
    rule = data.get("rule")
    params = data.get("params", {})
    test_periods = data.get("test_periods", 50)
    result = analyzer.backtest(lottery_type, rule, params, test_periods)
    return jsonify(result)


@app.route("/api/rules", methods=["GET"])
def get_rules():
    """获取所有可用的分析规则"""
    return jsonify(analyzer.get_available_rules())


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
