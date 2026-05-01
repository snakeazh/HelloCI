"""排列五号码分布分析工具 - 主应用"""
from flask import Flask, render_template, request, jsonify
from analyzer import LotteryAnalyzer

app = Flask(__name__)
analyzer = LotteryAnalyzer()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/history", methods=["GET"])
def get_history():
    """获取历史数据"""
    return jsonify(analyzer.get_history())


@app.route("/api/upload_history", methods=["POST"])
def upload_history():
    """上传历史数据"""
    data = request.json
    records = data.get("records", [])
    result = analyzer.add_history(records)
    return jsonify(result)


@app.route("/api/distribution", methods=["GET"])
def get_distribution():
    """获取号码分布统计，支持按位查询"""
    position = request.args.get("position", "-1", type=int)
    data = analyzer.get_distribution(position)
    return jsonify(data)


@app.route("/api/analyze", methods=["POST"])
def analyze():
    """执行自定义分析规则"""
    data = request.json
    rule = data.get("rule")
    params = data.get("params", {})
    result = analyzer.run_analysis(rule, params)
    return jsonify(result)


@app.route("/api/backtest", methods=["POST"])
def backtest():
    """回测验证分析思路的正确率"""
    data = request.json
    rule = data.get("rule")
    params = data.get("params", {})
    test_periods = data.get("test_periods", 50)
    result = analyzer.backtest(rule, params, test_periods)
    return jsonify(result)


@app.route("/api/rules", methods=["GET"])
def get_rules():
    """获取所有可用的分析规则"""
    return jsonify(analyzer.get_available_rules())


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
