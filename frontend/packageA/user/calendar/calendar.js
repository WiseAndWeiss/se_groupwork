const { getTodos, addTodo, updateTodo, deleteTodo } = require('../../../utils/request.js'); 

Page({
  data: {
    currentView: 'month',
    currentViewTitle: '',
    selectedDate: '',
    todayDate: '',
    weekHeaders: ['一', '二', '三', '四', '五', '六', '日'],
    calendarDateList: [],
    timeAxisList: Array.from({ length: 24 }, (_, i) => ({
      time: `${i.toString().padStart(2, '0')}:00`,
      height: 70
    })),
    scheduleList: [],
    weekScheduleList: [],
    weekScheduleGrouped: {},
    todoList: [], 
    allTodoList: [], 
    showAddTodoModal: false,
    timeRange: [],
    newTodoStartTimeIndex: [0, 0, 0, 0, 0],
    newTodoEndTimeIndex: [0, 0, 0, 0, 0],
    currentYear: new Date().getFullYear(),
    currentMonth: new Date().getMonth() + 1,
    newTodoData: {
      title: '',
      content: '',
      startTime: '', 
      endTime: '',   
      status: 0
    },
    showTodoPopup: false,
    popupData: {},
  },

  onLoad() {
    console.log('===== 【1/7】页面初始化 =====');
    const today = new Date();
    const todayDate = this.formatDate(today);
    this.setData({ 
      todayDate, 
      selectedDate: todayDate
    }, () => {
      console.log('初始化后selectedDate：', this.data.selectedDate);
      this.renderCalendar('month');
      this.loadAllTodoList(() => {
        this.loadTodoList(todayDate);
      });
    });
  },

  // 新增：页面渲染完成后强制检查DOM和数据
  onReady() {
    setTimeout(() => {
      console.log('===== 【关键】页面渲染完成 - 周视图数据检查 =====');
      console.log('weekScheduleGrouped 完整数据：', JSON.stringify(this.data.weekScheduleGrouped, null, 2));
      console.log('weekScheduleList 长度：', this.data.weekScheduleList.length);
      console.log('weekScheduleList 数据：', JSON.stringify(this.data.weekScheduleList, null, 2));
      
      // 查询待办条DOM节点，确认是否渲染
      wx.createSelectorQuery().selectAll('.week-schedule-bar').boundingClientRect(rects => {
        console.log('===== 待办条DOM节点检测 =====');
        console.log('待办条数量：', rects.length);
        if (rects.length === 0) {
          console.log(' 无待办条DOM节点');
        } else {
          console.log('待办条位置信息：', rects);
        }
      }).exec();
    }, 1000);
  },

  loadAllTodoList(callback) {
    console.log('===== 【2/7】加载全量待办 =====');
    getTodos().then(res => {
      console.log('后端返回原始数据：', JSON.stringify(res, null, 2));
      const allTodoList = (res.list || res || []).map((todo, index) => {
        const formatTime = (timeStr) => {
          if (!timeStr || typeof timeStr !== 'string') return '';
          const date = new Date(timeStr.replace('T', ' '));
          if (isNaN(date.getTime())) return '';
          return `${date.getFullYear()}-${String(date.getMonth()+1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')} ${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`;
        };
  
        const formattedTodo = {
          id: todo.id,
          title: todo.title || '',
          content: todo.note || '',
          articleid: todo.article || '',
          startTime: formatTime(todo.start_time),
          endTime: formatTime(todo.end_time),
          status: todo.status || 0,
          createTime: todo.created_at || '',
          updateTime: todo.updated_at || ''
        };
        console.log(`格式化后待办${index}：`, formattedTodo);
        return formattedTodo;
      });
      this.setData({ allTodoList }, () => {
        console.log('全量待办列表长度：', this.data.allTodoList.length);
        if (this.data.currentView === 'all') {
          this.setData({ todoList: allTodoList });
        }
        callback && callback();
      });
    }).catch(err => {
      console.error('加载全量待办失败：', err);
      wx.showToast({ title: '加载待办失败', icon: 'none' });
      this.setData({ allTodoList: [], todoList: [], scheduleList: [], weekScheduleList: [], weekScheduleGrouped: {} });
      callback && callback();
    });
  },

  parseTimeStr(timeStr) {
    if (!timeStr || typeof timeStr !== 'string') return null;
    const normalized = timeStr.replace('T', ' ').trim();
    const date = new Date(normalized);
    if (isNaN(date.getTime())) {
      console.warn(`时间解析失败：${timeStr}`);
      return null;
    }
    return date;
  },

  isSingleDayTodo(todo) {
    const start = this.parseTimeStr(todo.startTime);
    const end = this.parseTimeStr(todo.endTime);
    if (!start || !end) return false;
    const isSameDay = start.getFullYear() === end.getFullYear() &&
                      start.getMonth() === end.getMonth() &&
                      start.getDate() === end.getDate();
    console.log(`待办${todo.id}是否单天：`, isSameDay, 'start：', todo.startTime, 'end：', todo.endTime);
    return isSameDay;
  },

  getWeekDayIndex(dateStr) {
    const date = this.parseTimeStr(dateStr + ' 00:00');
    if (!date) return -1;
    let day = date.getDay(); 
    const index = day === 0 ? 6 : day - 1;
    console.log(`日期${dateStr}在周内索引：`, index);
    return index;
  },

  isDateInTodoRange(dateStr, todo) {
    const todoStart = this.parseTimeStr(todo.startTime);
    const todoEnd = this.parseTimeStr(todo.endTime);
    if (!todoStart || !todoEnd) return false;

    const [year, month, day] = dateStr.split('-').map(Number);
    const targetDateStart = new Date(year, month - 1, day, 0, 0, 0, 0);
    const targetDateEnd = new Date(year, month - 1, day, 23, 59, 59, 999);

    const isInRange = todoStart.getTime() <= targetDateEnd.getTime() && todoEnd.getTime() >= targetDateStart.getTime();
    return isInRange;
  },

  mergeOverlappingTodos(todos) {
    console.log('===== 【3/7】合并重叠待办 =====');
    console.log('合并前待办数量：', todos.length);
    
    if (todos.length === 0) return [];

    const sortedTodos = [...todos].sort((a, b) => a.startTs - b.startTs);
    const mergedItems = [];
    let currentGroup = {
      todos: [sortedTodos[0]],
      startTs: sortedTodos[0].startTs,
      endTs: sortedTodos[0].endTs,
      dayIndex: sortedTodos[0].dayIndex
    };

    for (let i = 1; i < sortedTodos.length; i++) {
      const todo = sortedTodos[i];
      if (todo.startTs <= currentGroup.endTs) {
        currentGroup.todos.push(todo);
        currentGroup.endTs = Math.max(currentGroup.endTs, todo.endTs);
      } else {
        mergedItems.push(this.formatMergedItem(currentGroup));
        currentGroup = {
          todos: [todo],
          startTs: todo.startTs,
          endTs: todo.endTs,
          dayIndex: todo.dayIndex
        };
      }
    }
    mergedItems.push(this.formatMergedItem(currentGroup));

    console.log('合并后待办项数量：', mergedItems.length);
    return mergedItems;
  },

  formatMergedItem(group) {
    const HOUR_HEIGHT_RPX = 70;
    const startDate = new Date(group.startTs);
    const endDate = new Date(group.endTs);
    const startHour = startDate.getHours();
    const startMinute = startDate.getMinutes();
    const durationMs = group.endTs - group.startTs;
    const durationHours = durationMs / (1000 * 60 * 60);
    const minuteOffsetRpx = startMinute * (HOUR_HEIGHT_RPX / 60);
    let heightRpx = durationHours * HOUR_HEIGHT_RPX;

    

    let item = {};
    if (group.todos.length === 1) {
      const todo = group.todos[0];
      item = {
        type: 'single',
        id: todo.id,
        groupId: `single-${todo.id}`,
        dayIndex: group.dayIndex,
        title: todo.title,
        todoCount: 1,
        startHour: startHour,
        startMinute: startMinute,
        durationHours: durationHours,
        minuteOffset: minuteOffsetRpx,
        height: heightRpx,
        startTime: todo.startTime,
        endTime: todo.endTime,
        content: todo.content,
        todos: group.todos
      };
    } else {
      item = {
        type: 'group',
        groupId: `group-${group.dayIndex}-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
        dayIndex: group.dayIndex,
        title: `当前时段有${group.todos.length}个待办`,
        todoCount: group.todos.length,
        startHour: startHour,
        startMinute: startMinute,
        durationHours: durationHours,
        minuteOffset: minuteOffsetRpx,
        height: heightRpx,
        startTime: `${startDate.getFullYear()}-${String(startDate.getMonth()+1).padStart(2, '0')}-${String(startDate.getDate()).padStart(2, '0')} ${String(startHour).padStart(2, '0')}:${String(startMinute).padStart(2, '0')}`,
        endTime: `${endDate.getFullYear()}-${String(endDate.getMonth()+1).padStart(2, '0')}-${String(endDate.getDate()).padStart(2, '0')} ${String(endDate.getHours()).padStart(2, '0')}:${String(endDate.getMinutes()).padStart(2, '0')}`,
        todos: group.todos
      };
    }
    return item;
  },

  handleYearNavClick(e) {
    const type = e.currentTarget.dataset.type;
    this.changeYear(type);
  },

  prevMonth() {
    this.changeMonth('prev');
  },
  nextMonth() {
    this.changeMonth('next');
  },
  handleNewTodoTitleInput(e) {
    this.inputTodoData(e, 'title');
  },
  handleNewTodoContentInput(e) {
    this.inputTodoData(e, 'content');
  },
  handleNewTodoStartTimeColumnChange(e) {
    this.handleTimeColumnChange(e, 'start');
  },
  handleNewTodoEndTimeColumnChange(e) {
    this.handleTimeColumnChange(e, 'end');
  },
  handleNewTodoStartTimeConfirm(e) {
    this.confirmTime(e, 'start');
  },
  handleNewTodoEndTimeConfirm(e) {
    this.confirmTime(e, 'end');
  },
  stopPropagation() {},

  changeYear(type) {
    const currentDate = new Date(this.data.selectedDate);
    currentDate.setFullYear(currentDate.getFullYear() + (type === 'prev' ? -1 : 1));
    const newDate = this.formatDate(currentDate);
    this.setData({ selectedDate: newDate }, () => {
      this.renderCalendar('year');
      this.loadTodoList(newDate);
    });
  },

  handleYearMonthClick(e) {
    const month = e.currentTarget.dataset.month; 
    const currentYear = new Date(this.data.selectedDate).getFullYear(); 
    const targetDate = this.formatDate(new Date(currentYear, month - 1, 1));
    this.setData({
      currentView: 'month',
      selectedDate: targetDate
    }, () => {
      this.renderCalendar('month');
      this.loadTodoList(targetDate);
    });
  },

  loadTodoList(selectDate) {
    console.log('===== 【4/7】筛选待办 =====');
    console.log('筛选日期：', selectDate, '当前视图：', this.data.currentView);
    console.log('全量待办长度：', this.data.allTodoList.length);
    
    if (this.data.currentView === 'all') return;
  
    if (!selectDate || !this.data.allTodoList.length) {
      console.log('筛选条件不满足，清空数据');
      this.setData({ todoList: [], scheduleList: [], weekScheduleList: [], weekScheduleGrouped: {} });
      return;
    }
  
    let todoList = [];
    const { currentView } = this.data;

    if (currentView === 'month') {
      todoList = this.data.allTodoList.filter((todo, index) => {
        const isInRange = this.isDateInTodoRange(selectDate, todo);
        console.log(`待办${index}（${todo.title}）是否在${selectDate}：`, isInRange);
        return isInRange;
      });
      this.convertTodoToSchedule(todoList, 'month');
    } else if (currentView === 'week') {
      console.log('===== 周视图筛选 =====');
      todoList = this.data.allTodoList.filter((todo, index) => {
        console.log(`待办${index}筛选检查：`, todo);
        if (!todo.startTime || !todo.endTime || typeof todo.startTime !== 'string' || typeof todo.endTime !== 'string') {
          console.log(`待办${index}时间格式无效，跳过`);
          return false;
        }
        const isSingleDay = this.isSingleDayTodo(todo);
        if (!isSingleDay) {
          console.log(`待办${index}跨天，跳过`);
          return false;
        }
        const todoDate = todo.startTime.split(' ')[0];
        const isInWeek = this.data.calendarDateList.some(item => item.dateStr === todoDate);
        console.log(`待办${index}日期${todoDate}是否在本周：`, isInWeek);
        return isInWeek;
      });
      console.log('周视图筛选后待办长度：', todoList.length);
      this.convertTodoToSchedule(todoList, 'week');
    }

    console.log('筛选后待办长度：', todoList.length);
    this.setData({ todoList });
  },

  convertTodoToSchedule(todoList, viewType) {
    console.log('===== 【5/7】转换为', viewType, '视图日程 =====');
    console.log('待转换待办长度：', todoList.length);
    
    if (viewType === 'month') {
      const scheduleList = [];
      todoList.forEach((todo, index) => {
        if (todo.startTime && todo.endTime && typeof todo.startTime === 'string' && (todo.startTime.includes(' ') || todo.startTime.includes('T'))) {
          const [date, time = ''] = todo.startTime.replace('T', ' ').split(' ');
          if (time && time.includes(':')) {
            const hour = time.split(':')[0];
            const start = this.parseTimeStr(todo.startTime);
            const end = this.parseTimeStr(todo.endTime);
            if (!isNaN(start.getTime()) && !isNaN(end.getTime())) {
              const durationMinutes = Math.round((end - start) / (1000 * 60));
              const duration = (durationMinutes / 60) * 2;
              const scheduleItem = {
                id: todo.id,
                dateStr: date,
                time: `${hour.toString().padStart(2, '0')}:00`,
                duration: duration,
                title: todo.title,
                articleid: todo.articleid || '' 
              };
              scheduleList.push(scheduleItem);
            }
          }
        }
      });
      console.log('月视图转换后日程长度：', scheduleList.length);
      this.setData({ scheduleList });
    } else if (viewType === 'week') {
      const HOUR_HEIGHT_RPX = 70;
      const rawWeekTodos = [];
      todoList.forEach((todo, index) => {
        const start = this.parseTimeStr(todo.startTime);
        const end = this.parseTimeStr(todo.endTime);
        if (!start || !end) {
          console.log(`待办${index}时间解析失败，跳过`);
          return;
        }

        const todoDateStr = this.formatDate(start);
        const dayIndex = this.getWeekDayIndex(todoDateStr);
        if (dayIndex === -1) {
          console.log(`待办${index}日期${todoDateStr}索引获取失败，跳过`);
          return;
        }

        rawWeekTodos.push({
          ...todo,
          dayIndex,
          startTs: start.getTime(),
          endTs: end.getTime()
        });
      });

      console.log('周视图原始列表长度：', rawWeekTodos.length);

      const todosByDay = {};
      rawWeekTodos.forEach(todo => {
        if (!todosByDay[todo.dayIndex]) {
          todosByDay[todo.dayIndex] = [];
        }
        todosByDay[todo.dayIndex].push(todo);
      });

      const mergedWeekItems = [];
      Object.values(todosByDay).forEach(dayTodos => {
        const mergedItems = this.mergeOverlappingTodos(dayTodos);
        mergedWeekItems.push(...mergedItems);
      });

      const validWeekItems = mergedWeekItems.filter(item => item && item.type);
      console.log('有效待办项长度：', validWeekItems.length);

      const weekScheduleGrouped = {};
      validWeekItems.forEach((item, index) => {
        const { dayIndex, startHour } = item;
        if (!weekScheduleGrouped[dayIndex]) {
          weekScheduleGrouped[dayIndex] = {};
        }
        if (!weekScheduleGrouped[dayIndex][startHour]) {
          weekScheduleGrouped[dayIndex][startHour] = [];
        }
        weekScheduleGrouped[dayIndex][startHour].push(item);
        console.log(`待办项${index}分组：dayIndex=${dayIndex}, startHour=${startHour}`);
      });

      console.log('===== 【关键】周视图分组数据 =====');
      console.log('分组数据结构：', JSON.stringify(weekScheduleGrouped, null, 2));

      this.setData({ 
        weekScheduleList: validWeekItems,
        weekScheduleGrouped: weekScheduleGrouped 
      }, () => {
        console.log('setData后分组数据：', JSON.stringify(this.data.weekScheduleGrouped, null, 2));
      });
    }
  },

  goBack() {
    const pages = getCurrentPages();
    pages.length <= 1 
      ? wx.switchTab({ url: '/pages/index/index' }) 
      : wx.navigateBack({ delta: 1 });
  },

  switchView(e) {
    const view = e?.currentTarget?.dataset?.view || 'month';
    console.log('===== 【6/7】切换视图 =====', view);
    this.setData({ currentView: view }, () => {
      if (!this.data.selectedDate) {
        this.setData({ selectedDate: this.formatDate(new Date()) });
      }
      this.renderCalendar(view);
      
      if (view === 'month' || view === 'week') {
        this.loadTodoList(this.data.selectedDate);
      } else if (view === 'all') {
        this.setData({ todoList: this.data.allTodoList, scheduleList: [], weekScheduleList: [], weekScheduleGrouped: {} });
      }
    });
  },

  selectDate(e) {
    const selectedDate = e?.currentTarget?.dataset?.date || this.formatDate(new Date());
    console.log('===== 选择日期 =====', selectedDate);
    if (!selectedDate) return;
    this.setData({ selectedDate }, () => {
      this.renderCalendar(this.data.currentView);
      if (['month', 'week'].includes(this.data.currentView)) {
        this.loadTodoList(selectedDate);
      }
    });
  },

  changeMonth(type) {
    const currentDate = new Date(this.data.selectedDate);
    currentDate.setMonth(currentDate.getMonth() + (type === 'prev' ? -1 : 1));
    const newDate = this.formatDate(currentDate);
    this.setData({ selectedDate: newDate }, () => {
      this.renderCalendar('month');
      this.loadTodoList(newDate);
    });
  },

  getCurrentTimeStr(isEnd = false) {
    const now = new Date();
    if (isEnd) now.setMinutes(now.getMinutes() + 1);
    const timeStr = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')} ${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}`;
    return timeStr;
  },

  getTimeIndexByStr(timeStr) {
    const { timeRange } = this.data;
    if (!timeStr || typeof timeStr !== 'string' || timeStr.trim() === '') {
      return [0, 0, 0, 0, 0];
    }
    
    const [datePart = '', timePart = ''] = timeStr.split(' ');
    const yearArr = (datePart || '').split('-').map(Number);
    const timeArr = (timePart || '').split(':').map(Number);
    const [year = 0, month = 0, day = 0] = yearArr;
    const [hour = 0, minute = 0] = timeArr;
  
    const result = [
      timeRange[0]?.findIndex(item => item === `${year}年`) || 0,
      timeRange[1]?.findIndex(item => item === `${month}月`) || 0,
      timeRange[2]?.findIndex(item => item === `${day}日`) || 0,
      timeRange[3]?.findIndex(item => item === `${String(hour).padStart(2, '0')}时`) || 0,
      timeRange[4]?.findIndex(item => item === `${String(minute).padStart(2, '0')}分`) || 0
    ];
    return result;
  },

  initTimeRange() {
    const now = new Date();
    const year = now.getFullYear();
    const month = now.getMonth() + 1;

    const yearList = [year - 2, year - 1, year, year + 1, year + 2].map(y => `${y}年`);
    const monthList = Array.from({ length: 12 }, (_, i) => `${i + 1}月`);
    const dayList = Array.from({ length: new Date(year, month, 0).getDate() }, (_, i) => `${i + 1}日`);
    const hourList = Array.from({ length: 24 }, (_, i) => `${String(i).padStart(2, '0')}时`);
    const minuteList = Array.from({ length: 60 }, (_, i) => `${String(i).padStart(2, '0')}分`);

    this.setData({
      timeRange: [yearList, monthList, dayList, hourList, minuteList],
      currentYear: year,
      currentMonth: month
    });
  },

  handleTimeColumnChange(e, type) {
    const { column, value } = e.detail;
    const indexKey = type === 'start' ? 'newTodoStartTimeIndex' : 'newTodoEndTimeIndex';
    const { timeRange, [indexKey]: index, currentYear, currentMonth } = this.data;
    
    if (!timeRange.length) return;
    
    const newIndex = [...index];
    newIndex[column] = value;
    let newTimeRange = JSON.parse(JSON.stringify(timeRange));

    if (column === 0 || column === 1) {
      const targetYear = column === 0 ? parseInt(newTimeRange[0][value]) : currentYear;
      const targetMonth = column === 1 ? parseInt(newTimeRange[1][value]) : currentMonth;
      const validMonth = Math.max(1, Math.min(12, targetMonth));
      const dayCount = new Date(targetYear, validMonth, 0).getDate();
      newTimeRange[2] = Array.from({ length: dayCount }, (_, i) => `${i + 1}日`);
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

  confirmTime(e, type) {
    const { value } = e.detail;
    const { timeRange } = this.data;
    const timeKey = type === 'start' ? 'startTime' : 'endTime';
    
    if (!timeRange[0] || !timeRange[1] || !timeRange[2] || !timeRange[3] || !timeRange[4]) {
      wx.showToast({ title: '时间选择异常', icon: 'none' });
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

  openAddTodoModal() {
    this.initTimeRange();
    const startTime = this.getCurrentTimeStr();
    const endTime = this.getCurrentTimeStr(true);

    this.setData({
      showAddTodoModal: true,
      newTodoData: {
        title: '',
        content: '',
        startTime,
        endTime,
        status: 0
      },
      newTodoStartTimeIndex: this.getTimeIndexByStr(startTime),
      newTodoEndTimeIndex: this.getTimeIndexByStr(endTime)
    });
  },

  closeAddTodoModal() {
    this.setData({ showAddTodoModal: false });
  },

  inputTodoData(e, type) {
    this.setData({ [`newTodoData.${type}`]: e.detail.value });
  },

  handleAddTodoConfirm() {
    const { newTodoData } = this.data;
    if (!newTodoData.title) return wx.showToast({ title: '标题不能为空', icon: 'none' });
    if (!newTodoData.startTime) return wx.showToast({ title: '请选择开始时间', icon: 'none' });
    if (!newTodoData.endTime) return wx.showToast({ title: '请选择结束时间', icon: 'none' });
    
    const startTime = this.parseTimeStr(newTodoData.startTime);
    const endTime = this.parseTimeStr(newTodoData.endTime);
    if (!startTime || !endTime || isNaN(startTime.getTime()) || isNaN(endTime.getTime())) {
      return wx.showToast({ title: '时间格式错误', icon: 'none' });
    }
    if (startTime >= endTime) return wx.showToast({ title: '结束时间需晚于开始时间', icon: 'none' });

    const requestData = {
      title: newTodoData.title,
      note: newTodoData.content || "",
      start_time: newTodoData.startTime + ":00",
      end_time: newTodoData.endTime + ":00",
      remind: true,
      status: newTodoData.status
    };

    addTodo(requestData).then(() => {
      wx.showToast({ title: '创建成功', icon: 'success' });
      this.closeAddTodoModal();
      this.loadAllTodoList(() => {
        if (['month', 'week'].includes(this.data.currentView)) {
          this.loadTodoList(this.data.selectedDate);
        }
      });
    }).catch(err => {
      console.error('创建待办失败：', err);
      wx.showToast({ title: `创建失败：${err}`, icon: 'none' });
    });
  },

  handleUpdateTodo(e) {
    const { todoData } = e.detail;
    if (!todoData?.id) return;
    
    const updateData = {
      title: todoData.title,
      note: todoData.content || "",
      start_time: todoData.startTime + ":00",
      end_time: todoData.endTime + ":00",
      remind: true,
      status: todoData.status
    };
  
    if (todoData.article !== undefined && todoData.article !== null && !isNaN(Number(todoData.article))) {
      updateData.article = Number(todoData.article);
    }
  
    updateTodo(todoData.id, updateData).then(() => {
      wx.showToast({ title: '修改成功', icon: 'success' });
      this.loadAllTodoList(() => {
        if (['month', 'week'].includes(this.data.currentView)) {
          this.loadTodoList(this.data.selectedDate);
        }
      });
    }).catch(err => {
      console.error('修改待办失败：', err);
      wx.showToast({ title: `修改失败：${err}`, icon: 'none' });
    });
  },

  handleDeleteTodo(e) {
    const { todoId } = e.detail;
    if (!todoId) return;
    deleteTodo(todoId).then(() => {
      wx.showToast({ title: '删除成功', icon: 'success' });
      this.loadAllTodoList(() => {
        if (['month', 'week'].includes(this.data.currentView)) {
          this.loadTodoList(this.data.selectedDate);
        }
      });
    }).catch(err => {
      console.error('删除待办失败：', err);
      wx.showToast({ title: `删除失败：${err}`, icon: 'none' });
    });
  },

  // 输出所有日志
  handleScheduleItemClick(e) {
    // 强制打印所有信息
    console.log('===== 【7/7】待办条点击事件触发 =====', new Date().getTime());
    console.log('原始e对象：', e);
    console.log('currentTarget：', e.currentTarget);
    console.log('target：', e.target);
    console.log('dataset：', e.currentTarget?.dataset || e.target?.dataset);
    
    // 兼容获取item
    const item = e.currentTarget?.dataset?.item || e.target?.dataset?.item || {};
    console.log('最终获取的item：', JSON.stringify(item, null, 2));
    
    if (Object.keys(item).length === 0) {
      wx.showToast({ title: '未获取到待办数据', icon: 'none' });
      console.error('待办数据为空！');
      return;
    }

    // 弹窗逻辑
    let popupData = {};
    try {
      if (item.type === 'single') {
        popupData = { type: 'single', todo: item.todos?.[0] || {} };
        console.log('Single待办articleid：', popupData.todo.articleid);
      } else if (item.type === 'group') {
        popupData = { type: 'group', todos: item.todos || [] };
      } else {
        throw new Error('待办类型错误：' + item.type);
      }
      console.log('组装弹窗数据：', JSON.stringify(popupData, null, 2));

      this.setData({ showTodoPopup: true, popupData }, () => {
        console.log(' 弹窗状态已更新：showTodoPopup=', this.data.showTodoPopup);
      });
    } catch (err) {
      console.error(' 弹窗组装失败：', err);
      wx.showToast({ title: '无法显示详情：' + err.message, icon: 'none' });
    }
  },

  closeTodoPopup() {
    this.setData({ showTodoPopup: false, popupData: {} });
  },

  formatDate(date) {
    if (!date || isNaN(date.getTime())) {
      date = new Date();
    }
    return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;
  },

  renderCalendar(view) {
    console.log('===== 渲染', view, '视图 =====');
    const currentRenderDate = new Date(this.data.selectedDate);
    if (isNaN(currentRenderDate.getTime())) {
      currentRenderDate.setTime(new Date().getTime());
    }
    
    let dateList = [];
    let viewTitle = '';
    const { weekHeaders, todayDate } = this.data;

    switch (view) {
      case 'year':
        viewTitle = `${currentRenderDate.getFullYear()}年`;
        for (let month = 1; month <= 12; month++) {
          const monthFirstDay = new Date(currentRenderDate.getFullYear(), month - 1, 1);
          const monthLastDay = new Date(currentRenderDate.getFullYear(), month, 0);
          let firstDayWeek = monthFirstDay.getDay();
          firstDayWeek = firstDayWeek === 0 ? 6 : firstDayWeek - 1;
          const monthDateList = [];
          for (let i = 0; i < firstDayWeek; i++) {
            monthDateList.push({ day: '', dateStr: '', isCurrent: false, isSelected: false });
          }
          for (let i = 1; i <= monthLastDay.getDate(); i++) {
            const date = new Date(currentRenderDate.getFullYear(), month - 1, i);
            const dateStr = this.formatDate(date);
            monthDateList.push({
              day: i,
              dateStr,
              isCurrent: dateStr === todayDate,
              isSelected: dateStr === this.data.selectedDate
            });
          }
          dateList.push({ month, dateList: monthDateList });
        }
        break;

      case 'month':
        viewTitle = `${currentRenderDate.getFullYear()}年${currentRenderDate.getMonth() + 1}月`;
        const monthFirstDay = new Date(currentRenderDate.getFullYear(), currentRenderDate.getMonth(), 1);
        const monthLastDay = new Date(currentRenderDate.getFullYear(), currentRenderDate.getMonth() + 1, 0);
        const firstDayWeekIndex = (monthFirstDay.getDay() || 7) - 1;
        for (let i = 0; i < firstDayWeekIndex; i++) {
          dateList.push({ dateStr: '', day: '', week: '', isCurrent: false, isSelected: false });
        }
        for (let i = 1; i <= monthLastDay.getDate(); i++) {
          const date = new Date(currentRenderDate.getFullYear(), currentRenderDate.getMonth(), i);
          const dateStr = this.formatDate(date);
          dateList.push({
            dateStr,
            day: i,
            week: weekHeaders[(date.getDay() || 7) - 1],
            isCurrent: dateStr === todayDate,
            isSelected: dateStr === this.data.selectedDate
          });
        }
        break;

      case 'week':
        viewTitle = `${currentRenderDate.getFullYear()}年${currentRenderDate.getMonth() + 1}月 第${Math.ceil(currentRenderDate.getDate()/7)}周`;
        const weekStart = new Date(currentRenderDate);
        weekStart.setDate(currentRenderDate.getDate() - ((currentRenderDate.getDay() || 7) - 1));
        for (let i = 0; i < 7; i++) {
          const date = new Date(weekStart);
          date.setDate(weekStart.getDate() + i);
          const dateStr = this.formatDate(date);
          dateList.push({
            dateStr,
            day: date.getDate(),
            dayIndex: i,
            isCurrent: dateStr === todayDate,
            isSelected: dateStr === this.data.selectedDate
          });
        }
        break;

      case 'all':
        viewTitle = '全部日程';
        dateList = [];
        break;
    }

    console.log(view, '视图渲染后dateList长度：', dateList.length);
    this.setData({ calendarDateList: dateList, currentViewTitle: viewTitle });
  }
});