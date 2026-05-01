let distributionChart = null;
let currentRules = [];

document.addEventListener("DOMContentLoaded", () => {
    loadRules();
    loadDataCount();
    loadDistribution("red");

    document.getElementById("lottery-type").addEventListener("change", () => {
        loadDataCount();
        loadDistribution("red");
    });

    document.getElementById("rule-select").addEventListener("change", onRuleChange);
    document.getElementById("btn-analyze").addEventListener("click", runAnalysis);
    document.getElementById("btn-backtest").addEventListener("click", runBacktest);

    document.querySelectorAll(".tab").forEach(tab => {
        tab.addEventListener("click", () => switchTab(tab.dataset.tab));
    });
});

function switchTab(tabName) {
    document.querySelectorAll(".tab").forEach(t => t.classList.remove("active"));
    document.querySelectorAll(".tab-content").forEach(t => t.classList.remove("active"));
    document.querySelector(`.tab[data-tab="${tabName}"]`).classList.add("active");
    document.getElementById(`tab-${tabName}`).classList.add("active");
}

async function loadRules() {
    const resp = await fetch("/api/rules");
    currentRules = await resp.json();
    const select = document.getElementById("rule-select");
    currentRules.forEach(rule => {
        const opt = document.createElement("option");
        opt.value = rule.id;
        opt.textContent = rule.name;
        select.appendChild(opt);
    });
}

async function loadDataCount() {
    const type = document.getElementById("lottery-type").value;
    const resp = await fetch(`/api/history/${type}`);
    const data = await resp.json();
    document.getElementById("data-count").textContent = `${data.count} 期数据`;
}

async function loadDistribution(zone) {
    const type = document.getElementById("lottery-type").value;
    const resp = await fetch(`/api/distribution/${type}?zone=${zone}`);
    const data = await resp.json();

    if (data.error) {
        return;
    }

    const labels = data.distribution.map(d => d.number);
    const counts = data.distribution.map(d => d.count);
    const avgCount = counts.reduce((a, b) => a + b, 0) / counts.length;

    const colors = counts.map(c =>
        c > avgCount * 1.3 ? (zone === "red" ? "rgba(229, 57, 53, 0.8)" : "rgba(21, 101, 192, 0.8)") :
        c < avgCount * 0.7 ? "rgba(136, 146, 176, 0.5)" :
        (zone === "red" ? "rgba(229, 57, 53, 0.5)" : "rgba(21, 101, 192, 0.5)")
    );

    const ctx = document.getElementById("distribution-chart").getContext("2d");

    if (distributionChart) {
        distributionChart.destroy();
    }

    distributionChart = new Chart(ctx, {
        type: "bar",
        data: {
            labels: labels,
            datasets: [{
                label: `${zone === "red" ? "红球" : "蓝球"}出现次数`,
                data: counts,
                backgroundColor: colors,
                borderColor: colors.map(c => c.replace("0.5", "1").replace("0.8", "1")),
                borderWidth: 1,
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { labels: { color: "#8892b0" } },
                annotation: {
                    annotations: {
                        line1: {
                            type: "line",
                            yMin: avgCount,
                            yMax: avgCount,
                            borderColor: "rgba(100, 255, 218, 0.5)",
                            borderWidth: 1,
                            borderDash: [5, 5],
                        }
                    }
                }
            },
            scales: {
                x: { ticks: { color: "#8892b0" }, grid: { color: "rgba(255,255,255,0.05)" } },
                y: { ticks: { color: "#8892b0" }, grid: { color: "rgba(255,255,255,0.05)" } }
            }
        }
    });

    switchTab("distribution");
}

function onRuleChange() {
    const ruleId = document.getElementById("rule-select").value;
    const rule = currentRules.find(r => r.id === ruleId);

    const descEl = document.getElementById("rule-description");
    const paramsEl = document.getElementById("rule-params");

    if (!rule) {
        descEl.textContent = "";
        paramsEl.innerHTML = "";
        return;
    }

    descEl.textContent = rule.description;
    paramsEl.innerHTML = "";

    rule.params.forEach(param => {
        const group = document.createElement("div");
        group.className = "form-group";

        const label = document.createElement("label");
        label.textContent = param.description;
        group.appendChild(label);

        let input;
        if (param.type === "select") {
            input = document.createElement("select");
            param.options.forEach(opt => {
                const option = document.createElement("option");
                option.value = opt;
                option.textContent = opt;
                if (opt === param.default) option.selected = true;
                input.appendChild(option);
            });
        } else {
            input = document.createElement("input");
            input.type = "number";
            input.value = param.default;
            if (param.type === "float") input.step = "0.1";
        }

        input.id = `param-${param.name}`;
        input.className = "param-input";
        group.appendChild(input);
        paramsEl.appendChild(group);
    });
}

function getParams() {
    const ruleId = document.getElementById("rule-select").value;
    const rule = currentRules.find(r => r.id === ruleId);
    if (!rule) return {};

    const params = {};
    rule.params.forEach(param => {
        const el = document.getElementById(`param-${param.name}`);
        if (el) {
            if (param.type === "int") params[param.name] = parseInt(el.value);
            else if (param.type === "float") params[param.name] = parseFloat(el.value);
            else params[param.name] = el.value;
        }
    });
    return params;
}

async function runAnalysis() {
    const type = document.getElementById("lottery-type").value;
    const rule = document.getElementById("rule-select").value;

    if (!rule) {
        alert("请先选择分析规则");
        return;
    }

    const params = getParams();
    const resp = await fetch("/api/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ lottery_type: type, rule: rule, params: params })
    });

    const result = await resp.json();
    displayAnalysisResult(result);
    switchTab("analysis");
}

