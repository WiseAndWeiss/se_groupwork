
const request = require('../../../utils/request');

Page({
  data: {
    accountid: '',
    accountName: '',
    articles: [],
    isLoading: false,
    startRank: 0,
    reachEnd: false,   // 是否已加载完所有数据
  },

  // 返回上一页
  goBack() {
    wx.navigateBack({ delta: 1 });
  },

  onLoad(options) {
    // 接收跳转传递的 accounti和name,在本页面里均为data，应该没有问题
    const accountid = decodeURIComponent(options.accountid || '');
    const accountName = decodeURIComponent(options.name || ''); 
    console.log('detail 页面接收的 accountid：', accountid,'name',accountName);
    
    if (!accountid) {
      wx.showToast({ title: '参数错误，无法加载', icon: 'none' });
      wx.navigateBack(); // 回退上一页
      return;
    }

    this.setData({ 
        accountid ,
        accountName
    });
    this.loadAccountArticles(); // 加载该公众号的文章
  },

    // 页面卸载时清理（比如跳转到其他Tab页面、关闭页面）
  onHide() {
    console.log('页面卸载，彻底清理数据');
    this.clearPageData();
  },
    
  clearPageData() {
    this.setData({
        accountid: '',
        accountName: '',
        articles: [],
        isLoading: false,
        startRank: 0,
        reachEnd: false, 
    });
  },

  // 加载指定公众号的文章（调用 Mock 接口 mockGetArticlesByAccount）
  async loadAccountArticles() {
    if (this.data.isLoading) return;
    console.log('开始加载文章...');
    this.setData({ isLoading: true });
    try {
      console.log('正在加载公众号文章，accountid:', this.data.accountid);
      const data = {
        account_id: this.data.accountid,
        start_rank: this.data.startRank
      }
      const response = await request.getArticlesByAccount(data);
      console.log('API 响应:', response);
      this.setData({
        articles: response.articles,
      });
      console.log('响应:', this.data.articles);
    } catch (err) {
        console.error('加载公众号文章失败：', err);
        wx.showToast({ title: '加载失败', icon: 'none' });
    } finally {
      this.setData({ isLoading: false });
    }
  }
});