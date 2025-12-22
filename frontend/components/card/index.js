const request = require('../../utils/request');

Component({
  options: {
    addGlobalClass: true,
  },
  properties: {
    id_: Number, // 文章唯一ID
    title: String, // 文章标题
    time: String, // 发布时间
    tags: { // Array默认空数组
      type: Array,
      value: []
    },
    desc: String, // 文章描述
    url: String, // 文章链接
    name: String, // 公众号名称
    key_info: String, // 关键词
    is_favorited: Number, // 是否被收藏
  },
  data: {
    isExpanded: false, // 描述是否展开
    isAnimating: false, // 展开的动画
    showFavTipPopup: false, // 提示弹窗
    showCollectionSelect: false, // 收藏夹选择弹窗
    collectionList: [], // 所有收藏夹列表
    defaultCollection: null, // 默认收藏夹
    currentFavoriteId: '', // 当前收藏ID
    tipTimer: null, // 提示弹窗定时器
    // 待办功能
    showAddTodoModal: false, // 添加待办弹窗显示
    newTodoData: { // 待办数据（仅关联文章ID）
      title: '',
      content: '',
      startTime: '',
      endTime: '',
      status: 0,
      article_id: '' // 仅存文章ID
    },
    // 时间选择器相关
    timeRange: [], // [年,月,日,时,分]
    newTodoStartTimeIndex: [0, 0, 0, 0, 0],
    newTodoEndTimeIndex: [0, 0, 0, 0, 0],
    currentYear: new Date().getFullYear(),
    currentMonth: new Date().getMonth() + 1,
    formattedKeyInfo: ''
  },

  lifetimes: {
    detached() {
      if (this.data.tipTimer) clearTimeout(this.data.tipTimer);
    },
    attached() {
      // 初始化时间选择器
      this.initTimeRange();
      const formattedKeyInfo = this.formatKeyInfo(this.properties.key_info);
      this.setData({
        formattedKeyInfo
      });
    }
  },

  methods: {
    formatKeyInfo(keyInfo) {
      if (!keyInfo || typeof keyInfo !== 'string') {
        return '无';
      }
      return keyInfo.replace(/[\[\]"']/g, '').trim() || '无';
    },

    openWebView(e) {
      const url = e.currentTarget.dataset.url;
      // 对URL进行编码
      const encodedUrl = encodeURIComponent(url);
      console.log(url);
      wx.navigateTo({
        url: `/pages/webview/webview?url=${encodedUrl}`
      });
    },

    // 获取所有收藏夹列表
    async getCollectionList() {
      try {
        console.log('开始获取收藏夹列表');
        const res = await request.getCollections();
        console.log('收藏夹列表返回：', res);
        const collectionList = res.list || res;
        const validList = Array.isArray(collectionList) ? collectionList : [];
        const defaultCollection = validList.find(item => item.is_default);
        this.setData({
          collectionList: validList,
          defaultCollection
        });
        console.log('收藏夹列表设置完成：', {
          validList,
          defaultCollection
        });
        // 无默认收藏夹时提示（不清楚是否会正常创建默认收藏夹）
        if (!defaultCollection) {
          wx.showToast({
            title: '未找到默认收藏夹',
            icon: 'none'
          });
        }
      } catch (err) {
        console.error('获取收藏夹列表失败：', err);
        wx.showToast({
          title: '获取收藏夹失败',
          icon: 'none'
        });
      }
    },

    // 收藏/取消收藏逻辑（对接 POST /api/user/favorites/ 和 DELETE /api/user/favorites/{id}/）
    async onFavourite() {
      const articleId = this.properties.id_;
      console.log(articleId);
      if (!articleId) {
        wx.showToast({
          title: '操作失败：文章ID无效',
          icon: 'none'
        });
        return;
      }
      try {
        if (this.properties.is_favorited) {
          // 取消收藏：调用 DELETE 接口
          this.setData({
            animateStar: true
          });
          await request.deleteFavourite(this.properties.is_favorited);
          this.setData({
            is_favorited: 0
          });
          wx.showToast({
            title: '取消收藏成功'
          });
          setTimeout(() => {
            this.setData({
              animateStar: false
            });
          }, 300);
        } else {
          // 添加收藏：调用 POST 接口
          const articleData = {
            article_id: articleId,
            // 关联默认收藏夹（如果接口支持）
            collection_id: this.data.defaultCollection ? this.data.defaultCollection.id : '' // 修复可选链
          };
          this.setData({
            animateStar: true
          });
          const response = await request.addFavourite(articleData);
          this.setData({
            is_favorited: response.id,
            currentFavoriteId: response.id // 记录收藏ID，用于后续移动
          });
          this.showFavTipPopup();
          setTimeout(() => {
            this.setData({
              animateStar: false
            });
          }, 300);
        }
      } catch (err) {
        console.error('收藏操作失败：', err);
        wx.showToast({
          title: err || '操作失败',
          icon: 'none'
        });
      }
    },

    // 显示收藏提示弹窗
    showFavTipPopup() {
      // 清理原有定时器
      if (this.data.tipTimer) clearTimeout(this.data.tipTimer);

      this.setData({
        showFavTipPopup: true,
        showCollectionSelect: false // 关闭收藏夹弹窗
      });

      // 通知父组件收藏操作开始
      this.triggerEvent('collectionOperationStart');

      // 3秒后自动关闭
      const timer = setTimeout(() => {
        // 只有在没有打开收藏夹选择弹窗时才通知操作结束
        if (!this.data.showCollectionSelect) {
          this.setData({
            showFavTipPopup: false
          });
          // 通知父组件收藏操作结束
          this.triggerEvent('collectionOperationEnd');
        }
      }, 3000);
      this.setData({
        tipTimer: timer
      });
    },

    // 打开收藏夹选择弹窗
    openCollectionSelect() {
      this.getCollectionList();
      // 清理定时器
      if (this.data.tipTimer) {
        clearTimeout(this.data.tipTimer);
        this.setData({
          tipTimer: null
        });
      }
      // 关闭提示弹窗，显示收藏夹选择弹窗
      this.setData({
        showFavTipPopup: false,
        showCollectionSelect: true
      });
      // 通知父组件收藏操作开始
      this.triggerEvent('collectionOperationStart');
    },

    // 关闭所有弹窗
    closeAllPopups() {
      if (this.data.tipTimer) {
        clearTimeout(this.data.tipTimer);
        this.setData({
          tipTimer: null
        });
      }
      this.setData({
        showFavTipPopup: false,
        showCollectionSelect: false
      });
      // 通知父组件收藏操作结束
      this.triggerEvent('collectionOperationEnd');
    },

    // 移动收藏到指定收藏夹
    async moveFavouriteToCollection(e) {
      const targetCollectionId = e.currentTarget.dataset.collectionid;
      const {
        currentFavoriteId
      } = this.data;
      console.log('移动收藏', {
        currentFavoriteId,
        targetCollectionId,
        targetType: typeof targetCollectionId,
        collectionList: this.data.collectionList.map(item => item.id)
      });
      if (!currentFavoriteId || !targetCollectionId) {
        wx.showToast({
          title: '参数错误',
          icon: 'none'
        });
        return;
      }

      try {
        wx.showLoading({
          title: '移动中...'
        });
        // 调用移动收藏接口
        await request.moveFavourite(currentFavoriteId, targetCollectionId);
        wx.hideLoading();
        wx.showToast({
          title: '移动成功'
        });
        // 关闭所有弹窗
        this.closeAllPopups();
      } catch (err) {
        wx.hideLoading();
        console.error('移动收藏失败：', err);
        wx.showToast({
          title: err || '移动失败',
          icon: 'none'
        });
        // 即使失败也关闭弹窗并通知父组件
        this.closeAllPopups();
      }
    },

    async onExpand() {
      const newExpanded = !this.data.isExpanded;

      // 开始动画
      this.setData({
        isAnimating: true,
      });

      // 如果是收起操作，先隐藏文字
      if (!newExpanded) {
        this.setData({
          isExpanded: newExpanded // 立即更新展开状态，触发收起动画
        });
      } else {
        // 如果是展开操作，先更新状态再记录历史
        this.setData({
          isExpanded: newExpanded
        });

        const articleId = this.properties.id_;
        if (!articleId) {
          wx.showToast({
            title: '记录失败：文章ID无效',
            icon: 'none'
          });
          return;
        }
        try {
          // 添加历史记录：调用 POST 接口
          const historyData = {
            article_id: articleId,
          };
          await request.addHistory(historyData);
        } catch (err) {
          console.error('添加历史记录失败：', err);
          wx.showToast({
            title: err || '记录失败',
            icon: 'none'
          });
        }
      }

      // 动画结束后清除动画状态
      setTimeout(() => {
        this.setData({
          isAnimating: false
        });
      }, 400); // 与CSS动画时间匹配
    },

    // 1. 初始化时间选择器（和Calendar完全一致）
    initTimeRange() {
      const now = new Date();
      const year = now.getFullYear();
      const month = now.getMonth() + 1;

      const yearList = [year - 2, year - 1, year, year + 1, year + 2].map(y => `${y}年`);
      const monthList = Array.from({
        length: 12
      }, (_, i) => `${i + 1}月`);
      const dayList = Array.from({
        length: new Date(year, month, 0).getDate()
      }, (_, i) => `${i + 1}日`);
      const hourList = Array.from({
        length: 24
      }, (_, i) => `${String(i).padStart(2, '0')}时`);
      const minuteList = Array.from({
        length: 60
      }, (_, i) => `${String(i).padStart(2, '0')}分`);

      this.setData({
        timeRange: [yearList, monthList, dayList, hourList, minuteList],
        currentYear: year,
        currentMonth: month
      });
    },

    // 2. 生成当前时间字符串（和Calendar完全一致）
    getCurrentTimeStr(isEnd = false) {
      const now = new Date();
      if (isEnd) now.setMinutes(now.getMinutes() + 1);
      return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')} ${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}`;
    },

    // 3. 时间字符串转选择器索引（修复可选链语法）
    getTimeIndexByStr(timeStr) {
      const timeRange = this.data.timeRange; // 先取数据，避免链式调用
      if (!timeStr || typeof timeStr !== 'string') return [0, 0, 0, 0, 0];

      const [datePart = '', timePart = ''] = timeStr.split(' ');
      const [year = 0, month = 0, day = 0] = datePart.split('-').map(Number);
      const [hour = 0, minute = 0] = timePart.split(':').map(Number);

      // 修复可选链：用条件判断替代?.
      const yearIndex = timeRange[0] ? timeRange[0].findIndex(item => item === `${year}年`) : 0;
      const monthIndex = timeRange[1] ? timeRange[1].findIndex(item => item === `${month}月`) : 0;
      const dayIndex = timeRange[2] ? timeRange[2].findIndex(item => item === `${day}日`) : 0;
      const hourIndex = timeRange[3] ? timeRange[3].findIndex(item => item === `${String(hour).padStart(2, '0')}时`) : 0;
      const minuteIndex = timeRange[4] ? timeRange[4].findIndex(item => item === `${String(minute).padStart(2, '0')}分`) : 0;

      return [
        yearIndex || 0,
        monthIndex || 0,
        dayIndex || 0,
        hourIndex || 0,
        minuteIndex || 0
      ];
    },

    // 4. 修复：时间选择器列切换（从dataset取type）
    handleTimeColumnChange(e) {
      const type = e.currentTarget.dataset.type; // 从dataset获取type
      if (!type) return; // 无type直接返回
      const {
        column,
        value
      } = e.detail;
      const indexKey = type === 'start' ? 'newTodoStartTimeIndex' : 'newTodoEndTimeIndex';
      const {
        timeRange,
        currentYear,
        currentMonth
      } = this.data;
      const index = this.data[indexKey]; // 先取索引

      if (!timeRange.length) return;
      const newIndex = [...index];
      newIndex[column] = value;
      let newTimeRange = JSON.parse(JSON.stringify(timeRange));

      if (column === 0 || column === 1) {
        const targetYear = column === 0 ? parseInt(newTimeRange[0][value]) : currentYear;
        const targetMonth = column === 1 ? parseInt(newTimeRange[1][value]) : currentMonth;
        const validMonth = Math.max(1, Math.min(12, targetMonth));
        const dayCount = new Date(targetYear, validMonth, 0).getDate();
        newTimeRange[2] = Array.from({
          length: dayCount
        }, (_, i) => `${i + 1}日`);
        newIndex[2] = Math.min(newIndex[2], newTimeRange[2].length - 1);
        this.setData({
          currentYear: targetYear,
          currentMonth: validMonth
        });
      }

      this.setData({
        timeRange: newTimeRange,
        [indexKey]: newIndex
      });
    },

    // 确认时间选择
    confirmTime(e) {
      const type = e.currentTarget.dataset.type; // 从dataset获取type
      if (!type) return;
      const {
        value
      } = e.detail;
      const {
        timeRange
      } = this.data;
      const timeKey = type === 'start' ? 'startTime' : 'endTime';

      if (!timeRange[0] || !timeRange[1] || !timeRange[2] || !timeRange[3] || !timeRange[4]) {
        wx.showToast({
          title: '时间选择异常',
          icon: 'none'
        });
        return;
      }

      const year = timeRange[0][value[0]].replace('年', '');
      const month = String(timeRange[1][value[1]].replace('月', '')).padStart(2, '0');
      const day = String(timeRange[2][value[2]].replace('日', '')).padStart(2, '0');
      const hour = timeRange[3][value[3]].replace('时', '');
      const minute = timeRange[4][value[4]].replace('分', '');
      const timeStr = `${year}-${month}-${day} ${hour}:${minute}`;

      this.setData({
        [`newTodoData.${timeKey}`]: timeStr,
        [type === 'start' ? 'newTodoStartTimeIndex' : 'newTodoEndTimeIndex']: value
      });
    },

    // 6. 打开添加待办弹窗（仅新增文章ID赋值）
    handleAddTodo() {
      const articleId = this.properties.id_;
      if (!articleId) {
        wx.showToast({
          title: '文章ID无效',
          icon: 'none'
        });
        return;
      }
      // 初始化待办数据（和Calendar一致，仅关联文章ID）
      const startTime = this.getCurrentTimeStr();
      const endTime = this.getCurrentTimeStr(true);
      this.setData({
        showAddTodoModal: true,
        newTodoData: {
          title: '',
          content: '',
          startTime,
          endTime,
          status: 0,
          article_id: articleId // 仅传递文章ID
        },
        newTodoStartTimeIndex: this.getTimeIndexByStr(startTime),
        newTodoEndTimeIndex: this.getTimeIndexByStr(endTime)
      });
    },

    // 7. 关闭添加待办弹窗（和Calendar完全一致）
    closeAddTodoModal() {
      this.setData({
        showAddTodoModal: false
      });
    },

    // 8. 核心修复：输入待办标题/内容（从dataset取type + 去空格）
    inputTodoData(e) {
      const type = e.currentTarget.dataset.type; // 从dataset获取type
      const value = e.detail.value.trim(); // 去除首尾空格
      console.log(`输入${type}：`, value); // 调试日志
      if (!type) return; // 无type直接返回
      this.setData({
        [`newTodoData.${type}`]: value
      }, () => {
        // 确认数据更新
        console.log('newTodoData更新后：', this.data.newTodoData);
      });
    },

    // 9. 确认添加待办（修复标题校验 + 调试日志）
    handleAddTodoConfirm() {
      const {
        newTodoData
      } = this.data;
      // 调试：打印完整数据，确认标题是否真的有值
      console.log('确认添加待办，当前数据：', newTodoData);

      // 修复：标题去空格后校验
      const title = newTodoData.title ? newTodoData.title.trim() : '';
      if (!title) {
        return wx.showToast({
          title: '标题不能为空',
          icon: 'none'
        });
      }
      if (!newTodoData.startTime) {
        return wx.showToast({
          title: '请选择开始时间',
          icon: 'none'
        });
      }
      if (!newTodoData.endTime) {
        return wx.showToast({
          title: '请选择结束时间',
          icon: 'none'
        });
      }

      // 时间校验（和Calendar完全一致）
      const parseTimeStr = (timeStr) => {
        if (!timeStr) return null;
        const date = new Date(timeStr.replace('T', ' '));
        return isNaN(date.getTime()) ? null : date;
      };
      const startTime = parseTimeStr(newTodoData.startTime);
      const endTime = parseTimeStr(newTodoData.endTime);
      if (!startTime || !endTime) {
        return wx.showToast({
          title: '时间格式错误',
          icon: 'none'
        });
      }
      if (startTime >= endTime) {
        return wx.showToast({
          title: '结束时间需晚于开始时间',
          icon: 'none'
        });
      }

      // 请求参数（和Calendar一致 + 新增article_id）
      const requestData = {
        title: title, // 使用去空格后的标题
        note: newTodoData.content ? newTodoData.content.trim() : "",
        start_time: newTodoData.startTime + ":00",
        end_time: newTodoData.endTime + ":00",
        remind: true,
        status: newTodoData.status,
        article: newTodoData.article_id // 仅传递文章ID
      };

      console.log('待办请求参数：', requestData); // 调试日志

      // 调用添加待办接口（和Calendar一致）
      request.addTodo(requestData).then(() => {
        wx.showToast({
          title: '创建成功',
          icon: 'success'
        });
        this.closeAddTodoModal();
      }).catch(err => {
        console.error('创建待办失败：', err);
        wx.showToast({
          title: `创建失败：${err}`,
          icon: 'none'
        });
      });
    },

    stopPropagation() {}
  }
});