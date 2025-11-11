Component({
    data: {},
  
    pageLifetimes: {
      onLoad(options) {
        console.log('校内公众号一览页面加载完成');
      }
    },
  
    methods: {
     

      goBack() {
        wx.navigateBack({
          delta: 1 // 返回1级页面栈
        });
      },
      
      
    }
  });