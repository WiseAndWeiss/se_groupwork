const request = require('../../../utils/request');

Component({
  data: {
    historyList: [], // 历史记录列表
    start_rank: 0, // 分页游标
    reach_end: false, // 是否到底
    isLoading: false, // 是否正在加载
    showLoadingAnimation: false,
    startX: 0, // 触摸开始X坐标
    currentSwipeIndex: -1, // 当前滑动的项目索引
    isSwiping: false ,// 是否正在滑动
    isCollectionOperating: false // 是否正在进行收藏操作
  },

  methods: {
    // 页面显示时刷新历史记录
    onShow() {
      this.resetAndLoadHistory();
    },

    // 页面卸载时清理（比如跳转到其他Tab页面、关闭页面）
    onHide() {
      console.log('页面卸载，彻底清理数据');
      this.clearPageData();
    },
  
    clearPageData() {
      this.setData({
        historyList: [],
        start_rank: 0,
        reach_end: false,
        isLoading: false,
        currentSwipeIndex: -1,
        isSwiping: false
      });
    },

    // 重置并加载第一页历史记录
    resetAndLoadHistory() {
      this.setData({
        historyList: [],
        start_rank: 0,
        reach_end: false
      }, () => {
        this.loadHistory(true);
      });
    },

    // 分页加载历史记录
    async loadHistory(reset = false) {
      if (this.data.isLoading || this.data.reach_end) return;
      this.setData({ 
        isLoading: true,
        showLoadingAnimation: true
      });
      try {
        let start_rank = reset ? 0 : this.data.start_rank;
        const response = await request.getHistoryList(start_rank);
        if (response && response.histories) {
          const newHistories = response.histories.map(item => ({ ...item.article, swipeClass: '' }));
          const finalList = reset ? newHistories : [...this.data.historyList, ...newHistories];
          const newStartRank = start_rank + (newHistories.length || 20);
          const reach_end = response.reach_end;
          this.setData({
            historyList: finalList,
            start_rank: newStartRank,
            reach_end: reach_end
          });
        } else {
          wx.showToast({ title: '数据加载异常', icon: 'none' });
        }
      } catch (err) {
        wx.showToast({ title: '获取历史记录失败', icon: 'none' });
        console.error('获取历史记录失败：', err);
      }
      this.setData({ 
        showLoadingAnimation: false,
        isLoading: false
      });
    },
    // 滚动到底部加载更多
    onReachBottom() {
      this.loadHistory(false);
    },

    // 触摸开始
    onTouchStart(e) {
      if (this.data.isSwiping) return;
      
      const index = e.currentTarget.dataset.index;
      this.setData({
        startX: e.touches[0].clientX,
        currentSwipeIndex: index
      });
    },

    // 触摸移动
    onTouchMove(e) {
      if (this.data.isSwiping) return;
      
      const index = e.currentTarget.dataset.index;
      const currentX = e.touches[0].clientX;
      const diffX = this.data.startX - currentX;
      
      // 只允许向右滑动（显示删除按钮）
      if (diffX > 0) {
        const translateX = Math.min(diffX, 120); // 最大滑动距离为单个按钮宽度
        this.updateSwipePosition(index, -translateX);
      }
    },

    // 触摸结束
    onTouchEnd(e) {
      if (this.data.isSwiping) return;
      
      const index = e.currentTarget.dataset.index;
      const currentX = e.changedTouches[0].clientX;
      const diffX = this.data.startX - currentX;
      
      // 如果滑动距离超过按钮宽度的一半，则完全展开，否则收回
      if (diffX > 60) {
        this.openSwipe(index);
      } else {
        this.closeSwipe(index);
      }
    },

    // 更新滑动位置
    updateSwipePosition(index, translateX) {
      const { historyList } = this.data;
      const newList = [...historyList];
      
      if (newList[index]) {
        newList[index].swipeClass = `swipe-open`;
        newList[index].swipeStyle = `transform: translateX(${translateX}rpx);`;
      }
      
      this.setData({ historyList: newList });
    },

    // 打开滑动（显示按钮）
    openSwipe(index) {
      const { historyList } = this.data;
      const newList = [...historyList];
      
      if (newList[index]) {
        newList[index].swipeClass = 'swipe-open';
      }
      
      this.setData({ 
        historyList: newList,
        isSwiping: true 
      });
      
      // 300ms后重置滑动状态
      setTimeout(() => {
        this.setData({ isSwiping: false });
      }, 300);
    },

    // 关闭滑动（隐藏按钮）
    closeSwipe(index) {
        const { historyList } = this.data;
        const newList = [...historyList];
        if (newList[index]) {
            newList[index].swipeClass = '';
            newList[index].swipeStyle = '';
        }
        this.setData({ 
            historyList: newList,
            currentSwipeIndex: -1,
            isSwiping: false 
        });
      
      // 300ms后重置滑动状态
      setTimeout(() => {
        this.setData({ isSwiping: false });
      }, 300);
    },

    // 单条删除
    async deleteHistory(e) {
      const articleId = e.currentTarget.dataset.id;
      const index = e.currentTarget.dataset.index;
      // 先关闭滑动
      this.closeSwipe(index);

      const { historyList } = this.data;
      const deletedItem = historyList[index]; // 保存被删项，用于接口失败回滚
      const newHistoryList = historyList.filter((_, i) => i !== index);
      this.setData({ historyList: newHistoryList }, () => {
        console.log('本地已移除历史记录，UI即时更新');
      });
      try {
        await request.deleteHistory(articleId);
        wx.showToast({ title: '删除成功' });
        // 删除后如果不足一页且未到末尾，自动补充加载
        if (this.data.historyList.length < 10 && !this.data.reach_end) {
          this.loadHistory(false);
        }
      } catch (err) {
        this.setData({ historyList: [...newHistoryList.slice(0, index), deletedItem, ...newHistoryList.slice(index)] });
        wx.showToast({ title: err || '删除失败', icon: 'none' });
        console.error('删除单条历史记录失败：', err);
      }
    },

    deleteAllHistory() {
      const that = this;
      wx.showModal({
        title: '确认删除',
        content: '是否删除所有浏览历史？删除后不可恢复',
        cancelText: '取消',
        confirmText: '删除',
        confirmColor: '#ff4d4f',
        success: async function(res) {
          if (res.confirm) { // 用户点击「删除」
            try {
              wx.showLoading({ title: '删除中...' });
              await request.deleteAllHistory();
              wx.hideLoading();
              wx.showToast({ title: '全部删除成功' });
              that.resetAndLoadHistory();
            } catch (err) {
              wx.hideLoading();
              wx.showToast({ title: err || '删除失败', icon: 'none' });
              console.error('删除所有历史记录失败：', err);
            }
          }
        }
      });
    },

    // 返回上一页
    goBack() {
      wx.navigateBack({ delta: 1 });
    },

    // 初始化卡片展开状态
    initCardExpand(e) {
      const index = e.currentTarget.dataset.index;
      this.selectComponent(`.card-component-${index}`).setData({ isExpanded: true });
    },

    // 收藏操作开始
    onCollectionOperationStart() {
      this.setData({ isCollectionOperating: true });
    },

    // 收藏操作结束
    onCollectionOperationEnd() {
      this.setData({ isCollectionOperating: false });
    }
  }
});