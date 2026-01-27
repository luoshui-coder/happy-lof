// pages/index/index.js
const api = require('../../utils/api.js');
const util = require('../../utils/util.js');

Page({
    data: {
        fundList: [],
        loading: true,
        updateTime: '加载中...'
    },

    /**
     * 生命周期函数--监听页面加载
     */
    onLoad(options) {
        this.loadData();
    },

    /**
     * 页面相关事件处理函数--监听用户下拉动作
     */
    onPullDownRefresh() {
        this.loadData().then(() => {
            wx.stopPullDownRefresh();
        });
    },

    /**
     * 加载数据
     */
    async loadData() {
        this.setData({
            loading: true
        });

        try {
            const result = await api.getLOFList();

            if (result.success) {
                this.setData({
                    fundList: result.data || [],
                    updateTime: result.update_time || util.formatTime(new Date()),
                    loading: false
                });
            } else {
                throw new Error(result.error || '数据获取失败');
            }
        } catch (error) {
            console.error('加载失败:', error);
            util.showError('数据加载失败，请稍后重试');
            this.setData({
                loading: false,
                fundList: []
            });
        }
    },

    /**
     * 刷新按钮点击
     */
    onRefresh() {
        this.loadData();
    },

    /**
     * 基金卡片点击
     */
    onFundCardTap(e) {
        const { fund } = e.detail;
        wx.navigateTo({
            url: `/pages/detail/detail?fundId=${fund.fund_id}&fundName=${fund.fund_name}`
        });
    }
});
