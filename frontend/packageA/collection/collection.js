const request = require('../../utils/request');

Page({
  data: {
    collectionid: '',
    collectionName: '',
    articles: [], // 文章列表（格式：{id, title, publish_time, tags, summary, article_url, key_info, account_name, is_favorited}）
    isLoading: false,
  },

  // 返回上一页
  goBack() {
    wx.navigateBack({
      delta: 1
    });
  },

  onLoad(options) {
    // 接收跳转传递的 accounti和name,在本页面里均为data，应该没有问题
    const collectionid = decodeURIComponent(options.collectionid || '');
    const collectionName = decodeURIComponent(options.name || '');
    console.log('collection 页面接收的 collectionid：', collectionid, 'name', collectionName);

    if (!collectionid) {
      wx.showToast({
        title: '参数错误，无法加载',
        icon: 'none'
      });
      wx.navigateBack(); // 回退上一页
      return;
    }

    this.setData({
      collectionid,
      collectionName,
      articles: []
    });
    this.loadCollectionArticles(); // 加载对应收藏夹文章
  },

  async loadCollectionArticles() {
    if (this.data.isLoading) return;
    console.log('开始加载收藏夹文章...');
    this.setData({
      isLoading: true
    });
    try {
      console.log('正在加载收藏夹文章，collectionid:', this.data.collectionid);
      // 调用 getCollectionArticles 接口，不传 startRank 或传 0，一次性加载所有
      const response = await request.getCollectionArticles(
        this.data.collectionid,
        0
      );
      console.log('收藏夹文章 API 响应:', response);
      
      // 转换数据格式为 article-list 需要的格式
      const formattedArticles = (response || []).map(item => ({
        id: item.article.id,
        title: item.article.title,
        publish_time: item.article.publish_time,
        tags: item.article.tags || [],
        summary: item.article.summary || '',
        article_url: item.article.article_url || '',
        key_info: item.article.key_info || '',
        account_name: item.article.account_name || '',
        is_favorited: item.id || 0 // 收藏ID
      }));

      this.setData({
        articles: formattedArticles
      });
      console.log('收藏夹文章列表:', this.data.articles);
    } catch (err) {
      console.error('加载收藏夹文章失败：', err);
      wx.showToast({
        title: '加载失败',
        icon: 'none'
      });
    } finally {
      this.setData({
        isLoading: false
      });
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
    });
  }
});