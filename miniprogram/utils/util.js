// utils/util.js - 工具函数

/**
 * 格式化时间
 */
function formatTime(date) {
    const year = date.getFullYear();
    const month = date.getMonth() + 1;
    const day = date.getDate();
    const hour = date.getHours();
    const minute = date.getMinutes();
    const second = date.getSeconds();

    return `${[year, month, day].map(formatNumber).join('-')} ${[hour, minute, second].map(formatNumber).join(':')}`;
}

function formatNumber(n) {
    n = n.toString();
    return n[1] ? n : `0${n}`;
}

/**
 * 复制文本到剪贴板
 * @param {string} text - 要复制的文本
 */
function copyToClipboard(text) {
    return new Promise((resolve, reject) => {
        wx.setClipboardData({
            data: text,
            success: () => {
                wx.showToast({
                    title: `已复制 ${text}`,
                    icon: 'success',
                    duration: 1500
                });
                resolve();
            },
            fail: reject
        });
    });
}

/**
 * 判断是否为上海交易所
 * @param {string} fundId - 基金代码
 */
function isShanghai(fundId) {
    return fundId.startsWith('50') || fundId.startsWith('51');
}

/**
 * 获取交易所名称
 * @param {string} fundId - 基金代码
 */
function getExchange(fundId) {
    return isShanghai(fundId) ? '沪' : '深';
}

/**
 * 获取持有天数
 * @param {string} fundId - 基金代码
 */
function getHoldDays(fundId, fundType = '') {
    // 默认规则：普通 LOF -> T+2；QDII-LOF -> T+3
    // 说明：这里展示的是“申购确认后可卖出”的经验值，用于界面提示。
    if (typeof fundType === 'string' && fundType.includes('QDII')) {
        return 'T+3';
    }
    return 'T+2';
}

/**
 * 计算套利难度评级（散户薅羊毛版）
 * @param {object} fund - 基金信息
 * @returns {number} 1-5 星评级，0 表示暂停申购
 */
function calculateDifficulty(fund) {
    const { fund_id, volume, premium_rate, apply_status, fund_type } = fund;
    const isPaused = apply_status.includes('暂停');
    const holdDays = getHoldDays(fund_id || '', fund_type);
    const isLongHold = holdDays === 'T+3';

    if (isPaused) {
        return 0; // 暂停申购
    }

    let difficulty = 1;

    if (premium_rate >= 5 && volume >= 5000) {
        difficulty = 5; // 强烈推荐
    } else if (premium_rate >= 3.5 && volume >= 3000) {
        difficulty = 4; // 推荐
    } else if (premium_rate >= 2.5 && volume >= 2000) {
        difficulty = 3; // 可尝试
    } else if (premium_rate >= 2 && volume >= 1000) {
        difficulty = 2; // 谨慎
    } else {
        difficulty = 1; // 不推荐
    }

    // 持有期更长（如 T+3）则降级：资金占用更久、波动暴露更长
    if (isLongHold && difficulty > 1) {
        difficulty = Math.max(1, difficulty - 1);
    }

    return difficulty;
}

/**
 * 获取星级显示
 * @param {number} difficulty - 难度评级
 */
function getStars(difficulty) {
    if (difficulty === 0) {
        return '🚫';
    }
    return '⭐'.repeat(difficulty);
}

/**
 * 格式化成交额
 * @param {number} volume - 成交额（万元）
 */
function formatVolume(volume) {
    if (volume >= 10000) {
        return `${(volume / 10000).toFixed(2)}亿`;
    }
    return `${volume.toFixed(0)}万`;
}

/**
 * 显示加载提示
 */
function showLoading(title = '加载中...') {
    wx.showLoading({
        title: title,
        mask: true
    });
}

/**
 * 隐藏加载提示
 */
function hideLoading() {
    wx.hideLoading();
}

/**
 * 显示错误提示
 */
function showError(message = '操作失败') {
    wx.showToast({
        title: message,
        icon: 'none',
        duration: 2000
    });
}

module.exports = {
    formatTime,
    copyToClipboard,
    isShanghai,
    getExchange,
    getHoldDays,
    calculateDifficulty,
    getStars,
    formatVolume,
    showLoading,
    hideLoading,
    showError
};
