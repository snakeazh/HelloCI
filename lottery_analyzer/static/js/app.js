const POSITION_NAMES = ["万位", "千位", "百位", "十位", "个位"];
const POSITION_COLORS = [
    "rgba(229, 57, 53, 0.7)",
    "rgba(255, 152, 0, 0.7)",
    "rgba(76, 175, 80, 0.7)",
    "rgba(33, 150, 243, 0.7)",
    "rgba(156, 39, 176, 0.7)",
];

let distributionChart = null;
let currentRules = [];

document.addEventListener("DOMContentLoaded", () => {
    loadRules();
    loadDataCount();
    loadDistribution(-1);

    document.getElementById("rule-select").addEventListener("change", onRuleChange);
    document.getElementById("btn-analyze").addEventListener("click", runAnalysis);
    document.getElementById("btn-backtest").addEventListener("click", runBacktest);

    document.querySelectorAll(".tab").forEach(tab => {
        tab.addEventListener("click", () => switchTab(tab.dataset.tab));
    });

    document.querySelectorAll(".pos-btn").forEach(btn => {
        btn.addEventListener("click", () => {
            document.querySelectorAll(".pos-btn").forEach(b => b.classList.remove("active"));
            btn.classList.add("active");
            loadDistribution(parseInt(btn.dataset.pos));
        });
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
    const resp = await fetch("/api/history");
    const data = await resp.json();
    document.getElementById("data-count").textContent = `${data.count} 期数据`;
}

async function loadDistribution(position) {
    const resp = await fetch(`/api/distribution?position=${position}`);
    const data = await resp.json();

    if (data.error) return;

    const ctx = document.getElementById("distribution-chart").getContext("2d");
    if (distributionChart) distributionChart.destroy();

    if (position === -1 && data.positions) {
        const datasets = data.positions.map((pos, idx) => ({
            label: pos.name,
            data: pos.distribution.map(d => d.count),
            backgroundColor: POSITION_COLORS[idx],
            borderColor: POSITION_COLORS[idx].replace("0.7", "1"),
            borderWidth: 1,
        }));

        distributionChart = new Chart(ctx, {
            type: "bar",
            data: { labels: [0,1,2,3,4,5,6,7,8,9], datasets },
            options: {
                responsive: true,
                plugins: { legend: { labels: { color: "#8892b0" } } },
                scales: {
                    x: { ticks: { color: "#8892b0" }, grid: { color: "rgba(255,255,255,0.05)" } },
                    y: { ticks: { color: "#8892b0" }, grid: { color: "rgba(255,255,255,0.05)" } }
                }
            }
        });
    } else {
        const dist = data.distribution;
        const counts = dist.map(d => d.count);
        const avgCount = counts.reduce((a, b) => a + b, 0) / counts.length;
        const colors = counts.map(c =>
            c > avgCount * 1.2 ? "rgba(100, 255, 218, 0.8)" :
            c < avgCount * 0.8 ? "rgba(136, 146, 176, 0.5)" :
            "rgba(100, 255, 218, 0.4)"
        );

        distributionChart = new Chart(ctx, {
            type: "bar",
            data: {
                labels: [0,1,2,3,4,5,6,7,8,9],
                datasets: [{
                    label: `${data.name || "全部"}出现次数`,
                    data: counts,
                    backgroundColor: colors,
                    borderColor: colors.map(c => c.replace("0.4", "1").replace("0.5", "1").replace("0.8", "1")),
                    borderWidth: 1,
                }]
            },
            options: {
                responsive: true,
                plugins: { legend: { labels: { color: "#8892b0" } } },
                scales: {
                    x: { ticks: { color: "#8892b0" }, grid: { color: "rgba(255,255,255,0.05)" } },
                    y: { ticks: { color: "#8892b0" }, grid: { color: "rgba(255,255,255,0.05)" } }
                }
            }
        });
    }
}

function onRuleChange() {
    const ruleId = document.getElementById("rule-select").value;
    const rule = currentRules.find(r => r.id === ruleId);

    const descEl = document.getElementById("rule-description");
    const paramsEl = document.getElementById("rule-params");

    if (!rule) { descEl.textContent = ""; paramsEl.innerHTML = ""; return; }

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
    const rule = document.getElementById("rule-select").value;
    if (!rule) { alert("请先选择分析规则"); return; }

    const params = getParams();
    const resp = await fetch("/api/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ rule, params })
    });

    const result = await resp.json();
    displayAnalysisResult(result);
    switchTab("analysis");
}

function displayAnalysisResult(result) {
    const container = document.getElementById("analysis-result");
    if (result.error) { container.innerHTML = `<p class="placeholder">${result.error}</p>`; return; }

    let html = `<div class="result-card">
        <h4>${result.description || "分析结果"}</h4>
        <p style="color:#8892b0;margin-bottom:8px;">各位预测号码：</p>
        <div class="position-prediction">`;

    if (result.predicted_positions) {
        result.predicted_positions.forEach((pos, idx) => {
            html += `<div class="position-card">
                <div class="pos-name">${POSITION_NAMES[idx]}</div>
                <div class="numbers">
                    ${pos.numbers.map(n => `<div class="digit-ball">${n}</div>`).join("")}
                </div>
            </div>`;
        });
    }
    html += `</div></div>`;

    if (result.position_details) {
        html += `<div class="result-card"><h4>各位详细频率</h4>`;
        result.position_details.forEach(detail => {
            if (detail.frequency) {
                html += `<p style="color:#8892b0;font-size:0.85rem;margin:8px 0 4px;">${detail.name}：`;
                const sorted = [...detail.frequency].sort((a, b) => b.count - a.count);
                html += sorted.map(f => `${f.number}<small>(${f.count})</small>`).join(" ");
                html += `</p>`;
            }
        });
        html += `</div>`;
    }

    if (result.position_trends) {
        html += `<div class="result-card"><h4>走势详情</h4><div class="position-prediction">`;
        result.position_trends.forEach(t => {
            const icon = t.trend === "上升" ? "↑" : t.trend === "下降" ? "↓" : "→";
            const cls = t.trend === "上升" ? "trend-up" : t.trend === "下降" ? "trend-down" : "trend-flat";
            html += `<div class="position-card">
                <div class="pos-name">${t.name}</div>
                <div class="trend-indicator ${cls}">${icon} ${t.trend}</div>
                <div style="font-size:0.7rem;color:#8892b0;margin-top:4px;">↑${t.ups} ↓${t.downs} →${t.flats}</div>
            </div>`;
        });
        html += `</div></div>`;
    }

    if (result.sum_distribution) {
        html += `<div class="result-card"><h4>和值分布</h4><div class="stat-grid">`;
        result.sum_distribution.forEach(b => {
            html += `<div class="stat-item"><div class="value">${b.count}</div><div class="label">${b.range}</div></div>`;
        });
        html += `</div></div>`;
    }

    if (result.ratio_distribution) {
        html += `<div class="result-card"><h4>比例分布</h4><div class="stat-grid">`;
        Object.entries(result.ratio_distribution).forEach(([ratio, count]) => {
            html += `<div class="stat-item"><div class="value">${ratio}</div><div class="label">${count}次</div></div>`;
        });
        html += `</div></div>`;
    }

    if (result.pattern_distribution) {
        html += `<div class="result-card"><h4>形态分布</h4><div class="stat-grid">`;
        Object.entries(result.pattern_distribution).forEach(([pattern, count]) => {
            html += `<div class="stat-item"><div class="value">${pattern}</div><div class="label">${count}次</div></div>`;
        });
        html += `</div></div>`;
    }

    if (result.per_position_repeat_rate) {
        html += `<div class="result-card"><h4>各位重号概率</h4><div class="stat-grid">`;
        result.per_position_repeat_rate.forEach(p => {
            html += `<div class="stat-item"><div class="value">${p.rate}</div><div class="label">${p.name}</div></div>`;
        });
        html += `</div></div>`;
    }

    container.innerHTML = html;
}

async function runBacktest() {
    const rule = document.getElementById("rule-select").value;
    if (!rule) { alert("请先选择分析规则"); return; }

    const params = getParams();
    const testPeriods = parseInt(document.getElementById("test-periods").value);

    const container = document.getElementById("backtest-result");
    container.innerHTML = `<p class="loading">⏳ 正在回测 ${testPeriods} 期数据...</p>`;
    switchTab("backtest");

    const resp = await fetch("/api/backtest", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ rule, params, test_periods: testPeriods })
    });

    const result = await resp.json();
    displayBacktestResult(result);
}

