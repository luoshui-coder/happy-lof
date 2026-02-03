// components/fund-card/fund-card.js
const util = require('../../utils/util.js');

Component({
    properties: {
        fund: {
            type: Object,
            value: {}
        }
    },

    data: {
        exchange: '',
        holdDays: '',
        stars: '',
        volumeText: '',
        priceText: '',
        netValueText: '',
        premiumText: '',
        changeText: '',
        badgeClass: '',
        isSuspended: false
    },

    lifetimes: {
        attached() {
            this.updateFundInfo();
        }
    },

    observers: {
        'fund': function (fund) {
            if (fund && fund.fund_id) {
                this.updateFundInfo();
            }
        }
    },

    methods: {
        /**
         * 更新基金信息
         */
        updateFundInfo() {
            const fund = this.data.fund;
            if (!fund || !fund.fund_id) return;

            const exchange = util.getExchange(fund.fund_id);
            const holdDays = util.getHoldDays(fund.fund_id, fund.fund_type);
            const difficulty = util.calculateDifficulty(fund);
            const stars = util.getStars(difficulty);
            const volumeText = util.formatVolume(fund.volume);

            // 格式化数字显示
            const priceText = fund.price ? fund.price.toFixed(3) : '0.000';
            const netValueText = fund.net_value ? fund.net_value.toFixed(3) : '0.000';
            const premiumText = fund.premium_rate ? fund.premium_rate.toFixed(2) + '%' : '0.00%';
            const changeSign = fund.change_pct > 0 ? '+' : '';
            const changeText = fund.change_pct ? changeSign + fund.change_pct.toFixed(2) + '%' : '0.00%';

            const badgeClass = util.getBadgeClass(fund.apply_status);
            const isSuspended = fund.volume === 0;

            this.setData({
                exchange,
                holdDays,
                stars,
                volumeText,
                priceText,
                netValueText,
                premiumText,
                changeText,
                badgeClass,
                isSuspended
            });
        },

        /**
         * 复制基金代码
         */
        onCopyCode(e) {
            const fundId = this.data.fund.fund_id;
            util.copyToClipboard(fundId);
        },

        /**
         * 卡片点击事件
         */
        onCardTap() {
            const fund = this.data.fund;
            this.triggerEvent('cardtap', { fund });
        }
    }
});
