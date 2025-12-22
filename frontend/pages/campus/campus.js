const request = require('../../utils/request');

Page({
  data: {
    selectionList: [], // 从接口获取的数据
    filteredList: [], // 筛选后数据
    isFilterShow: false,
    isLoading: false, // 加载状态
    start_rank: 0, // 分页偏移量
    reach_end: false, // 是否已加载完所有数据
    scrollTop: 0, // 控制 article-list 滚动位置
    outerSearchContent: '', // 外部搜索栏当前输入内容
    lastOuterSearchContent: '', // 记忆上一次外部搜索的内容
    innerSearchContent: '', // 悬浮窗内搜索内容
    currentCategory: 'time', // 当前选中的类目（默认时间）
    showLoadingAnimation: false,
    isSelected: false,
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
    otherTags: ["其他"],
    currentDate: new Date().toISOString().slice(0, 10), // 初始化当前日期
    emptyTip: '暂无匹配标签的动态' // 新增：动态空提示文本
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
    this.setData({
      scrollTop: 0
    });
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
      filteredList: [], // 筛选后数据
      isFilterShow: false,
      outerSearchContent: '',
      lastOuterSearchContent: '',
      innerSearchContent: '',
      isLoading: false, // 加载状态
      start_rank: 0, // 分页偏移量
      reach_end: false, // 是否已加载完所有数据
      currentCategory: 'time',
      emptyTip: '暂无匹配标签的动态'
    });
  },

  // 切换类目
  switchCategory(e) {
    const category = e.currentTarget.dataset.category;
    this.setData({
      currentCategory: category
    });
  },

  // 重置筛选
  resetFilters() {
    this.setData({
      // 清空临时标签
      tempSelectedFilters: {
        type: [],
        account: [],
        content: [],
        other: []
      },
      // 重置时间筛选
      timeFilter: {
        start: '',
        end: ''
      },
      // 清空悬浮窗内搜索内容
      innerSearchContent: ''
    });
  },

  // 显示悬浮窗
  showFilterPopup() {
    // 打开时将最终筛选条件复制到临时存储
    const tempSelected = JSON.parse(JSON.stringify(this.data.selectedFilters));
    this.setData({
      isFilterShow: true,
      tempSelectedFilters: tempSelected // 临时存储继承当前已选状态
    });
  },

  // 隐藏悬浮窗：清空临时标签，放弃本次修改
  hideFilterPopup() {
    this.setData({
      // 清空临时标签
      tempSelectedFilters: {
        type: [],
        account: [],
        content: [],
        other: []
      },
      // 重置时间筛选
      timeFilter: {
        start: '',
        end: ''
      },
      // 清空悬浮窗内搜索内容
      innerSearchContent: '',
      isFilterShow: false
    });
  },

  handleLoadMore() {
    console.log('父页面接收到加载更多事件');
    if (this.data.isSelected) {
      // 加载更多时根据当前搜索类型继续请求
      if (this.data.lastSearchType === 'outer') {
        // 外部搜索加载更多：强制使用记忆的关键词，而非当前输入框内容
        this.searchByOuterInput(false);
      } else if (this.data.lastSearchType === 'filter') {
        this.searchByFilter(false);
      }
    } else {
      this.loadCampusArticles(false);
    }
  },

  // 加载校园最新文章（默认初始加载）
  async loadCampusArticles(reset = false) {
    if (this.data.isLoading) return;
    console.log('开始加载校园文章...');
    this.setData({
      isLoading: true,
      showLoadingAnimation: true
    });
    if (reset) {
      this.setData({
        scrollTop: 0
      });
    };

    try {
      let start_rank = reset ? 0 : this.data.start_rank;
      console.log('请求start_rank:', start_rank);

      const response = await request.getCampusLatestArticles(start_rank);

      if (response) {
        // 处理后端返回的error提示
        if (response.error) {
          if (response.error === '没有找到符合条件的文章') {
            // 置空列表，显示对应提示，标记到底
            this.setData({
              selectionList: [],
              filteredList: [],
              emptyTip: '没有找到符合条件的文章',
              reach_end: true,
              isSelected: false
            });
          } else {
            console.log('数据异常');
          }
        } else if (response.articles) {
          const newArticles = response.articles;
          console.log('本次加载文章数量：', newArticles.length);

          // 处理数据合并/重置
          const finalList = reset ? newArticles : [...this.data.selectionList, ...newArticles];

          // 计算新的start_rank
          const newStartRank = start_rank + (newArticles.length || 10); // 假设pageSize=10

          // 标记是否已到数据末尾
          const reach_end = response.reach_end;

          // 有数据时恢复默认提示
          this.setData({
            selectionList: finalList,
            filteredList: finalList,
            start_rank: newStartRank,
            reach_end: reach_end,
            isSelected: false,
            emptyTip: '暂无匹配标签的动态'
          });
        } else {
          console.warn('接口返回数据格式异常：', response);
        }
      } else {
        console.warn('接口返回空数据');
      }
    } catch (error) {
      console.error('加载校园文章失败：', error);
      this.setData({
        selectionList: [],
        filteredList: [],
        emptyTip: '数据加载失败，请重试'
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
    let value = e.detail.value;

    // 格式化日期为YYYY-MM-DD
    if (value) {
      value = value.replace(/\//g, '-');
      if (!/^\d{4}-\d{2}-\d{2}$/.test(value)) {
        return;
      }
    }

    // 更新对应的时间值
    const newTimeFilter = {
      ...this.data.timeFilter,
      [type]: value
    };

    // 验证时间范围
    const validationResult = this.validateTimeRange(newTimeFilter.start, newTimeFilter.end);
    if (!validationResult.valid) {
      // 验证失败，显示提示但不阻止输入
      wx.showToast({
        title: validationResult.message,
        icon: 'none',
        duration: 2000
      });
      // 如果验证失败，可以选择不更新数据，或者更新后让用户知道
      // 这里选择更新数据，但在提交时会再次验证
    }

    this.setData({
      [`timeFilter.${type}`]: value
    });
  },

  // 验证时间范围
  validateTimeRange(start, end) {
    // 如果两个时间都为空，验证通过
    if (!start && !end) {
      return {
        valid: true,
        message: ''
      };
    }

    // 如果只有起始时间或只有终止时间，验证通过
    if (!start || !end) {
      return {
        valid: true,
        message: ''
      };
    }

    // 验证日期格式
    const datePattern = /^\d{4}-\d{2}-\d{2}$/;
    if (!datePattern.test(start) || !datePattern.test(end)) {
      return {
        valid: false,
        message: '日期格式不正确'
      };
    }

    // 转换为Date对象进行比较
    const startDate = new Date(start);
    const endDate = new Date(end);

    // 验证起始时间不能晚于终止时间
    if (startDate > endDate) {
      return {
        valid: false,
        message: '起始时间不能晚于终止时间'
      };
    }

    return {
      valid: true,
      message: ''
    };
  },

  // 切换标签选中状态 tempSelectedFilters
  toggleTag(e) {
    const {
      category,
      tag
    } = e.currentTarget.dataset;
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

    this.setData({
      tempSelectedFilters: tempSelected
    }, () => {
      console.log(`临时标签更新：${category}类 - ${tag}`, this.data.tempSelectedFilters[category]);
    });
  },

  isFilterParamsEmpty() {
    const {
      innerSearchContent,
      timeFilter,
      tempSelectedFilters
    } = this.data;
    const isSearchEmpty = !innerSearchContent.trim();
    const isTimeEmpty = !timeFilter.start && !timeFilter.end;
    const isTagsEmpty =
      tempSelectedFilters.type.length === 0 &&
      tempSelectedFilters.account.length === 0 &&
      tempSelectedFilters.content.length === 0 &&
      tempSelectedFilters.other.length === 0;

    return isSearchEmpty && isTimeEmpty && isTagsEmpty;
  },

  // 外部搜索
  getOuterSearchParams(reset) {
    const {
      lastOuterSearchContent,
      outerSearchContent
    } = this.data;
    const start_rank = reset ? 0 : this.data.start_rank;
    // 首次搜索reset=true，加载更多reset=false
    const searchContent = reset ? outerSearchContent.trim() : lastOuterSearchContent.trim();

    const params = {
      start_rank
    };
    if (searchContent) {
      params.search_content = searchContent;
    }
    console.log('外部搜索参数（仅内容）：', params);
    return params;
  },

  // 筛选搜索
  getFilterSearchParams(reset) {
    const {
      timeFilter,
      tempSelectedFilters,
      innerSearchContent
    } = this.data;
    const start_rank = reset ? 0 : this.data.start_rank;

    // 初始化
    const params = {
      // 标签参数
      tags: [
        ...tempSelectedFilters.type,
        ...tempSelectedFilters.content,
        ...tempSelectedFilters.other
      ].filter(Boolean),
      account_names: tempSelectedFilters.account.filter(Boolean),
      start_rank
    };

    // 只有内部搜索内容非空时，才添加search_content字段
    const innerSearch = innerSearchContent.trim();
    if (innerSearch) {
      params.search_content = innerSearch;
    }

    // 仅当日期有值时才传入
    if (timeFilter.start) {
      if (/^\d{4}-\d{2}-\d{2}$/.test(timeFilter.start)) {
        params.date_from = timeFilter.start;
      } else {
        console.error('起始日期格式错误:', timeFilter.start);
      }
    }
    if (timeFilter.end) {
      if (/^\d{4}-\d{2}-\d{2}$/.test(timeFilter.end)) {
        params.date_to = timeFilter.end;
      } else {
        console.error('终止日期格式错误:', timeFilter.end);
      }
    }

    console.log('筛选搜索参数（修复后）：', params);
    return params;
  },

  // 外部搜索栏搜索
  async searchByOuterInput(reset = true) {
    // 保存最后搜索类型，用于加载更多
    this.setData({
      lastSearchType: 'outer',
      isSelected: true
    });

    // 首次搜索时（reset=true），清空悬浮窗所有筛选条件
    if (reset) {
      // 清空内部搜索内容
      this.setData({
        scrollTop: 0,
        innerSearchContent: '',
        // 重置临时选中标签
        tempSelectedFilters: {
          type: [],
          account: [],
          content: [],
          other: []
        },
        // 重置已选中标签（确认后的标签）
        selectedFilters: {
          type: [],
          account: [],
          content: [],
          other: []
        },
        // 重置时间筛选
        timeFilter: {
          start: '',
          end: ''
        },
        // 重置当前选中类目为默认的time
        currentCategory: 'time'
      });

      // 首次搜索时，更新记忆的搜索内容
      this.setData({
        lastOuterSearchContent: this.data.outerSearchContent.trim()
      });
    }

    const params = this.getOuterSearchParams(reset);
    // 无search_content时，返回默认列表
    if (!params.search_content) {
      this.setData({
        lastOuterSearchContent: ''
      });
      return this.loadCampusArticles(true);
    }

    this.setData({
      showLoadingAnimation: true,
      isLoading: true
    });

    try {
      const response = await request.getFilteredArticles(params);
      if (response) {
        // 处理后端返回的error
        if (response.error) {
          if (response.error === '没有找到符合条件的文章') {
            this.setData({
              selectionList: [],
              filteredList: [],
              emptyTip: '没有找到符合条件的文章',
              reach_end: true
            });
          } else {
            this.setData({
              selectionList: [],
              filteredList: []
            });
          }
        } else if (response.articles) {
          const newArticles = response.articles;
          const finalList = reset ? newArticles : [...this.data.selectionList, ...newArticles];
          const newStartRank = params.start_rank + (newArticles.length || 10);
          const reach_end = response.reach_end;

          this.setData({
            selectionList: finalList,
            filteredList: finalList,
            start_rank: newStartRank,
            reach_end: reach_end,
            emptyTip: '暂无匹配标签的动态' // 恢复默认提示
          });

          // 即使有articles但长度为0（空结果），也显示对应提示
          if (newArticles.length === 0 && reset) {
            this.setData({
              emptyTip: '没有找到符合条件的文章',
              reach_end: true
            });
          }
        } else {
          this.setData({
            selectionList: [],
            filteredList: [],
            emptyTip: '没有找到符合条件的文章',
            reach_end: true
          });
        }
      } else {
        this.setData({
          selectionList: [],
          filteredList: [],
          emptyTip: '没有找到符合条件的文章',
          reach_end: true
        });
      }
    } catch (error) {
      console.error('外部搜索失败：', error);
      this.setData({
        selectionList: [],
        filteredList: [],
        emptyTip: '搜索失败，请重试'
      });
    } finally {
      this.setData({
        showLoadingAnimation: false,
        isLoading: false
      });
      if (!reset) {
        this.setData({
          outerSearchContent: this.data.lastOuterSearchContent
        });
      }
    }
  },

  // 筛选悬浮窗确定触发的搜索（空条件调用默认加载，清空外部搜索记忆）
  async searchByFilter(reset = true) {
    // 验证时间范围
    const {
      start,
      end
    } = this.data.timeFilter;
    const validationResult = this.validateTimeRange(start, end);
    if (!validationResult.valid) {
      // 验证失败，显示提示并阻止提交
      wx.showToast({
        title: validationResult.message,
        icon: 'none',
        duration: 2000
      });
      return; // 阻止提交
    }

    // 先关闭悬浮窗
    this.setData({
      isFilterShow: false
    });

    // 清空外部搜索内容和记忆（核心需求）
    this.setData({
      outerSearchContent: '',
      lastOuterSearchContent: '',
      lastSearchType: '' // 清空搜索类型记忆
    });
    console.log('内部调用')

    // 1. 判断筛选参数是否为空，空则调用默认加载并置顶
    if (this.isFilterParamsEmpty()) {
      console.log('内部空调用');
      this.loadCampusArticles(true);
      // 重置筛选状态
      this.setData({
        selectedFilters: {
          type: [],
          account: [],
          content: [],
          other: []
        },
        isSelected: false
      });
      return;
    }

    // 2. 非空则执行筛选搜索
    // 保存最后筛选条件到正式状态
    this.setData({
      selectedFilters: JSON.parse(JSON.stringify(this.data.tempSelectedFilters)),
      lastSearchType: 'filter',
      isSelected: true
    });

    const params = this.getFilterSearchParams(reset);
    this.setData({
      showLoadingAnimation: true,
      isLoading: true
    });

    try {
      const response = await request.getFilteredArticles(params);
      if (response) {
        // 处理后端返回的error
        if (response.error) {
          if (response.error === '没有找到符合条件的文章') {
            this.setData({
              selectionList: [],
              filteredList: [],
              emptyTip: '没有找到符合条件的文章',
              reach_end: true
            });
          } else {
            this.setData({
              selectionList: [],
              filteredList: []
            });
          }
        } else if (response.articles) {
          const newArticles = response.articles;
          const finalList = reset ? newArticles : [...this.data.selectionList, ...newArticles];
          const newStartRank = params.start_rank + (newArticles.length || 10);
          const reach_end = response.reach_end;

          this.setData({
            selectionList: finalList,
            filteredList: finalList,
            start_rank: newStartRank,
            reach_end: reach_end,
            emptyTip: '暂无匹配标签的动态'
          });

          // 空结果处理
          if (newArticles.length === 0 && reset) {
            this.setData({
              emptyTip: '没有找到符合条件的文章',
              reach_end: true
            });
          }
        } else {
          this.setData({
            selectionList: [],
            filteredList: [],
            emptyTip: '没有找到符合条件的文章',
            reach_end: true
          });
        }
      } else {
        this.setData({
          selectionList: [],
          filteredList: [],
          emptyTip: '没有找到符合条件的文章',
          reach_end: true
        });
      }
    } catch (error) {
      console.error('筛选搜索失败：', error);
      this.setData({
        selectionList: [],
        filteredList: [],
        emptyTip: '搜索失败，请重试'
      });
    } finally {
      this.setData({
        showLoadingAnimation: false,
        isLoading: false
      });
    }
  },

  // 外部搜索栏输入绑定
  onOuterSearchInput(e) {
    this.setData({
      outerSearchContent: e.detail.value
    });
  },

  // 悬浮窗内搜索输入绑定
  onInnerSearchInput(e) {
    this.setData({
      innerSearchContent: e.detail.value
    });
  },

  // 其他方法
  goToAlllist() {
    this.clearPageData();
    wx.switchTab({
      url: '/pages/campus-all/campus-all'
    });
  },

  goToHome() {
    this.clearPageData();
    wx.switchTab({
      url: '/pages/home/home'
    });
  },

  goToSelection() {
    this.clearPageData();
    wx.switchTab({
      url: '/pages/selection/selection'
    });
  },

  goToUser() {
    this.clearPageData();
    wx.switchTab({
      url: '/pages/user/user'
    });
  }
});