function displayBacktestResult(result) {
    const container = document.getElementById("backtest-result");
    if (result.error) { container.innerHTML = `<p class="placeholder">${result.error}</p>`; return; }

    const acc = parseFloat(result.position_accuracy_pct);
    const colorClass = acc >= 50 ? "high" : acc >= 30 ? "medium" : "low";

    let html = `
        <div class="result-card">
            <h4>回测总览</h4>
            <div class="accuracy-display ${colorClass}">${result.position_accuracy_pct}</div>
            <p style="text-align:center;color:#8892b0;">单位正确率（每个位置命中的概率）</p>
            <div class="stat-grid">
                <div class="stat-item"><div class="value">${result.test_periods}</div><div class="label">测试期数</div></div>
                <div class="stat-item"><div class="value">${result.avg_hit_positions}</div><div class="label">平均命中位数</div></div>
                <div class="stat-item"><div class="value">${result.any_hit_pct}</div><div class="label">至少命中1位</div></div>
                <div class="stat-item"><div class="value">${result.exact_hits}</div><div class="label">全中期数</div></div>
            </div>
        </div>

        <div class="result-card">
            <h4>各位命中率</h4>`;

    result.per_position_accuracy.forEach(p => {
        const pct = parseFloat(p.accuracy);
        html += `<div class="position-accuracy-bar">
            <span class="pos-label">${p.name}</span>
            <div class="bar-bg"><div class="bar-fill" style="width:${pct}%"></div></div>
            <span class="pct">${p.accuracy}</span>
        </div>`;
    });

    html += `</div>
        <div class="result-card">
            <h4>逐期回测详情</h4>
            <table class="backtest-table">
                <tr><th>期号</th><th>预测(万千百十个)</th><th>开奖</th><th>命中</th></tr>`;

    result.details.slice(0, 30).forEach(d => {
        const hitClass = d.hit_count >= 3 ? "hit" : "";
        const predictedStr = d.position_hits.map(ph => {
            const numsStr = ph.numbers.join(",");
            return ph.hit ? `<b style="color:#ffd700">[${numsStr}]</b>` : `[${numsStr}]`;
        }).join(" ");
        const actualStr = d.actual_digits.join(" ");

        html += `<tr class="${hitClass}">
            <td>${d.period}</td>
            <td style="font-size:0.75rem;">${predictedStr}</td>
            <td><b>${actualStr}</b></td>
            <td>${d.hit_count}/5 ${d.hit_count >= 3 ? "🎯" : d.hit_count > 0 ? "✓" : ""}</td>
        </tr>`;
    });

    if (result.details.length > 30) {
        html += `<tr><td colspan="4" style="text-align:center;color:#8892b0">... 还有 ${result.details.length - 30} 期 ...</td></tr>`;
    }

    html += `</table></div>`;
    container.innerHTML = html;
}
