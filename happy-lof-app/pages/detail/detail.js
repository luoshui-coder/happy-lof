// pages/detail/detail.js
const api = require('../../utils/api.js');
const util = require('../../utils/util.js');

Page({
    data: {
        fundId: '',
        fundName: '',
        historyData: [],
        loading: true
    },

    onLoad(options) {
        const { fundId, fundName } = options;
        this.setData({
            fundId: fundId || '',
            fundName: decodeURIComponent(fundName || '基金详情')
        });

        wx.setNavigationBarTitle({
            title: decodeURIComponent(fundName || '基金详情')
        });

        this.loadHistoryData();
    },

    async loadHistoryData() {
        const { fundId } = this.data;
        if (!fundId) return;

        this.setData({ loading: true });

        try {
            const result = await api.getLOFHistory(fundId, 30);

            if (result.success && result.data && result.data.length > 0) {
                this.setData({
                    historyData: result.data.slice(-10).reverse(),
                    loading: false
                });
            } else {
                this.setData({
                    historyData: [],
                    loading: false
                });
            }
        } catch (error) {
            console.error('加载历史数据失败:', error);
            util.showError('历史数据加载失败');
            this.setData({
                loading: false,
                historyData: []
            });
        }
    },

    onCopyCode() {
        util.copyToClipboard(this.data.fundId);
    },

    onViewDetail() {
        const url = `http://fund.eastmoney.com/${this.data.fundId}.html`;

        wx.setClipboardData({
            data: url,
            success: () => {
                wx.showModal({
                    title: '提示',
                    content: '链接已复制，请在浏览器中打开查看详情',
                    showCancel: false
                });
            }
        });
    }
});
