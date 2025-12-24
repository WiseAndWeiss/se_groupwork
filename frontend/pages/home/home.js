const request = require('../../utils/request');

Page({
  data: {
    showLoadingAnimation: false,
    current: 0,
    autoplay: false, // 自动轮播
    duration: 500,
    interval: 5000,
    swiperList: [], // 轮播图数据 
    selectionList: [], // 卡片数据
    isLoading: false, // 加载状态
    isSwiperLoading: false, // 轮播图加载状态
    processedList: [], // 文章推送数据
    start_rank: 0, // 分页起始位置
    pageSize: 10, // 每页固定加载10条
    reach_end: false, // 是否已加载完所有数据
    isLoaded: false, // 是否已首次加载数据
  },

  onReady() {
    // 此时页面已渲染完成，tabBar 存在，调用不会报错
    wx.hideTabBar({
      animation: false,
      success: () => console.log("tabBar 隐藏成功"),
      fail: (err) => console.log("隐藏失败", err)
    });
  },

  // 页面生命周期
  onShow() {
    console.log('首页页面加载完成');
    if (!this.data.isLoaded) {
      this.setData({ isLoaded: true });
      this.loadRecommendedArticles(); // 加载推荐文章数据（轮播图）
      this.loadLatestArticles(true); // 加载首页文章数据（卡片）
    } else {
      // 返回时不重新加载文章列表，保持之前的状态
      // this.loadRecommendedArticles(); // 轮播图可以每次刷新
    }
  },

  /*
  onPullDownRefresh() {
    const app = getApp();
    // 如果正在拖动桌宠，直接停止刷新，不执行任何操作
    if (app.globalData.isPetDragging) {
      wx.stopPullDownRefresh();
      console.log(app.globalData.isPetDragging);
      return;
    }
    
    console.log('下拉刷新，重置文章列表');
    this.setData({
        start_rank: 0,
        reach_end: false
      });
    Promise.all([this.loadLatestArticles(true)]) // 重置数据
      .finally(() => wx.stopPullDownRefresh());
  },*/

  // 页面卸载时清理（比如跳转到其他Tab页面、关闭页面）
  onHide() {
    console.log('首页页面卸载，彻底清理数据');
    // this.clearPageData();
  },

  clearPageData() {
    this.setData({
      // 清空临时数据列表（轮播图、卡片数据）
      swiperList: [],
      selectionList: [],
      // 重置分页状态
      start_rank: 0,
      reach_end: false,
      // 重置加载状态
      isLoading: false,
      isSwiperLoading: false,
      isLoaded: false,
      // 重置轮播图当前索引
      current: 0
    });
  },

  /**
   * 加载推荐文章（轮播图）
   */
  async loadRecommendedArticles() {
    this.setData({
      showLoadingAnimation: true // 显示加载动画
    });
    if (this.data.isSwiperLoading) return;
    console.log('开始加载推荐文章...');
    this.setData({
      isSwiperLoading: true
    });

    try {
      const response = await request.getRecommendedArticles();
      console.log('获取推荐文章：', response);

      if (response && response.articles) {
        console.log('成功获取推荐文章列表，数量：', response.articles.length);
        const processedList = response.articles.map(item => {
          // 计算paddingRight：摘要长度 × 5
          const paddingRight = item.summary.length;

          return {
            ...item,
            padding_right: paddingRight
          };
        });
        this.setData({
          swiperList: processedList,

        });
        console.log(this.data.swiperList);
      } else {
        console.warn('推荐文章接口返回数据格式异常：', response);
      }
    } catch (error) {
      console.error('加载推荐文章失败：', error);
      this.setData({
        swiperList: [],
      });
    } finally {
      this.setData({
        isSwiperLoading: false,
        showLoadingAnimation: false // 显示加载动画
      });
    };
  },

  /**
   * 轮播栏收藏逻辑（和card组件同一接口、状态、提示）
   */
  async handleCollect(e) {
    const index = e.currentTarget.dataset.index;
    const swiperList = [...this.data.swiperList];
    const article = swiperList[index];
    const articleId = article.id;

    if (!articleId) {
      wx.showToast({
        title: '操作失败：文章ID无效',
        icon: 'none'
      });
      return;
    }
    try {
      if (article.is_favorited) {
        // 取消收藏：调用 DELETE 接口
        await request.deleteFavourite(article.is_favorited);
        article.is_favorited = 0;
        wx.showToast({
          title: '取消收藏成功'
        });
        console.log('swiperlist', swiperList);
        this.loadLatestArticles(true); // 加载首页文章数据（卡片）
        console.log('重新加载');
      } else {
        // 添加收藏：调用 POST 接口
        const articleData = {
          article_id: articleId,
        };
        const response = await request.addFavourite(articleData);
        swiperList[index].is_favorited = response.id;
        wx.showToast({
          title: '收藏成功'
        });
        this.setData({
          swiperList
        });
        console.log('swiperlist', swiperList);
        this.loadLatestArticles(true); // 加载首页文章数据（卡片）
        console.log('重新加载');
      }
      this.setData({
        swiperList
      });
      console.log('swiperlist', swiperList)
    } catch (err) {
      console.error('收藏操作失败：', err);
      wx.showToast({
        title: err || '操作失败',
        icon: 'none'
      });
    }
  },

  /**
   * 加载首页最新文章（卡片）
   */
  async loadLatestArticles(reset = false) {
    if (this.data.isLoading || this.data.reach_end) return; // 新增：已到末尾则不加载
    console.log('开始加载首页文章...');
    this.setData({
      isLoading: true,
      showLoadingAnimation: true // 显示加载动画
    });

    try {

      let start_rank = reset ? 0 : this.data.start_rank;
      console.log('请求start_rank:', start_rank);

      const response = await request.getLatestArticles({
        start_rank
      });

      console.log('获取首页最新文章：', response);

      if (response && response.articles) {
        const newArticles = response.articles;
        console.log('本次加载文章数量：', newArticles.length);

        // 3. 处理数据合并/重置
        const finalList = reset ? newArticles : [...this.data.selectionList, ...newArticles];

        // 4. 计算新的start_rank（建议与pageSize对齐，或用返回数量）
        const newStartRank = start_rank + (newArticles.length || this.data.pageSize);

        // 5. 标记是否已到数据末尾（返回数量小于pageSize则为末尾）
        const reach_end = response.reach_end;

        this.setData({
          selectionList: finalList,
          start_rank: newStartRank,
          reach_end: reach_end // 新增：标记末尾
        });

        console.log('加载后data.start_rank:', this.data.start_rank); // 修正：打印data中的值
        console.log('是否已到末尾:', this.data.reach_end);
      } else {
        console.warn('首页文章接口返回数据格式异常：', response);
        wx.showToast({
          title: '数据加载异常',
          icon: 'none'
        });
      }
    } catch (error) {
      console.error('加载首页文章失败：', error);
      wx.showToast({
        title: '加载失败: ' + error.message,
        icon: 'none'
      });
    } finally {
      this.setData({
        isLoading: false,
        showLoadingAnimation: false // 隐藏加载动画
      });
    }
  },

  /**
   * 轮播图点击事件 - 跳转到文章
   */
  onSwiperTap(e) {
    const index = e.currentTarget.dataset.index;
    const article = this.data.swiperList[index];
    console.log('轮播图点击文章：', article);

    if (article && article.article_url) {
      console.log(article.article_url);
      // 跳转到文章链接
      wx.navigateTo({
        url: `/pages/webview/webview?url=${encodeURIComponent(article.article_url)}&title=${encodeURIComponent(article.title)}`
      });
    } else {
      wx.showToast({
        title: '文章链接无效',
        icon: 'none'
      });
    }
  },

  handleLoadMore() {
    console.log('父页面接收到加载更多事件');
    this.loadLatestArticles(false); // false=追加数据
  },

  onChange(e) {
    const {
      current,
      source
    } = e.detail;
    this.setData({
      current
    });
    console.log('轮播图切换到：', current, source);
  },

  onImageLoad(e) {
    console.log('轮播图图片加载完成：', e.currentTarget.dataset.index);
  },

  // 跳转到校内页面（Tab 切换）
  goToCampus() {
    // this.clearPageData();
    wx.switchTab({
      url: '/pages/campus/campus'
    });
  },

  // 跳转到自选页面（Tab 切换）
  goToSelection() {
    // this.clearPageData();
    wx.switchTab({
      url: '/pages/selection/selection'
    });
  },

  // 跳转到我的页面（Tab 切换）
  goToUser() {
    // this.clearPageData();
    wx.switchTab({
      url: '/pages/user/user'
    });
  },

  // 刷新按钮事件
  onRefresh() {
    console.log('手动刷新首页数据');
    this.clearPageData();
    this.onShow(); // 重新加载数据
  }
});