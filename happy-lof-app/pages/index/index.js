// pages/index/index.js
const api = require('../../utils/api.js');
const util = require('../../utils/util.js');

Page({
    data: {
        fundList: [],
        allFundList: [], // 存储所有数据用于筛选
        loading: true,
        updateTime: '加载中...',
        showPaused: false,
        showHelpModal: false
    },

    /**
     * 生命周期函数--监听页面加载
     */
    onLoad(options) {
        this.loadData();
    },

    /**
     * 切换显示暂停申购
     */
    onTogglePaused(e) {
        const showPaused = e.detail.value;
        this.setData({
            showPaused
        });
        this.renderList();
    },

    /**
     * 显示帮助说明
     */
    showHelp() {
        this.setData({
            showHelpModal: true
        });
    },

    /**
     * 关闭帮助说明
     */
    closeHelp() {
        this.setData({
            showHelpModal: false
        });
    },

    /**
     * 渲染列表（执行筛选）
     */
    renderList() {
        const { allFundList, showPaused } = this.data;
        const fundList = allFundList.filter(fund => {
            if (showPaused) return true;
            return !fund.apply_status.includes('暂停');
        });

        this.setData({
            fundList
        });
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
                const allData = result.data || [];
                this.setData({
                    allFundList: allData,
                    updateTime: result.update_time || util.formatTime(new Date()),
                    loading: false
                });
                // 执行一次渲染筛选
                this.renderList();
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
