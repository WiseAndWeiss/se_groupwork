const request = require('../../utils/request');

Page({
  data: {
    collectionid: '',
    collectionName: '',
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
    const collectionid = decodeURIComponent(options.collectionid || '');
    const collectionName = decodeURIComponent(options.name || ''); 
    console.log('collection 页面接收的 collectionid：', collectionid,'name',collectionName);
    
    if (!collectionid) {
      wx.showToast({ title: '参数错误，无法加载', icon: 'none' });
      wx.navigateBack(); // 回退上一页
      return;
    }

    this.setData({ 
        collectionid ,
        collectionName
    });
    this.loadCollectionArticles(); // 加载对应收藏夹文章
  },

  async loadCollectionArticles() {
    if (this.data.isLoading) return;
    console.log('开始加载收藏夹文章...');
    this.setData({ isLoading: true });
    try {
      console.log('正在加载收藏夹文章，collectionid:', this.data.collectionid);
      // 调用 getCollectionArticles 接口
      const response = await request.getCollectionArticles(
        this.data.collectionid, 
        this.data.startRank
      );
      console.log('收藏夹文章 API 响应:', response);
      this.setData({
        articles: response || [],
      });
      console.log('收藏夹文章列表:', this.data.articles);
    } catch (err) {
        console.error('加载收藏夹文章失败：', err);
        wx.showToast({ title: '加载失败', icon: 'none' });
    } finally {
      this.setData({ isLoading: false });
    }
  },

    // 页面卸载时清理（比如跳转到其他Tab页面、关闭页面）
  onHide() {
    console.log('页面卸载，彻底清理数据');
    this.clearPageData();
  },
    
  clearPageData() {
    this.setData({
        collectionid: '',
        collectionName: '',
        articles: [],
        isLoading: false,
        startRank: 0,
        reachEnd: false, 
    });
  }
});