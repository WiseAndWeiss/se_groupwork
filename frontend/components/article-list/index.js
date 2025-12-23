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
    }
  },

  data: {
    showCollectionSelect: false,
    collectionList: [],
    defaultCollection: null,
    currentFavoriteId: ''
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