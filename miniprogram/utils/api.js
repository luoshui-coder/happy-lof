// utils/api.js - API 请求封装
const app = getApp();

/**
 * 封装 wx.request
 */
function request(url, method = 'GET', data = {}) {
    return new Promise((resolve, reject) => {
        wx.request({
            url: `${app.globalData.apiBase}${url}`,
            method: method,
            data: data,
            header: {
                'Content-Type': 'application/json'
            },
            success: (res) => {
                if (res.statusCode === 200) {
                    resolve(res.data);
                } else {
                    reject(new Error(`请求失败: ${res.statusCode}`));
                }
            },
            fail: (err) => {
                reject(err);
            }
        });
    });
}

/**
 * 获取高溢价 LOF 基金列表
 * 筛选条件：溢价率 >= 1%，成交额 >= 1000万，非开放申购
 */
function getLOFList() {
    return request('/lof');
}

/**
 * 获取全部 LOF 基金列表
 */
function getAllLOFList() {
    return request('/lof/all');
}

/**
 * 获取指定基金的历史溢价率数据
 * @param {string} fundId - 基金代码
 * @param {number} days - 查询天数，默认 30 天
 */
function getLOFHistory(fundId, days = 30) {
    return request(`/lof/history/${fundId}?days=${days}`);
}

module.exports = {
    getLOFList,
    getAllLOFList,
    getLOFHistory
};
