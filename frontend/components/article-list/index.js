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
    },

    methods: {
        onReachBottom: function() {
              this.triggerEvent('loadmore');
          }
    },

    lifetimes: {
        attached: function() {
          console.log('article-list 组件挂载');
        }
      }
  
  })