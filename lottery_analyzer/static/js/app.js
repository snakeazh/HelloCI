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

    const COLORS = [
        "rgba(229, 57, 53, 0.7)", "rgba(255, 152, 0, 0.7)",
        "rgba(76, 175, 80, 0.7)", "rgba(33, 150, 243, 0.7)", "rgba(156, 39, 176, 0.7)"
    ];

    if (position === -1 && data.positions) {
        distributionChart = new Chart(ctx, {
            type: "bar",
            data: {
                labels: [0,1,2,3,4,5,6,7,8,9],
                datasets: data.positions.map((pos, idx) => ({
                    label: pos.name,
                    data: pos.distribution.map(d => d.count),
                    backgroundColor: COLORS[idx],
                    borderWidth: 1,
                }))
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
    } else {
        const dist = data.distribution;
        const counts = dist.map(d => d.count);
        const avg = counts.reduce((a, b) => a + b, 0) / counts.length;
        const colors = counts.map(c =>
            c > avg * 1.2 ? "rgba(100, 255, 218, 0.8)" :
            c < avg * 0.8 ? "rgba(136, 146, 176, 0.5)" : "rgba(100, 255, 218, 0.4)"
        );
        distributionChart = new Chart(ctx, {
            type: "bar",
            data: {
                labels: [0,1,2,3,4,5,6,7,8,9],
                datasets: [{ label: `${data.name}出现次数`, data: counts, backgroundColor: colors, borderWidth: 1 }]
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

    const resp = await fetch("/api/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ rule, params: getParams() })
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
        <p style="color:#8892b0;margin-bottom:12px;">预测3个号码（出现在开奖5位中即命中）：</p>
        <div class="pick3-display">`;

    (result.predicted_numbers || []).forEach(n => {
        html += `<div class="digit-ball big">${n}</div>`;
    });
    html += `</div></div>`;

    if (result.frequency_data) {
        html += `<div class="result-card"><h4>号码频率（近期所有位置汇总）</h4><div class="freq-bars">`;
        const maxCount = Math.max(...result.frequency_data.map(f => f.count));
        result.frequency_data.sort((a, b) => b.count - a.count);
        result.frequency_data.forEach(f => {
            const pct = (f.count / maxCount * 100).toFixed(0);
            const isSelected = (result.predicted_numbers || []).includes(f.number);
            html += `<div class="freq-bar-row ${isSelected ? 'selected' : ''}">
                <span class="freq-num">${f.number}</span>
                <div class="freq-bar-bg"><div class="freq-bar-fill" style="width:${pct}%"></div></div>
                <span class="freq-count">${f.count}</span>
            </div>`;
        });
        html += `</div></div>`;
    }

    if (result.top_combinations) {
        html += `<div class="result-card"><h4>最热门3号组合 TOP10</h4><table class="backtest-table">
            <tr><th>#</th><th>组合</th><th>同时出现次数</th></tr>`;
        result.top_combinations.forEach((c, i) => {
            const isTop = i === 0;
            html += `<tr class="${isTop ? 'hit' : ''}"><td>${i+1}</td><td><b>${c.combo.join(" ")}</b></td><td>${c.count}</td></tr>`;
        });
        html += `</table></div>`;
    }

    if (result.gap_data) {
        html += `<div class="result-card"><h4>各号码遗漏期数</h4><div class="freq-bars">`;
        result.gap_data.forEach(g => {
            const isSelected = (result.predicted_numbers || []).includes(g.number);
            html += `<div class="freq-bar-row ${isSelected ? 'selected' : ''}">
                <span class="freq-num">${g.number}</span>
                <div class="freq-bar-bg"><div class="freq-bar-fill overdue" style="width:${Math.min(g.gap * 10, 100)}%"></div></div>
                <span class="freq-count">${g.gap}期</span>
            </div>`;
        });
        html += `</div></div>`;
    }

    if (result.trend_data) {
        html += `<div class="result-card"><h4>趋势评分（前半段→后半段变化）</h4><div class="freq-bars">`;
        result.trend_data.forEach(t => {
            const isSelected = (result.predicted_numbers || []).includes(t.number);
            const direction = t.trend > 0 ? "↑" : t.trend < 0 ? "↓" : "→";
            html += `<div class="freq-bar-row ${isSelected ? 'selected' : ''}">
                <span class="freq-num">${t.number}</span>
                <span style="color:${t.trend > 0 ? '#38ef7d' : '#ff5252'}">${direction} ${(t.trend * 100).toFixed(1)}%</span>
                <span class="freq-count">前${t.first_half} 后${t.second_half}</span>
            </div>`;
        });
        html += `</div></div>`;
    }

    if (result.section_details) {
        html += `<div class="result-card"><h4>分区详情</h4>`;
        result.section_details.forEach(s => {
            html += `<p style="margin:8px 0;color:#8892b0;">${s.section}：选<b style="color:#64ffda">${s.selected}</b> — `;
            html += Object.entries(s.numbers).map(([n, c]) => `${n}(${c}次)`).join(" ");
            html += `</p>`;
        });
        html += `</div>`;
    }

    container.innerHTML = html;
}

async function runBacktest() {
    const rule = document.getElementById("rule-select").value;
    if (!rule) { alert("请先选择分析规则"); return; }

    const testPeriods = parseInt(document.getElementById("test-periods").value);
    const container = document.getElementById("backtest-result");
    container.innerHTML = `<p class="loading">⏳ 正在回测 ${testPeriods} 期...</p>`;
    switchTab("backtest");

    const resp = await fetch("/api/backtest", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ rule, params: getParams(), test_periods: testPeriods })
    });
    const result = await resp.json();
    displayBacktestResult(result);
}

function displayBacktestResult(result) {
    const container = document.getElementById("backtest-result");
    if (result.error) { container.innerHTML = `<p class="placeholder">${result.error}</p>`; return; }

    const all3 = parseFloat(result.all3_rate_pct);
    const colorClass = all3 >= 15 ? "high" : all3 >= 8 ? "medium" : "low";

    let html = `
        <div class="result-card">
            <h4>🎯 预测3个号码全部命中率</h4>
            <div class="accuracy-display ${colorClass}">${result.all3_rate_pct}</div>
            <p style="text-align:center;color:#8892b0;">3个预测号码全部出现在开奖5位数中</p>
            <div class="stat-grid">
                <div class="stat-item"><div class="value">${result.test_periods}</div><div class="label">测试期数</div></div>
                <div class="stat-item"><div class="value">${result.all3_hits}</div><div class="label">3个全中</div></div>
                <div class="stat-item"><div class="value">${result.at_least2_rate_pct}</div><div class="label">≥2个命中</div></div>
                <div class="stat-item"><div class="value">${result.at_least1_rate_pct}</div><div class="label">≥1个命中</div></div>
                <div class="stat-item"><div class="value">${result.avg_hit_count}</div><div class="label">平均命中个数</div></div>
            </div>
        </div>

        <div class="result-card">
            <h4>逐期详情</h4>
            <table class="backtest-table">
                <tr><th>期号</th><th>预测3号</th><th>开奖号码</th><th>命中</th></tr>`;

    result.details.slice(0, 50).forEach(d => {
        const hitClass = d.all_hit ? "hit" : "";
        const predictedHtml = d.predicted.map(n =>
            d.hit_numbers.includes(n)
                ? `<span style="color:#ffd700;font-weight:700">${n}</span>`
                : `${n}`
        ).join(" ");
        const actualStr = d.actual_digits.join("");
        const hitLabel = d.hit_count === 3 ? "🎯全中" : d.hit_count === 2 ? "✓✓" : d.hit_count === 1 ? "✓" : "✗";

        html += `<tr class="${hitClass}">
            <td>${d.period}</td>
            <td>${predictedHtml}</td>
            <td><b>${actualStr}</b></td>
            <td>${hitLabel} (${d.hit_count}/3)</td>
        </tr>`;
    });

    if (result.details.length > 50) {
        html += `<tr><td colspan="4" style="text-align:center;color:#8892b0">... 还有 ${result.details.length - 50} 期 ...</td></tr>`;
    }

    html += `</table></div>`;
    container.innerHTML = html;
}
