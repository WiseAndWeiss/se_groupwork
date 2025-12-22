// article-list.js
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

  methods: {
    // 移除：原滑到底部触发的 onReachBottom
    // 新增：点击加载更多按钮触发
    onLoadMoreTap() {
      // 加载中/已到底时不触发
      if (this.properties.isLoading || this.properties.reachEnd) return;
      this.triggerEvent('loadmore');
    }
  },

  lifetimes: {
    attached: function () {
      console.log('article-list 组件挂载');
    }
  }
})