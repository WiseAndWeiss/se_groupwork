const { getArticleDetail } = require('../../utils/request.js'); 

Component({
    properties: {
      todoData: {
        type: Object,
        value: {
          id: '',
          title: '',
          content: '',
          startTime: '', // 格式：YYYY-MM-DD HH:MM
          endTime: '',   // 格式：YYYY-MM-DD HH:MM
          status: 0,     // 0=未完成，1=已完成
          createTime: '',
          updateTime: '',
          articleid: ''
        },
        observer(newVal) {
          // 1. 先更新临时数据，兜底空值
          const tempData = {
            id: newVal.id || '',
            title: newVal.title || '',
            content: newVal.content || '',
            startTime: newVal.startTime || '',
            endTime: newVal.endTime || '',
            status: newVal.status || 0,
            createTime: newVal.createTime || '',
            updateTime: newVal.updateTime || '',
            articleid: newVal.articleid || ''
          };
          this.setData({ tempData });

          if (newVal.articleid && newVal.articleid !== '') {
            this.loadArticleDetail(newVal.articleid);
          } else {
            this.setData({ articleInfo: null }); // 无ID则清空文章信息
          }
  
          // 暂存需要初始化的时间，等待timeRange初始化完成后再处理
          this.waitForTimeRangeInit(() => {
            if (newVal.startTime) this.setTimeIndex('start', newVal.startTime);
            if (newVal.endTime) this.setTimeIndex('end', newVal.endTime);
          });
        }
      }
    },
  
    data: {
      showModal: false,
      isEdit: false,
      tempData: { // 初始化tempData，和todoData默认值对齐
        id: '',
        title: '',
        content: '',
        startTime: '',
        endTime: '',
        status: 0,
        createTime: '',
        updateTime: '',
        articleid:''
      },
      // 时间选择器：[年份列表, 月份列表, 日期列表, 小时列表, 分钟列表]
      timeRange: [],
      startTimeIndex: [0, 0, 0, 0, 0], // 开始时间各列选中索引
      endTimeIndex: [0, 0, 0, 0, 0],   // 结束时间各列选中索引
      currentYear: new Date().getFullYear(),
      currentMonth: new Date().getMonth() + 1,
      articleInfo: null, // 存储关联文章信息
      articleLoading: false // 文章加载状态
    },
  
    attached() {
      // 标记timeRange已初始化
      this.setData({ timeRangeInited: false });
      // 初始化时间选择器选项
      this.initTimeRange();
      // 初始化完成后标记状态
      this.setData({ timeRangeInited: true });
      // 执行暂存的时间初始化逻辑
      if (this.pendingTimeIndexTasks && this.pendingTimeIndexTasks.length) {
        this.pendingTimeIndexTasks.forEach(task => task());
        this.pendingTimeIndexTasks = [];
      }
    },
  
    methods: {
    openArticleUrl() {
    const { articleInfo } = this.data;
    // 1. 打印链接日志（核心需求）
    console.log('【关联文章跳转】当前点击的链接：', articleInfo.article_url);
    
    // 2. 校验链接有效性
    if (!articleInfo.article_url) {
      wx.showToast({ title: '文章链接为空', icon: 'none' });
      return;
    }
    
    // 3. 手动跳转（避免navigator的默认行为，更易控制）
    wx.navigateTo({
      url: `/pages/webview/webview?url=${encodeURIComponent(articleInfo.article_url)}`,
      fail: (err) => {
        console.error('【关联文章跳转失败】', err);
        wx.showToast({ title: '跳转失败', icon: 'none' });
      }
    });
  },

    // 加载文章详情
    loadArticleDetail(articleId) {
        if (!articleId) return;
        this.setData({ articleLoading: true });
        getArticleDetail(articleId)
          .then(res => {
            this.setData({
                articleInfo: { 
                  title: res.title || '无标题',
                  article_url: res.article_url || '' // 后端返回的文章链接字段
                }, 
                articleLoading: false
              });
          })
          .catch(err => {
            console.error('加载文章失败：', err);
            this.setData({
              articleInfo: { error: '文章加载失败' },
              articleLoading: false
            });
          });
      },
    
      // 等待timeRange初始化完成的工具方法
      waitForTimeRangeInit(callback) {
        if (this.data.timeRangeInited && this.data.timeRange.length > 0) {
          callback();
        } else {
          if (!this.pendingTimeIndexTasks) this.pendingTimeIndexTasks = [];
          this.pendingTimeIndexTasks.push(callback);
        }
      },
  
      // 初始化时间选择器的选项列表
      initTimeRange() {
        const now = new Date();
        const year = now.getFullYear();
        const month = now.getMonth() + 1;
  
        // 1. 年份选项（最近5年）
        const yearList = [year - 2, year - 1, year, year + 1, year + 2].map(y => `${y}年`);
        // 2. 月份选项（1-12月）
        const monthList = Array.from({ length: 12 }, (_, i) => `${i + 1}月`);
        // 3. 日期选项（根据当前年月动态生成）
        const dayList = this.getDayList(year, month);
        // 4. 小时选项（00-23时）
        const hourList = Array.from({ length: 24 }, (_, i) => `${i.toString().padStart(2, '0')}时`);
        // 5. 分钟选项（00-59分）
        const minuteList = Array.from({ length: 60 }, (_, i) => `${i.toString().padStart(2, '0')}分`);
  
        this.setData({
          timeRange: [yearList, monthList, dayList, hourList, minuteList],
          currentYear: year,
          currentMonth: month
        });
      },
  
      // 根据年份和月份，获取当月的日期列表
      getDayList(year, month) {
        const days = new Date(year, month, 0).getDate(); // 获取当月天数
        return Array.from({ length: days }, (_, i) => `${i + 1}日`);
      },
  
      // 将已有时间字符串转换为选择器索引
      setTimeIndex(type, timeStr) {
        if (!timeStr || typeof timeStr !== 'string') return;
        
        const { timeRange } = this.data;
        // 核心校验：确保timeRange已初始化且各列存在
        if (!timeRange || timeRange.length < 5) {
          console.warn('timeRange未初始化完成，跳过时间索引设置');
          return;
        }
  
        // 解析时间：兼容 T/空格 分隔符
        const timeStrNormalized = timeStr.replace('T', ' ');
        const [datePart, timePart] = timeStrNormalized.split(' ');
        if (!datePart || !timePart) return;
  
        const [year, month, day] = datePart.split('-').map(Number);
        const [hour, minute] = timePart.split(':').map(Number);
  
        // 匹配各列的索引（加可选链+兜底，避免undefined）
        const yearIndex = timeRange[0]?.findIndex(item => item === `${year}年`) ?? 0;
        const monthIndex = timeRange[1]?.findIndex(item => item === `${month}月`) ?? 0;
        const dayIndex = timeRange[2]?.findIndex(item => item === `${day}日`) ?? 0;
        const hourIndex = timeRange[3]?.findIndex(item => item === `${hour.toString().padStart(2, '0')}时`) ?? 0;
        const minuteIndex = timeRange[4]?.findIndex(item => item === `${minute.toString().padStart(2, '0')}分`) ?? 0;
  
        // 更新对应时间的索引
        const indexKey = type === 'start' ? 'startTimeIndex' : 'endTimeIndex';
        this.setData({
          [indexKey]: [
            yearIndex > -1 ? yearIndex : 0,
            monthIndex > -1 ? monthIndex : 0,
            dayIndex > -1 ? dayIndex : 0,
            hourIndex > -1 ? hourIndex : 0,
            minuteIndex > -1 ? minuteIndex : 0
          ]
        });
      },
  
      // 开始时间：列切换事件（动态更新日期）
      handleStartTimeColumnChange(e) {
        const { column, value } = e.detail;
        const { timeRange, startTimeIndex, currentYear, currentMonth } = this.data;
        if (!timeRange.length) return; // 加校验
  
        const newIndex = [...startTimeIndex];
        newIndex[column] = value;
        let newTimeRange = [...timeRange];
  
        // 年份切换：更新日期列表
        if (column === 0) {
          const newYear = parseInt(newTimeRange[0][value]);
          newTimeRange[2] = this.getDayList(newYear, currentMonth);
          newIndex[2] = Math.min(newIndex[2], newTimeRange[2].length - 1); // 防止日期越界
          this.setData({ currentYear: newYear });
        }
  
        // 月份切换：更新日期列表
        if (column === 1) {
          const newMonth = parseInt(newTimeRange[1][value]);
          newTimeRange[2] = this.getDayList(currentYear, newMonth);
          newIndex[2] = Math.min(newIndex[2], newTimeRange[2].length - 1); // 防止日期越界
          this.setData({ currentMonth: newMonth });
        }
  
        this.setData({ timeRange: newTimeRange, startTimeIndex: newIndex });
      },
  
      // 开始时间：确认选择（组合为YYYY-MM-DD HH:MM）
      handleStartTimeConfirm(e) {
        const { value } = e.detail;
        const { timeRange } = this.data;
        if (!timeRange.length) return; // 加校验
  
        // 解析各列值
        const year = timeRange[0][value[0]].replace('年', '');
        const month = timeRange[1][value[1]].replace('月', '').padStart(2, '0');
        const day = timeRange[2][value[2]].replace('日', '').padStart(2, '0');
        const hour = timeRange[3][value[3]].replace('时', '');
        const minute = timeRange[4][value[4]].replace('分', '');
        // 组合为目标格式
        const timeStr = `${year}-${month}-${day} ${hour}:${minute}`;
        this.setData({ 'tempData.startTime': timeStr, startTimeIndex: value });
      },
  
      // 结束时间：列切换事件（逻辑同开始时间）
      handleEndTimeColumnChange(e) {
        const { column, value } = e.detail;
        const { timeRange, endTimeIndex, currentYear, currentMonth } = this.data;
        if (!timeRange.length) return; // 加校验
  
        const newIndex = [...endTimeIndex];
        newIndex[column] = value;
        let newTimeRange = [...timeRange];
  
        if (column === 0) {
          const newYear = parseInt(newTimeRange[0][value]);
          newTimeRange[2] = this.getDayList(newYear, currentMonth);
          newIndex[2] = Math.min(newIndex[2], newTimeRange[2].length - 1);
          this.setData({ currentYear: newYear });
        }
  
        if (column === 1) {
          const newMonth = parseInt(newTimeRange[1][value]);
          newTimeRange[2] = this.getDayList(currentYear, newMonth);
          newIndex[2] = Math.min(newIndex[2], newTimeRange[2].length - 1);
          this.setData({ currentMonth: newMonth });
        }
  
        this.setData({ timeRange: newTimeRange, endTimeIndex: newIndex });
      },
  
      // 结束时间：确认选择（组合为YYYY-MM-DD HH:MM）
      handleEndTimeConfirm(e) {
        const { value } = e.detail;
        const { timeRange } = this.data;
        if (!timeRange.length) return; // 加校验
  
        const year = timeRange[0][value[0]].replace('年', '');
        const month = timeRange[1][value[1]].replace('月', '').padStart(2, '0');
        const day = timeRange[2][value[2]].replace('日', '').padStart(2, '0');
        const hour = timeRange[3][value[3]].replace('时', '');
        const minute = timeRange[4][value[4]].replace('分', '');
        const timeStr = `${year}-${month}-${day} ${hour}:${minute}`;
        this.setData({ 'tempData.endTime': timeStr, endTimeIndex: value });
      },
  
      // 原有方法（保留+优化）
      showModal() { this.setData({ showModal: true, isEdit: false }); },
      hideModal() { this.resetModal(); },
      stopPropagation() {},
      handleExit() { this.resetModal(); },
      handleEdit() { this.setData({ isEdit: true }); },
      handleSave() {
        const { tempData } = this.data;
        if (!tempData.title) { wx.showToast({ title: '标题不能为空', icon: 'none' }); return; }
        if (!tempData.startTime) { wx.showToast({ title: '请选择开始时间', icon: 'none' }); return; }
        if (!tempData.endTime) { wx.showToast({ title: '请选择结束时间', icon: 'none' }); return; }
        // 兼容时间格式转换
        const startTime = new Date(tempData.startTime.replace(' ', 'T'));
        const endTime = new Date(tempData.endTime.replace(' ', 'T'));
        if (isNaN(startTime.getTime()) || isNaN(endTime.getTime())) {
          wx.showToast({ title: '时间格式错误', icon: 'none' });
          return;
        }
        if (startTime >= endTime) {
          wx.showToast({ title: '结束时间需晚于开始时间', icon: 'none' });
          return;
        }
        this.triggerEvent('updateTodo', { todoData: tempData });
        this.resetModal();
        wx.showToast({ title: '修改成功', icon: 'success' });
      },
      handleDelete() {
        const { todoData } = this.properties;
        wx.showModal({
          title: '提示',
          content: '确定删除该待办吗？',
          success: (res) => {
            if (res.confirm) {
              this.triggerEvent('deleteTodo', { todoId: todoData.id });
              this.setData({ showModal: false });
              wx.showToast({ title: '删除成功', icon: 'success' });
            }
          }
        });
      },
      resetModal() {
        this.setData({
          showModal: false,
          isEdit: false,
          tempData: { ...this.properties.todoData }
        });
      },
      handleTitleInput(e) { this.setData({ 'tempData.title': e.detail.value }); },
      handleContentInput(e) { this.setData({ 'tempData.content': e.detail.value }); }
    }
  });