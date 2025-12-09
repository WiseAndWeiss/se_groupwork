const request = require('../../utils/request');

Component({
    data: {
      searchContent: '',
      campusAccountList: [],
      showLoadingAnimation: false,
    },
    
    pageLifetimes: {
      onLoad() {
        console.log('校内公众号一览页面加载完成');
      }
    },
  
    methods: {
    
      goBack() {
        wx.navigateBack({
          delta: 1 // 返回1级页面栈
        });
      },
      
      // 输入框内容变化时触发
      onSearchInput(e) {
        this.setData({
          searchContent: e.detail.value
        });
      },

      async searchMoreAccounts() {
        const searchContent = this.data.searchContent.trim();
        this.setData({ 
            showLoadingAnimation: true 
          });

        if (!searchContent) {
          wx.showToast({
            title: '请输入搜索关键词',
            icon: 'none'
          });
          return;
        }
        try {
          const list = await request.getMoreAccountsByName(searchContent);
          if (list) {
            this.setData({
              campusAccountList : list.public_accounts || list 
            })
          }
          else{
            wx.showToast({ title: '订阅列表为空', icon: 'none' });
          }
        } catch (err) {
          wx.showToast({ title: '获取订阅列表失败', icon: 'none' });
          console.error('获取订阅失败：', err);
        } finally {
          console.log(this.data.campusAccountList);
          this.setData({ 
            showLoadingAnimation: false
          });
        }
      },

      async searchAccount() {
        const searchContent = this.data.searchContent.trim();
        this.setData({ 
            showLoadingAnimation: true 
          });
        console.log('test',searchContent);
        

        if (!searchContent) {
          wx.showToast({
            title: '请输入搜索关键词',
            icon: 'none'
          });
          return;
        }

        try {
          const list = await request.getAccountsByName(searchContent);
          if (list) {
            this.setData({
              campusAccountList : list.public_accounts
            })
          }

        } catch (err) {
          wx.showToast({ title: '获取订阅列表失败', icon: 'none' });
          console.error('获取订阅失败：', err);
        } finally {
          console.log(this.data.campusAccountList);
          this.setData({ 
            showLoadingAnimation: false
          });
        }
      }
    }
  });