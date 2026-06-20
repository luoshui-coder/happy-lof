import re

with open('public/index.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 1. 移动 Cookie、刷新、指南到 Header 更新时间旁边
# Header 修改
header_html = """
        <div class="header-inner">
            <img class="brand-mark" src="chicken.png" width="48" height="48" alt="今乐福">
            <div class="brand-copy">
                <h1>今乐福</h1>
                <p>LOF 溢价查询 · 把握基金的每一次价值偏离</p>
                <div class="header-tools">
                    <span class="cookie-dot status-warn" id="cookieStatus" role="img" aria-label="Cookie 状态加载中" title="Cookie 状态加载中"></span>
                    <span class="update-time" id="updateTime" aria-live="polite">加载中...</span>
                    <button class="tool-btn" type="button" id="refreshBtn" onclick="loadData(true)" aria-label="刷新数据" title="刷新数据">↻</button>
                    <button class="tool-btn guide-btn" type="button" id="guideBtn" onclick="switchView('tutorial')" aria-pressed="false">指南</button>
                </div>
            </div>
        </div>
"""
html = re.sub(r'<div class="header-inner">.*?</div>\s*</div>', header_html.strip() + '\n    </div>', html, flags=re.DOTALL)

# 删除 control-top 里的 tool-actions
html = re.sub(r'<div class="tool-actions">.*?</div>', '', html, flags=re.DOTALL)
html = re.sub(r'<div class="control-top">\s*<label class="search-field">.*?</label>\s*</div>',
              r'<div class="control-top">\n            <label class="search-field">\n                <span class="search-icon" aria-hidden="true">🔍</span>\n                <input id="fundSearch" type="search" placeholder="代码 / 名称" autocomplete="off" aria-label="按基金代码或名称搜索">\n            </label>\n        </div>',
              html, flags=re.DOTALL)

# 2. 修改“共 / 全部”显示
html = html.replace('<span>共 ${displayList.length} 条 / 全部 ${(result.data || []).length} 条</span>',
                    '<span>${displayList.length} / ${(result.data || []).length}</span>')

with open('public/index.html', 'w', encoding='utf-8') as f:
    f.write(html)
