const request = require('../../utils/request');

// 标签处理（数组/字符串）
const processArticleTags = (tags) => {
    if (Array.isArray(tags)) {
      return tags.map(tag => (typeof tag === 'string' ? tag.trim() : '')).filter(tag => tag);
    } else if (typeof tags === 'string' && tags.trim()) {
      return tags.split(',').map(tag => tag.trim()).filter(tag => tag);
    }
    return [];
  };

Page({
  data: {
    selectionList: [], // 从接口获取的数据
    filteredList: [],  // 筛选后数据
    isFilterShow: false,
    isLoading: false,   // 加载状态
    startRank: 0,      // 分页偏移量
    reachEnd: false,   // 是否已加载完所有数据
    searchContent: '',  // 搜索内容
    currentCategory: 'time', // 当前选中的类目（默认时间）
    showLoadingAnimation: false,
    timeFilter: {
      start: '',
      end: ''
    },
    // 上传的标签
    selectedFilters: {
      type: [],
      account: [],
      content: [],
      other: []
    },
    // 临时标签
    tempSelectedFilters: {
      type: [],
      account: [],
      content: [],
      other: []
    },
    // 标签定义  type对应文章类型；account对应内容领域
    typeTags: ["活动", "比赛", "通知", "指南", "资源", "招募", "招聘", "整合"],
    accountTags: ["清华大学", "清华紫荆之声", "清华大学学生会", "清华大学社会实践", "清华大学学生公益", "清华大学学生社团", "乐学", "学在清华", "清华后勤服务", "清华家园网", "艾生权", "行在清华", "食在清华", "清华体育", "清华大学新清华学堂", "清华大学医院", "清华职业辅导", "清华大学艺术博物馆", "清华海外学习", "清华青年科创", "清华就业", "清华小清心", "软小宣", "清软小研"],
    contentTags: ["学术", "教务", "行政", "体育", "党建", "文娱", "医疗", "生活", "留学", "就业", "实践", "公益"],
    otherTags: ["其他"]
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
    console.log('校内页面加载完成');
    this.loadCampusArticles(true); // 加载文章数据
  },

  // 页面卸载时清理（比如跳转到其他Tab页面、关闭页面）
  onHide() {
    console.log('页面卸载，彻底清理数据');
    this.clearPageData();
  },

  clearPageData() {
    this.setData({
        selectionList: [], // 从接口获取的数据
        filteredList: [],  // 筛选后数据
        isFilterShow: false,
        isLoading: false,   // 加载状态
        startRank: 0,      // 分页偏移量
        reachEnd: false,   // 是否已加载完所有数据
        currentCategory: 'time', 
    });
  },

  // 切换类目
  switchCategory(e) {
    const category = e.currentTarget.dataset.category;
    this.setData({
      currentCategory: category
    });
  },

    //  重置筛选
  resetFilters() {
    this.setData({
      // 清空临时标签
      tempSelectedFilters: {
        type: [],
        account: [],
        content: [],
        other: []
      },
      // 同时重置时间筛选
      timeFilter: {
        start: '',
        end: ''
      }
    });
  },

  //  显示悬浮窗
  showFilterPopup() {
    // 打开时将最终筛选条件复制到临时存储
    const tempSelected = JSON.parse(JSON.stringify(this.data.selectedFilters));
    this.setData({ 
      isFilterShow: true,
      tempSelectedFilters: tempSelected // 临时存储继承当前已选状态
    });
  },
  
  //  隐藏悬浮窗：清空临时标签，放弃本次修改
  hideFilterPopup() {
    this.setData({
        // 清空临时标签
        tempSelectedFilters: {
          type: [],
          account: [],
          content: [],
          other: []
        },
        // 同时重置时间筛选
        timeFilter: {
          start: '',
          end: ''
        },
      isFilterShow: false
      });
  },

  // 加载校园最新文章
  async loadCampusArticles(reset = false) {
    if (this.data.isLoading) return;
    console.log('开始加载校园文章...');
    this.setData({ 
        isLoading: true,
        showLoadingAnimation: true // 显示加载动画
      });
    
    try {
      const startRank = reset ? 0 : this.data.startRank;
      const response = await request.getCampusLatestArticles(startRank);
      console.log('接口返回数据：', response);
      
      if (response && response.articles) {
        // 预处理tags字段：将字符串转换为数组
        const processedArticles = response.articles.map(article => {
          return {
            ...article,
            tags: processArticleTags(article.tags) 
          };
        });
        console.log('处理后的文章数据:', processedArticles);

        const newList = reset ? processedArticles : [...this.data.selectionList, ...processedArticles];
        this.setData({
          selectionList: newList,
          filteredList: newList,
          startRank: startRank + response.articles.length,
          reachEnd: response.reach_end
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

  // 时间输入处理
  onTimeInput(e) {
    const type = e.currentTarget.dataset.type;
    const value = e.detail.value;
    
    this.setData({
      [`timeFilter.${type}`]: value
    });
  },

  //  切换标签选中状态 tempSelectedFilters
  toggleTag(e) {
    const { category, tag } = e.currentTarget.dataset;
    const tempSelected = JSON.parse(JSON.stringify(this.data.tempSelectedFilters));
    const targetTags = tempSelected[category];

    console.log('=== 标签点击调试 ===');
    console.log('点击的标签:', tag);
    console.log('当前数组:', targetTags);
    console.log('数组长度:', targetTags.length);
    console.log('includes结果:', targetTags.includes(tag));
    
    if (targetTags.includes(tag)) {
      // 取消选中
      tempSelected[category] = targetTags.filter(item => item !== tag);
    } else {
      // 选中
      tempSelected[category].push(tag);
    }
    
    this.setData({ tempSelectedFilters: tempSelected }, () => {
      console.log(`临时标签更新：${category}类 - ${tag}`, this.data.tempSelectedFilters[category]);
    });
  },
  
  //  合并搜索内容、时间、最终标签
  getFilterParams() {
    const { timeFilter, selectedFilters, searchContent } = this.data;
    const filterParams = {};
    
    // 搜索内容（去空格）
    if (searchContent.trim()) {
      filterParams.search_content = searchContent.trim();
    }

    // 时间参数
    if (timeFilter.start) {
      filterParams.date_from = timeFilter.start;
    }
    if (timeFilter.end) {
      filterParams.date_to = timeFilter.end;
    }

    // 合并所有类目已选标签
    const allSelectedTags = [
      ...selectedFilters.type,
      ...selectedFilters.content,
      ...selectedFilters.other
    ];
    
    if (allSelectedTags.length > 0) {
      filterParams.tags = allSelectedTags;
    }
    if (selectedFilters.account) {
      filterParams.account_names = selectedFilters.account;
    }
    filterParams.range = 'd';

    console.log('最终请求：', filterParams);
    return filterParams;
  },

  //  应用筛选
  async applyFilters() {
    // 将临时标签保存到最终筛选条件
    this.setData({
      selectedFilters: JSON.parse(JSON.stringify(this.data.tempSelectedFilters)),
      isFilterShow: false
    });
    console.log('已保存的筛选条件：', this.data.selectedFilters);
  },
  
  //  搜索
  async searchArticles() {
    const filterParams = this.getFilterParams();
    this.setData({ showLoadingAnimation: true });
    
    try {
      const response = await request.getFilteredArticles(filterParams);
      if (response && response.articles) {
        // 预处理tags字段
        const processedArticles = response.articles.map(article => ({
          ...article,
          tags: processArticleTags(article.tags)
        }));
        this.setData({
          selectionList: processedArticles,
          filteredList: processedArticles,
          startRank: processedArticles.length,
          reachEnd: response.reach_end
        });
        wx.showToast({ title: `找到${processedArticles.length}条结果` });
      } else {
        wx.showToast({ title: '未找到匹配内容', icon: 'none' });
        this.setData({
          selectionList: [],
          filteredList: []
        });
      }
    } catch (error) {
      console.error('搜索失败：', error);
      wx.showToast({ title: '搜索失败，请重试', icon: 'none' });
    } finally {
      this.setData({ showLoadingAnimation: false });
      wx.hideLoading();
    }
  },

  // 搜索栏输入
  onSearchInput(e) {
    this.setData({
      searchContent: e.detail.value
    });
  },

  // 刷新
  onPullDownRefresh() {
    console.log('下拉刷新，重置campus文章列表');
    this.resetFilters();
    this.setData({
        selectionList: [], // 从接口获取的数据
        filteredList: [],  // 筛选后数据
        isFilterShow: false,
        isLoading: false,   // 加载状态
        startRank: 0,      // 分页偏移量
        reachEnd: false,   // 是否已加载完所有数据
        currentCategory: 'time', 
      });
    Promise.all([this.loadCampusArticles(true)]) // 重置数据
      .finally(() => wx.stopPullDownRefresh());
  },

  // 其他方法
  goToAlllist() {
    wx.switchTab({ url: '/pages/campus-all/campus-all' });
  },

  goToHome() {
    wx.switchTab({ url: '/pages/home/home' });
  },
  
  goToSelection() {
    wx.switchTab({ url: '/pages/selection/selection' });
  },
  
  goToUser() {
    wx.switchTab({ url: '/pages/user/user' });
  }
});