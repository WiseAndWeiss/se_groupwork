// article-list.js
const request = require('../../utils/request');

Component({
  properties: {
    // css设置样式
    article_list_scrollHeight: {
      type: String,
      value: "calc(100vh - 870rpx)"
    },
    // 文章列表数据
    list: {
      type: Array,
      value: [],
    },
    emptyText: {
      type: String,
      value: '暂无文章'
    },
    // 新增：加载状态（由父页面传递）
    isLoading: {
      type: Boolean,
      value: false
    },
    // 新增：是否已加载完所有数据（由父页面传递）
    reachEnd: {
      type: Boolean,
      value: false
    },
    // 父页面可控的滚动位置（用于切换页面后强制回到顶部）
    scrollTop: {
      type: Number,
      value: 0
    },
    // 是否启用左滑删除功能
    enableSwipeDelete: {
      type: Boolean,
      value: false
    }
  },

  data: {
    showCollectionSelect: false,
    collectionList: [],
    defaultCollection: null,
    currentFavoriteId: '',
    // 左滑删除相关
    startX: 0,
    currentSwipeIndex: -1,
    isSwiping: false,
    swipeStates: {} // 存储每个item的滑动状态 {index: {swipeClass: '', swipeStyle: ''}}
  },

  observers: {
    'list': function(list) {
      // 当list变化时，重置滑动状态
      if (list && list.length > 0) {
        const swipeStates = {};
        list.forEach((item, index) => {
          swipeStates[index] = {
            swipeClass: '',
            swipeStyle: ''
          };
        });
        this.setData({
          swipeStates: swipeStates,
          currentSwipeIndex: -1
        });
      } else {
        this.setData({
          swipeStates: {},
          currentSwipeIndex: -1
        });
      }
    }
  },

  methods: {
    // 移除：原滑到底部触发的 onReachBottom
    // 新增：点击加载更多按钮触发
    onLoadMoreTap() {
      // 加载中/已到底时不触发
      if (this.properties.isLoading || this.properties.reachEnd) return;
      this.triggerEvent('loadmore');
    },
    // 显示收藏夹选择弹窗
    onShowCollectionSelect(e) {
      console.log('article-list 收到 showCollectionSelect 事件:', e.detail);
      const { collectionList, defaultCollection, currentFavoriteId } = e.detail || {};
      console.log('解析后的数据:', {
        collectionList,
        defaultCollection,
        currentFavoriteId,
        collectionListLength: collectionList ? collectionList.length : 0,
        collectionListType: Array.isArray(collectionList) ? 'Array' : typeof collectionList,
        firstItem: collectionList && collectionList.length > 0 ? collectionList[0] : null
      });
      
      // 确保 collectionList 是数组，并使用深拷贝确保数据正确
      let validCollectionList = [];
      if (Array.isArray(collectionList)) {
        try {
          // 使用深拷贝确保数据是全新的对象
          validCollectionList = JSON.parse(JSON.stringify(collectionList));
        } catch (e) {
          console.error('深拷贝失败，使用原数组:', e);
          validCollectionList = collectionList;
        }
      }
      
      console.log('准备设置的数据:', {
        validCollectionList,
        validCollectionListLength: validCollectionList.length,
        firstItem: validCollectionList.length > 0 ? validCollectionList[0] : null,
        firstItemKeys: validCollectionList.length > 0 ? Object.keys(validCollectionList[0]) : [],
        firstItemId: validCollectionList.length > 0 ? validCollectionList[0].id : null,
        firstItemName: validCollectionList.length > 0 ? validCollectionList[0].name : null,
        allItems: validCollectionList
      });
      
      // 先设置数据，再显示弹窗，确保数据已准备好
      this.setData({
        collectionList: validCollectionList,
        defaultCollection: defaultCollection ? JSON.parse(JSON.stringify(defaultCollection)) : null,
        currentFavoriteId: currentFavoriteId || ''
      }, () => {
        // 数据设置完成后再显示弹窗，使用 setTimeout 确保渲染完成
        setTimeout(() => {
          this.setData({
            showCollectionSelect: true
          }, () => {
            // setData 回调中检查数据
            console.log('article-list setData 完成后的数据:', {
              showCollectionSelect: this.data.showCollectionSelect,
              collectionList: this.data.collectionList,
              collectionListLength: this.data.collectionList.length,
              collectionListType: Array.isArray(this.data.collectionList) ? 'Array' : typeof this.data.collectionList,
              firstItem: this.data.collectionList.length > 0 ? this.data.collectionList[0] : null,
              allItems: this.data.collectionList,
              firstItemName: this.data.collectionList.length > 0 ? this.data.collectionList[0].name : null
            });
          });
        }, 50);
      });
    },
    // 隐藏收藏夹选择弹窗
    onHideCollectionSelect() {
      this.setData({
        showCollectionSelect: false
      });
    },
    // 移动收藏到指定收藏夹
    async onMoveFavouriteToCollection(e) {
      const targetCollectionId = e.currentTarget.dataset.collectionid;
      const { currentFavoriteId } = this.data;
      
      if (!currentFavoriteId || !targetCollectionId) {
        wx.showToast({
          title: '参数错误',
          icon: 'none'
        });
        return;
      }

      try {
        wx.showLoading({
          title: '移动中...'
        });
        await request.moveFavourite(currentFavoriteId, targetCollectionId);
        wx.hideLoading();
        wx.showToast({
          title: '移动成功'
        });
        this.onHideCollectionSelect();
      } catch (err) {
        wx.hideLoading();
        console.error('移动收藏失败：', err);
        wx.showToast({
          title: err || '移动失败',
          icon: 'none'
        });
      }
    },
    // 左滑删除相关方法
    // 触摸开始
    onSwipeTouchStart(e) {
      if (!this.properties.enableSwipeDelete || this.data.isSwiping) return;
      
      const index = parseInt(e.currentTarget.dataset.index);
      // 如果点击的是其他项，先关闭之前打开的项
      if (this.data.currentSwipeIndex !== -1 && this.data.currentSwipeIndex !== index) {
        this.closeSwipe(this.data.currentSwipeIndex);
      }
      
      this.setData({
        startX: e.touches[0].clientX,
        currentSwipeIndex: index
      });
    },
    // 触摸移动
    onSwipeTouchMove(e) {
      if (!this.properties.enableSwipeDelete || this.data.isSwiping) return;
      
      const index = parseInt(e.currentTarget.dataset.index);
      // 只处理当前滑动的项
      if (index !== this.data.currentSwipeIndex) return;
      
      const currentX = e.touches[0].clientX;
      const diffX = this.data.startX - currentX;
      
      // 只允许向左滑动（显示删除按钮）
      if (diffX > 0) {
        const translateX = Math.min(diffX, 120); // 最大滑动距离为120rpx
        this.updateSwipePosition(index, -translateX);
      }
    },
    // 触摸结束
    onSwipeTouchEnd(e) {
      if (!this.properties.enableSwipeDelete || this.data.isSwiping) return;
      
      const index = parseInt(e.currentTarget.dataset.index);
      // 只处理当前滑动的项
      if (index !== this.data.currentSwipeIndex) return;
      
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
      const swipeStates = {...this.data.swipeStates};
      swipeStates[index] = {
        swipeClass: 'swipe-open',
        swipeStyle: `transform: translateX(${translateX}rpx);`
      };
      this.setData({
        swipeStates: swipeStates
      });
    },
    // 打开滑动（显示按钮）
    openSwipe(index) {
      const swipeStates = {...this.data.swipeStates};
      swipeStates[index] = {
        swipeClass: 'swipe-open',
        swipeStyle: 'transform: translateX(-120rpx);'
      };
      
      this.setData({
        swipeStates: swipeStates,
        isSwiping: true
      });
      
      // 300ms后重置滑动状态
      setTimeout(() => {
        this.setData({
          isSwiping: false
        });
      }, 300);
    },
    // 关闭滑动（隐藏按钮）
    closeSwipe(index) {
      const swipeStates = {...this.data.swipeStates};
      swipeStates[index] = {
        swipeClass: '',
        swipeStyle: ''
      };
      
      this.setData({
        swipeStates: swipeStates,
        currentSwipeIndex: -1,
        isSwiping: false
      });
    },
    // 删除操作
    onDeleteItem(e) {
      if (!this.properties.enableSwipeDelete) return;
      
      const index = parseInt(e.currentTarget.dataset.index);
      const list = this.properties.list || [];
      const item = list[index];
      
      if (!item) {
        console.error('删除项不存在:', index);
        return;
      }
      
      // 先关闭滑动
      this.closeSwipe(index);
      
      // 向父组件传递删除事件，传递完整的item对象以便父组件获取所需字段
      this.triggerEvent('delete', {
        id: item.id, // 文章ID（向后兼容）
        historyId: item.historyId, // 历史记录ID（如果有）
        index: index,
        item: item // 完整的item对象
      });
    }
  },

  lifetimes: {
    attached: function () {
      console.log('article-list 组件挂载，初始数据:', {
        showCollectionSelect: this.data.showCollectionSelect,
        collectionList: this.data.collectionList,
        collectionListLength: this.data.collectionList.length
      });
    }
  }
})