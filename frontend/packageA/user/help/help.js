Component({
    methods: {
      goBack() {
        wx.navigateBack({
          delta: 1 // 返回1级页面栈
        });
      }
    }
  });