Component({
    options: {
        addGlobalClass: true, 
      },
    properties: {
      title: String,   // 文章标题
      author: String,  // 文章作者
      time: String,    // 文章时间
      tags: Array,     // 文章标签
      desc: String,    // 文章描述
      url: String,     // 文章原文链接
    },
    data: {
      isExpanded: false,  // 控制悬浮窗的展开和收起
      isFavourite: false,
    },
    methods: {
      // 收藏按钮的处理函数
      onFavourite: function () {
        this.setData({
          isFavourite: !this.data.isFavourite,
        });
      },
  
      // 展开按钮的处理函数
      onExpand: function () {
        // 切换展开和收起状态
        this.setData({
          isExpanded: !this.data.isExpanded,
        });
      },
    },
  });
  