function displayAnalysisResult(result) {
    const container = document.getElementById("analysis-result");

    if (result.error) {
        container.innerHTML = `<p class="placeholder">${result.error}</p>`;
        return;
    }

    const zone = result.zone || "red";
    let html = `<div class="result-card">
        <h4>${result.description || "分析结果"}</h4>
        <p style="color:#8892b0;margin-bottom:12px;">预测号码：</p>
        <div class="numbers-display">`;

    (result.predicted_numbers || []).forEach(n => {
        html += `<div class="number-ball ${zone}">${n}</div>`;
    });

    html += `</div></div>`;

    if (result.frequency_data) {
        html += `<div class="result-card"><h4>频率详情</h4><div class="stat-grid">`;
        const sorted = [...result.frequency_data].sort((a, b) => b.count - a.count).slice(0, 10);
        sorted.forEach(item => {
            html += `<div class="stat-item"><div class="value">${item.number}</div><div class="label">${item.count}次</div></div>`;
        });
        html += `</div></div>`;
    }

    if (result.overdue_numbers && result.overdue_numbers.length > 0) {
        html += `<div class="result-card"><h4>逾期号码</h4><table class="backtest-table">
            <tr><th>号码</th><th>当前间隔</th><th>平均间隔</th><th>倍率</th></tr>`;
        result.overdue_numbers.slice(0, 10).forEach(item => {
            html += `<tr><td>${item.number}</td><td>${item.current_gap}</td><td>${item.avg_interval}</td><td>${item.ratio}x</td></tr>`;
        });
        html += `</table></div>`;
    }

    if (result.zone_data) {
        html += `<div class="result-card"><h4>区间分布</h4><table class="backtest-table">
            <tr><th>区间</th><th>出现次数</th><th>比例</th><th>预测个数</th></tr>`;
        result.zone_data.forEach(item => {
            html += `<tr><td>${item.zone}</td><td>${item.count}</td><td>${(item.ratio * 100).toFixed(1)}%</td><td>${item.predicted_count}</td></tr>`;
        });
        html += `</table></div>`;
    }

    if (result.ratio_distribution) {
        html += `<div class="result-card"><h4>奇偶比分布</h4><div class="stat-grid">`;
        Object.entries(result.ratio_distribution).forEach(([ratio, count]) => {
            html += `<div class="stat-item"><div class="value">${ratio}</div><div class="label">${count}次</div></div>`;
        });
        html += `</div></div>`;
    }

    if (result.repeat_distribution) {
        html += `<div class="result-card"><h4>重号个数分布</h4><div class="stat-grid">`;
        Object.entries(result.repeat_distribution).forEach(([count, freq]) => {
            html += `<div class="stat-item"><div class="value">${count}个</div><div class="label">${freq}次</div></div>`;
        });
        html += `</div></div>`;
    }

    container.innerHTML = html;
}

async function runBacktest() {
    const type = document.getElementById("lottery-type").value;
    const rule = document.getElementById("rule-select").value;

    if (!rule) {
        alert("请先选择分析规则");
        return;
    }

    const params = getParams();
    const testPeriods = parseInt(document.getElementById("test-periods").value);

    const container = document.getElementById("backtest-result");
    container.innerHTML = `<p class="loading">⏳ 正在回测 ${testPeriods} 期数据...</p>`;
    switchTab("backtest");

    const resp = await fetch("/api/backtest", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ lottery_type: type, rule: rule, params: params, test_periods: testPeriods })
    });

    const result = await resp.json();
    displayBacktestResult(result);
}

function displayBacktestResult(result) {
    const container = document.getElementById("backtest-result");

    if (result.error) {
        container.innerHTML = `<p class="placeholder">${result.error}</p>`;
        return;
    }

    const accuracy = result.accuracy;
    const colorClass = accuracy >= 0.7 ? "high" : accuracy >= 0.4 ? "medium" : "low";

    let html = `
        <div class="result-card">
            <h4>回测结果总览</h4>
            <div class="accuracy-display ${colorClass}">${result.accuracy_pct}</div>
            <p style="text-align:center;color:#8892b0;">命中正确率（至少命中1个号码）</p>
            <div class="stat-grid">
                <div class="stat-item"><div class="value">${result.test_periods}</div><div class="label">测试期数</div></div>
                <div class="stat-item"><div class="value">${result.hits}</div><div class="label">命中期数</div></div>
                <div class="stat-item"><div class="value">${result.avg_hit_count}</div><div class="label">平均命中个数</div></div>
            </div>
        </div>
        <div class="result-card">
            <h4>逐期回测详情</h4>
            <table class="backtest-table">
                <tr><th>期号</th><th>预测号码</th><th>开奖号码</th><th>命中</th></tr>`;

    result.details.slice(0, 30).forEach(d => {
        const hitClass = d.hit ? "hit" : "";
        const predictedHtml = d.predicted.map(n =>
            d.hit_numbers.includes(n) ? `<span style="color:#ffd700;font-weight:700">${n}</span>` : n
        ).join(", ");

        html += `<tr class="${hitClass}">
            <td>${d.period}</td>
            <td>${predictedHtml}</td>
            <td>${d.actual.join(", ")}</td>
            <td>${d.hit ? `✅ ${d.hit_count}个` : "❌"}</td>
        </tr>`;
    });

    if (result.details.length > 30) {
        html += `<tr><td colspan="4" style="text-align:center;color:#8892b0">... 还有 ${result.details.length - 30} 期 ...</td></tr>`;
    }

    html += `</table></div>`;
    container.innerHTML = html;
}
