const request = require('../../../utils/request');

Component({
  data: {
    historyList: [], // 历史记录列表
    start_rank: 0, // 分页游标
    reach_end: false, // 是否到底
    isLoading: false, // 是否正在加载
    showLoadingAnimation: false,
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
        isLoading: false
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
          const newHistories = response.histories.map(item => ({
            ...item.article,
            historyId: item.id // 保留历史记录的ID，用于删除操作
          }));
          const finalList = reset ? newHistories : [...this.data.historyList, ...newHistories];
          const newStartRank = start_rank + (newHistories.length || 20);
          const reach_end = response.reach_end;
          this.setData({
            historyList: finalList,
            start_rank: newStartRank,
            reach_end: reach_end
          });
        } else {
          wx.showToast({
            title: '数据加载异常',
            icon: 'none'
          });
        }
      } catch (err) {
        wx.showToast({
          title: '获取历史记录失败',
          icon: 'none'
        });
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

    // 单条删除（从 article-list 组件的事件中接收）
    async deleteHistory(e) {
      const { id, index, historyId, item } = e.detail || {};
      const itemIndex = index !== undefined ? index : e.currentTarget?.dataset?.index;
      
      if (itemIndex === undefined) {
        console.error('删除参数错误: 缺少index', e.detail);
        return;
      }

      const {
        historyList
      } = this.data;
      const deletedItem = item || historyList[itemIndex]; // 优先使用事件传递的item，否则从列表获取
      
      if (!deletedItem) {
        console.error('删除项不存在:', itemIndex);
        return;
      }
      
      // 使用历史记录的ID（historyId），如果没有则使用文章ID
      // 注意：后端API需要的是历史记录的ID，不是文章的ID
      const deleteId = historyId || deletedItem.historyId || deletedItem.id;
      
      console.log('删除历史记录:', { deleteId, deletedItem, itemIndex });
      
      const newHistoryList = historyList.filter((_, i) => i !== itemIndex);
      this.setData({
        historyList: newHistoryList
      }, () => {
        console.log('本地已移除历史记录，UI即时更新');
      });
      try {
        await request.deleteHistory(deleteId);
        wx.showToast({
          title: '删除成功'
        });
        // 删除后如果不足一页且未到末尾，自动补充加载
        if (this.data.historyList.length < 10 && !this.data.reach_end) {
          this.loadHistory(false);
        }
      } catch (err) {
        this.setData({
          historyList: [...newHistoryList.slice(0, itemIndex), deletedItem, ...newHistoryList.slice(itemIndex)]
        });
        wx.showToast({
          title: err || '删除失败',
          icon: 'none'
        });
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
        success: async function (res) {
          if (res.confirm) { // 用户点击「删除」
            try {
              wx.showLoading({
                title: '删除中...'
              });
              await request.deleteAllHistory();
              wx.hideLoading();
              wx.showToast({
                title: '全部删除成功'
              });
              that.resetAndLoadHistory();
            } catch (err) {
              wx.hideLoading();
              wx.showToast({
                title: err || '删除失败',
                icon: 'none'
              });
              console.error('删除所有历史记录失败：', err);
            }
          }
        }
      });
    },

    // 返回上一页
    goBack() {
      wx.navigateBack({
        delta: 1
      });
    },

    // 初始化卡片展开状态
    initCardExpand(e) {
      const index = e.currentTarget.dataset.index;
      this.selectComponent(`.card-component-${index}`).setData({
        isExpanded: true
      });
    },

    // 收藏操作开始
    onCollectionOperationStart() {
      this.setData({
        isCollectionOperating: true
      });
    },

    // 收藏操作结束
    onCollectionOperationEnd() {
      this.setData({
        isCollectionOperating: false
      });
    }
  }
});