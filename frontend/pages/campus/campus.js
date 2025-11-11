// 引入全局测试数据
const testData = require('../../data/testData.js');

Component({
  data: {
    selectionList: testData.sharedNewsList, // 原始卡片数据
    filteredList: testData.sharedNewsList,  // 筛选后数据
    isFilterShow: false,                    // 悬浮窗显示状态
    selectedTag: [],                        // 选中的标签
    // 标签，（后续添加）
    contentTags: ['文娱活动','学术论坛讲座','共享'],
    // 公众号
    officialTags: []
  },

  // 页面生命周期
  pageLifetimes: {
    onLoad(options) {
      console.log('校内页面加载完成');
      this.extractOfficialTags();
      this.extractContentTags();
    },
    onPullDownRefresh() {
      console.log('下拉刷新');
      setTimeout(() => {
        wx.stopPullDownRefresh();
        wx.showToast({ title: '刷新成功', icon: 'success' });
        this.setData({
            filteredList: testData.sharedNewsList,
            selectedTags: []
          });
      }, 1000);
    }
  },

  methods: {
    //提取公众号（未试验）
    extractOfficialTags() {
        const officialTags = testData.campusOfficialTestList.map(item => {
          return item.name; 
        });
        this.setData({ officialTags });
      },
    
    //提取标签
    extractContentTags() {
        const contentTags = ['全部']; // 默认包含“全部”
        this.data.selectionList.forEach(card => {
          card.tags.forEach(tag => {
            if (!contentTags.includes(tag)) {
              contentTags.push(tag); // 去重添加标签
            }
          });
        });
        this.setData({ contentTags });
      },
    
    // 显示/隐藏悬浮窗
    showFilterPopup() {
        this.setData({ isFilterShow: true });
      },
      hideFilterPopup() {
        this.setData({ isFilterShow: false });
      },
  
     // 核心优化：筛选逻辑+详细日志+匹配容错
    selectTag(e) {
        const tag = e.currentTarget.dataset.tag;
        const { selectedTags = [], selectionList = [] } = this.data;
        let newSelectedTags = [...selectedTags];
  
        // 切换选中/取消
        if (newSelectedTags.includes(tag)) {
          newSelectedTags = newSelectedTags.filter(item => item !== tag);
          console.log(`取消选中标签【${tag}】，当前选中标签：`, newSelectedTags);
        } else {
          newSelectedTags.push(tag);
          console.log(`选中标签【${tag}】，当前选中标签：`, newSelectedTags);
        }
  
        // 筛选逻辑：确保“所有选中标签都在卡片tags中”
        let filteredList = [];
        if (newSelectedTags.length === 0) {
          filteredList = selectionList;
          console.log('无选中标签，显示所有卡片（共', filteredList.length, '张）');
        } else {
          console.log('开始筛选：需要包含所有标签', newSelectedTags);
          filteredList = selectionList.filter((card, cardIndex) => {
            const cardTags = card.tags || []; 
            console.log(`\n卡片${cardIndex+1}：标题【${card.title}】，卡片tags：`, cardTags);
            
            // 检查是否包含所有选中标签
            const isMatch = newSelectedTags.every(selectedTag => {
              const match = cardTags.some(cardTag => 
                cardTag.trim().toLowerCase() === selectedTag.trim().toLowerCase()
              );
              console.log(`- 标签【${selectedTag}】是否匹配：`, match);
              return match;
            });
  
            return isMatch;
          });
          console.log('筛选完成，匹配到', filteredList.length, '张卡片');
        }
  
        // 更新筛选结果
        this.setData({
          selectedTags: newSelectedTags,
          filteredList
        });
      },

    goToAlllist() {
      wx.showToast({ title: '校内公众号一览', icon: 'none' });
      wx.navigateTo({ url: '/pages/campus-all/campus-all' });
    },

        // 跳转到首页（Tab 切换）
        goToHome() {
          wx.showToast({ title: '跳转到首页页面', icon: 'none' });
          wx.switchTab({ url: '/pages/home/home' }); // 替换为 switchTab
        },
        
        // 跳转到自选页面（Tab 切换）
        goToSelection() {
          wx.showToast({ title: '跳转到自选页面', icon: 'none' });
          wx.switchTab({ url: '/pages/selection/selection' }); // 替换为 switchTab
        },
        
        // 跳转到我的页面（Tab 切换）
        goToUser() {
          wx.showToast({ title: '跳转到我的页面', icon: 'none' });
          wx.switchTab({ url: '/pages/user/user' }); // 替换为 switchTab
        }
      
  }
});