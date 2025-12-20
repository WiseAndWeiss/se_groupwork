
const request = require('../../../utils/request');

Page({
  data: {
    accountid: '',
    accountName: '',
    articles: [],
    isLoading: false,
    start_rank: 0,      // 分页偏移量
    reach_end: false,   // 是否已加载完所有数据
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
    //this.clearPageData();
  },
    
  clearPageData() {
    this.setData({
        accountid: '',
        accountName: '',
        articles: [],
        isLoading: false,
        start_rank: 0,      // 分页偏移量
        reach_end: false,   // 是否已加载完所有数据
    });
  },

  // 加载指定公众号的文章（调用 Mock 接口 mockGetArticlesByAccount）
  async loadAccountArticles(reset = false) {
    if (this.data.isLoading || this.data.reach_end) return;
        console.log('开始加载公众号文章...');
        this.setData({ 
            isLoading: true,
            showLoadingAnimation: true 
          });
        
        try {
          let start_rank = reset ? 0 : this.data.start_rank;
          console.log('请求start_rank:', start_rank);
    
          const response = await request.getArticlesByAccount({
            account_id: this.data.accountid,
            start_rank: start_rank
          });
          
          if (response && response.articles) {
            const newArticles = response.articles;
            console.log('本次加载文章数量：', newArticles.length);
            
            // 3. 处理数据合并/重置
            const finalList = reset ? newArticles : [...this.data.articles, ...newArticles];
            
            // 4. 计算新的start_rank（建议与pageSize对齐，或用返回数量）
            const newStartRank = start_rank + (newArticles.length || this.data.pageSize);
            
            // 5. 标记是否已到数据末尾（返回数量小于pageSize则为末尾）
            const reach_end = response.reach_end;
            this.setData({
              articles: finalList,
              start_rank: newStartRank,
              reach_end: reach_end
            });
          } else {
            console.warn('接口返回数据格式异常：', response);
            wx.showToast({ title: '数据加载异常', icon: 'none' });
          }
        } catch (error) {
          console.error('加载校园文章失败：', error);
          wx.showToast({ title: '加载失败: ' + error, icon: 'none' });
          this.setData({
            selectionList: [],
            filteredList: []
          });
        } finally {
          console.log('加载完成，设置 isLoading = false');
          this.setData({ 
            isLoading: false,
            showLoadingAnimation: false // 隐藏加载动画
          });
        }
  },

  handleLoadMore() {
    console.log('触发加载更多文章...');
    this.loadAccountArticles();
  }
});

