import re

with open('public/index.html', 'r', encoding='utf-8') as f:
    html = f.read()

css_add = """
        .header-tools {
            display: flex;
            align-items: center;
            gap: 8px;
            margin-top: 6px;
        }

        .header-tools .update-time {
            padding: 0;
            border: 0;
            background: transparent;
            color: rgba(255, 250, 240, 0.86);
        }

        .header-tools .cookie-dot {
            width: 10px;
            height: 10px;
            box-shadow: 0 0 0 3px rgba(197, 154, 57, 0.12);
        }
        .header-tools .cookie-dot.status-ok {
            box-shadow: 0 0 0 3px rgba(38, 183, 120, 0.14);
        }
        .header-tools .cookie-dot.status-warn {
            box-shadow: 0 0 0 3px rgba(217, 169, 40, 0.14);
        }
        .header-tools .cookie-dot.status-error {
            box-shadow: 0 0 0 3px rgba(198, 61, 53, 0.13);
        }

        .header-tools .tool-btn {
            min-height: 26px;
            background: rgba(255, 250, 240, 0.12);
            border-color: rgba(255, 250, 240, 0.2);
            color: rgba(255, 250, 240, 0.9);
            font-size: 0.72rem;
        }
        .header-tools .tool-btn:hover {
            background: rgba(255, 250, 240, 0.2);
            color: #fff;
        }
"""
html = html.replace('.update-time {', css_add + '\n        .update-time {')

# 桌面端 PC 表头居中
css_head_center = """
            .fund-table-head span:not(:first-child) {
                padding-left: 12px;
                border-left: 1px solid rgba(216, 222, 206, 0.86);
                text-align: center;
            }
"""
html = re.sub(r'\.fund-table-head span:not\(:first-child\) \{.*?\n            \}', css_head_center.strip(), html, flags=re.DOTALL)

# 桌面端 fund-metric/premium 等内容居中
css_metric_center = """
        .fund-metric,
        .fund-premium,
        .fund-actions {
            padding-left: 12px;
            border-left: 1px solid rgba(216, 222, 206, 0.86);
            text-align: center;
        }

        .fund-actions {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
        }
"""
html = re.sub(r'\.fund-metric,\s*\n\s*\.fund-premium,\s*\n\s*\.fund-actions \{.*?border-left:.*?\n\s*\}', css_metric_center.strip(), html, flags=re.DOTALL)


# 移动端 719px 高度压缩，把 actions 和其他列放同一行
css_mobile_card = """
            .fund-card {
                grid-template-columns: minmax(90px, 1.2fr) minmax(56px, 0.8fr) minmax(56px, 0.8fr) minmax(56px, 0.8fr) minmax(64px, 0.9fr);
                min-height: 64px;
                padding: 10px 8px;
                border-left-width: 4px;
            }

            .fund-main {
                padding-right: 4px;
            }

            .fund-name {
                font-size: 0.82rem;
            }

            .fund-code {
                gap: 2px;
                font-size: 0.6rem;
                margin-top: 2px;
            }

            .fund-metric,
            .fund-premium {
                min-height: 48px;
                align-content: center;
                padding-left: 4px;
                border-left: 1px solid rgba(216, 222, 206, 0.6);
            }

            .fund-actions {
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                min-height: 48px;
                margin-top: 0;
                padding-top: 0;
                padding-left: 4px;
                border-top: 0;
                border-left: 1px solid rgba(216, 222, 206, 0.6);
            }

            .mobile-label {
                display: none; /* 去掉多余标签以省空间 */
            }
            .detail-value {
                font-size: 0.78rem;
            }
            .detail-sub {
                font-size: 0.6rem;
            }
            .status-badge {
                padding: 2px 4px;
                font-size: 0.6rem;
                min-height: 18px;
            }
            .detail-btn {
                min-height: 20px;
                padding: 2px 6px;
                font-size: 0.6rem;
                margin-top: 4px;
            }
"""
html = re.sub(r'\.fund-card \{\s*\n\s*grid-template-columns: minmax\(116px.*?\.detail-label \{\s*\n\s*display: none;\s*\n\s*\}', css_mobile_card.strip() + '\n\n            .detail-label {\n                display: none;\n            }', html, flags=re.DOTALL)

with open('public/index.html', 'w', encoding='utf-8') as f:
    f.write(html)
