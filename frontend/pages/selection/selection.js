// selection.js - 修复最大滚动距离计算问题
const request = require('../../utils/request');

Page({
  data: {
    showLoadingAnimation: false,
    searchContent: '',
    currentSort: 'time',
    subscriptionList: [],
    tempSubscriptionList: [],
    isEditing: false,
    dragStartIndex: -1,
    dragCurrentIndex: -1,
    touchStartY: 0,
    touchStartX: 0,
    touchStartScrollTop: 0, // 记录触摸开始时的滚动位置
    itemHeight: 0,
    itemWidth: 0,
    itemsPerRow: 3,
    scrollTop: 0,
    autoScrollInterval: null,
    autoScrollSpeed: 0,
    scrollContainerHeight: 0,
    scrollThreshold: 100,
    containerTop: 0,
    containerBottom: 0,
    maxScrollTop: 0,
    contentHeight: 0, // 添加内容高度
    enableScroll: true, // 控制滚动是否启用
    isDragging: false, // 是否正在拖动（长按后）
    longPressTimer: null, // 长按定时器
    scrollUpdateTimer: null // 滚动更新节流定时器
  },

  onReady() {
    wx.hideTabBar({
      animation: false,
      success: () => console.log("tabBar 隐藏成功"),
      fail: (err) => console.log("隐藏失败", err)
    });
    
    this.calculateItemSize();
    this.getScrollContainerInfo();
  },

  // 获取滚动容器完整信息
  getScrollContainerInfo() {
    return new Promise((resolve) => {
      const query = wx.createSelectorQuery();
      query.select('.subscription-container').boundingClientRect();
      query.exec((res) => {
        if (res[0]) {
          const container = res[0];
          this.setData({
            scrollContainerHeight: container.height,
            containerTop: container.top,
            containerBottom: container.bottom
          }, () => {
            // 延迟计算最大滚动距离，确保容器已经渲染
            setTimeout(() => {
              this.calculateMaxScrollTop();
            }, 100);
            resolve(container);
          });
          console.log('容器信息:', container);
        } else {
          console.warn('未找到滚动容器');
          resolve(null);
        }
      });
    });
  },

  // 计算最大滚动距离 - 修复版本
  calculateMaxScrollTop() {
    return new Promise((resolve) => {
      const query = wx.createSelectorQuery();
      
      // 同时查询容器和内容
      query.select('.subscription-container').boundingClientRect();
      query.select('.subscription-content').boundingClientRect();
      query.exec((res) => {
        if (res[0] && res[1]) {
          const container = res[0];
          const content = res[1];
          
          const containerHeight = container.height;
          const contentHeight = content.height;
          const maxScrollTop = Math.max(0, contentHeight - containerHeight);
          
          console.log('最大滚动距离计算:', {
            containerHeight,
            contentHeight,
            maxScrollTop,
            itemCount: this.data.tempSubscriptionList.length,
            itemsPerRow: this.data.itemsPerRow
          });
          
          this.setData({
            maxScrollTop: maxScrollTop,
            contentHeight: contentHeight
          });
          
          resolve(maxScrollTop);
        } else {
          console.warn('计算最大滚动距离失败，使用备用计算方式');
          
          // 备用计算方式：基于项目数量和行高计算
          const itemCount = this.data.tempSubscriptionList.length || this.data.subscriptionList.length;
          const rows = Math.ceil(itemCount / this.data.itemsPerRow);
          const estimatedContentHeight = rows * (this.data.itemHeight || 100); // 假设每个项目高度100px
          const containerHeight = this.data.scrollContainerHeight;
          const estimatedMaxScrollTop = Math.max(0, estimatedContentHeight - containerHeight);
          
          console.log('备用计算最大滚动距离:', {
            itemCount,
            rows,
            estimatedContentHeight,
            containerHeight,
            estimatedMaxScrollTop
          });
          
          this.setData({
            maxScrollTop: estimatedMaxScrollTop,
            contentHeight: estimatedContentHeight
          });
          
          resolve(estimatedMaxScrollTop);
        }
      });
    });
  },

  // 计算卡片尺寸和间距
  calculateItemSize() {
    return new Promise((resolve) => {
      const query = wx.createSelectorQuery();
      query.select('.subscription-item').boundingClientRect();
      query.selectAll('.draggable-item').boundingClientRect();
      query.exec((res) => {
        if (res[0] && res[1] && res[1].length >= 2) {
          const container = res[0];
          const firstItem = res[1][0];
          const secondItem = res[1][1];
          
          const itemWidth = firstItem.width;
          const itemHeight = firstItem.height;
          const colSpacing = secondItem.left - (firstItem.left + itemWidth);
          const actualItemWidth = itemWidth + colSpacing;
          
          this.setData({
            itemHeight: itemHeight,
            itemWidth: actualItemWidth,
            containerLeft: container.left,
            containerTop: container.top
          }, () => {
            console.log('项目尺寸计算完成:', {
              itemHeight,
              itemWidth: actualItemWidth
            });
            resolve();
          });
        } else if (res[1] && res[1].length > 0) {
          const item = res[1][0];
          this.setData({
            itemHeight: item.height,
            itemWidth: item.width
          }, () => {
            console.log('项目尺寸计算完成（备用）:', {
              itemHeight: item.height,
              itemWidth: item.width
            });
            resolve();
          });
        } else {
          console.warn('无法计算项目尺寸，使用默认值');
          this.setData({
            itemHeight: 100,
            itemWidth: 100
          });
          resolve();
        }
      });
    });
  },

  // 进入编辑模式
  async enterEditMode() {
    if (this.data.currentSort !== 'official') return;
    
    // 等待所有计算完成
    await this.calculateItemSize();
    await this.getScrollContainerInfo();
    await this.calculateMaxScrollTop();
    
    const tempSubscriptionList = this.data.subscriptionList.map((item, index) => ({
      ...item,
      isShaking: true,
      tempOrder: index
    }));
    
    this.setData({
      isEditing: true,
      tempSubscriptionList,
      subscriptionList: tempSubscriptionList,
      dragStartIndex: -1,
      dragCurrentIndex: -1,
      isDragging: false
      // scrollTop 保持当前值，不重置
    });
    
    console.log('编辑模式准备完成，最大滚动距离:', this.data.maxScrollTop);
  },

  // 触摸开始
  onTouchStart(e) {
    if (!this.data.isEditing) return;
    
    const touch = e.touches[0];
    const index = e.currentTarget.dataset.index;
    
    // 清除之前的长按定时器
    if (this.data.longPressTimer) {
      clearTimeout(this.data.longPressTimer);
    }
    
    // 保存触摸开始时的位置信息
    const touchStartY = touch.clientY;
    const touchStartX = touch.clientX;
    // const currentScrollTop = this.data.scrollTop; // 获取当前滚动位置（已禁用 scrollTop 维护）
    
    this.setData({
      touchStartY: touchStartY,
      touchStartX: touchStartX,
      // touchStartScrollTop: currentScrollTop, // 记录触摸开始时的滚动位置（已禁用 scrollTop 维护）
      dragStartIndex: index,
      dragCurrentIndex: index,
      isDragging: false
    });
    
    // 设置长按定时器，0.5秒后允许拖动
    const longPressTimer = setTimeout(() => {
      console.log('长按0.5秒，开始拖动模式');
      
      const tempSubscriptionList = this.data.tempSubscriptionList.map((item, i) => ({
        ...item,
        isDragging: i === index
      }));
      
      this.setData({
        isDragging: true,
        tempSubscriptionList,
        subscriptionList: tempSubscriptionList,
        enableScroll: false // 拖动时禁用手动滚动
      });
      
      // 开始检测自动滚动（使用当前触摸位置）
      // 注意：这里需要在 onTouchMove 中持续调用，因为触摸位置会变化
    }, 500);
    
    this.setData({
      longPressTimer: longPressTimer
    });
  },

  // 检测并启动自动滚动（只在拖动状态下才触发）
  checkAndStartAutoScroll(touchY) {
    if (!this.data.isEditing || this.data.dragStartIndex === -1 || !this.data.isDragging) {
      console.log('自动滚动检查失败:', {
        isEditing: this.data.isEditing,
        dragStartIndex: this.data.dragStartIndex,
        isDragging: this.data.isDragging
      });
      return;
    }
    
    const containerTop = this.data.containerTop;
    const containerBottom = this.data.containerBottom;
    
    // 修复逻辑：检查 containerTop 是否为 undefined 或 null
    if (containerTop === undefined || containerTop === null || 
        containerBottom === undefined || containerBottom === null) {
      console.warn('容器位置信息未获取到，重新获取');
      this.getScrollContainerInfo().then(() => {
        this.checkAndStartAutoScroll(touchY);
      });
      return;
    }
    
    // 判断触摸点是否在滚动触发区域
    const isInTopScrollArea = touchY < (containerTop + this.data.scrollThreshold);
    const isInBottomScrollArea = touchY > (containerBottom - this.data.scrollThreshold);
    
    console.log('检测自动滚动:', {
      touchY,
      containerTop,
      containerBottom,
      scrollThreshold: this.data.scrollThreshold,
      isInTopScrollArea,
      isInBottomScrollArea
    });
    
    if (isInTopScrollArea) {
      console.log('触发向上滚动');
      this.startAutoScroll(-1);
    } else if (isInBottomScrollArea) {
      console.log('触发向下滚动');
      this.startAutoScroll(1);
    } else {
      console.log('停止自动滚动');
      this.stopAutoScroll();
    }
  },

  // 启动自动滚动（已禁用，代码保留供参考）
  startAutoScroll(direction) {
    // 如果最大滚动距离为0，说明不需要滚动
    if (this.data.maxScrollTop <= 0) {
      console.log('最大滚动距离为0，无需滚动');
      return;
    }
    
    // 如果已经在滚动且方向相同，则不重复启动
    if (this.data.autoScrollInterval && 
        Math.sign(this.data.autoScrollSpeed) === Math.sign(direction)) {
      return;
    }
    
    this.stopAutoScroll();
    
    const scrollSpeed = 15; // 滚动速度
    const interval = 30; // 滚动间隔时间（毫秒）
    
    // 设置自动滚动速度
    this.setData({
      autoScrollSpeed: direction * scrollSpeed
    });
    
    console.log('启动自动滚动，速度:', this.data.autoScrollSpeed, '最大滚动距离:', this.data.maxScrollTop);
    
    // 设置定时器进行自动滚动（已禁用）
    // const intervalId = setInterval(() => {
    //   if (this.data.isEditing && this.data.dragStartIndex !== -1 && this.data.isDragging) {
    //     const currentScrollTop = this.data.scrollTop;
    //     const newScrollTop = currentScrollTop + this.data.autoScrollSpeed;
    //     
    //     // 确保滚动位置在合理范围内
    //     const clampedScrollTop = Math.max(0, Math.min(newScrollTop, this.data.maxScrollTop));
    //     
    //     if (clampedScrollTop !== currentScrollTop) {
    //       // 只更新滚动位置，不更新 touchStartY
    //       // touchStartY 保持为屏幕坐标，在计算时再补偿滚动
    //       this.setData({
    //         scrollTop: clampedScrollTop
    //       });
    //       console.log('自动滚动到:', clampedScrollTop, '/', this.data.maxScrollTop);
    //     } else {
    //       // 如果到达边界，停止滚动
    //       if (clampedScrollTop === 0 && direction === -1) {
    //         console.log('到达顶部边界，停止滚动');
    //         this.stopAutoScroll();
    //       } else if (clampedScrollTop >= this.data.maxScrollTop && direction === 1) {
    //         console.log('到达底部边界，停止滚动');
    //         this.stopAutoScroll();
    //       }
    //     }
    //   } else {
    //     console.log('自动滚动条件不满足，停止');
    //     this.stopAutoScroll();
    //   }
    // }, interval);
    // 
    // this.setData({
    //   autoScrollInterval: intervalId
    // });
  },

  // 停止自动滚动
  stopAutoScroll() {
    if (this.data.autoScrollInterval) {
      clearInterval(this.data.autoScrollInterval);
    }
    // 停止自动滚动时，如果不在拖动状态，恢复手动滚动
    const updateData = {
      autoScrollInterval: null,
      autoScrollSpeed: 0
    };
    if (this.data.isEditing && !this.data.isDragging) {
      updateData.enableScroll = true;
    }
    this.setData(updateData);
  },

  // 触摸移动
  onTouchMove(e) {
    if (!this.data.isEditing) {
      // 非编辑模式下，不处理任何逻辑，允许滚动
      return;
    }
    
    // 如果还没有设置 dragStartIndex，说明不是从卡片开始的触摸，允许滚动
    if (this.data.dragStartIndex === -1) {
      return;
    }
    
    const touch = e.touches[0];
    
    // 如果还没有进入拖动状态（长按未完成）
    if (!this.data.isDragging) {
      // 如果移动距离较大，取消长按，并重置 dragStartIndex，允许滚动
      const moveDistance = Math.abs(touch.clientY - this.data.touchStartY) + 
                          Math.abs(touch.clientX - this.data.touchStartX);
      if (moveDistance > 10) {
        if (this.data.longPressTimer) {
          clearTimeout(this.data.longPressTimer);
        }
        // 重置状态，允许滚动
        this.setData({ 
          longPressTimer: null,
          dragStartIndex: -1,
          dragCurrentIndex: -1,
          enableScroll: true // 恢复手动滚动
        });
      }
      // 未进入拖动状态，不处理移动，允许滚动正常进行
      return;
    }
    
    // 拖动状态下，阻止事件冒泡（防止滚动）
    
    // 持续检测位置以触发自动滚动
    this.checkAndStartAutoScroll(touch.clientY);
    
    if (this.data.itemHeight === 0 || this.data.itemWidth === 0) {
      this.calculateItemSize();
      return;
    }
    
    // 计算滚动距离的变化量（自动滚动导致的）- 已禁用自动滚动，所以不需要补偿
    // const scrollDelta = this.data.scrollTop - this.data.touchStartScrollTop;
    
    // 计算触摸点的移动距离，需要补偿滚动的影响（已禁用自动滚动，所以直接使用屏幕移动距离）
    // 屏幕上的移动：touch.clientY - touchStartY
    // 滚动导致的相对移动：scrollDelta（向下滚动为正，内容向上移动）
    // 总移动距离 = 屏幕移动 + 滚动导致的相对移动
    // const deltaY = touch.clientY - this.data.touchStartY + scrollDelta;
    const deltaY = touch.clientY - this.data.touchStartY; // 已禁用自动滚动，直接使用屏幕移动距离
    const deltaX = touch.clientX - this.data.touchStartX;
    
    const threshold = Math.min(this.data.itemHeight, this.data.itemWidth) * 0.3;
    if (Math.abs(deltaX) < threshold && Math.abs(deltaY) < threshold) {
      return;
    }
    
    // 计算移动的行数和列数
    const rowsMoved = Math.round(deltaY / this.data.itemHeight);
    const colsMoved = Math.round(deltaX / this.data.itemWidth);
    
    console.log('触摸移动:', {
      touchY: touch.clientY,
      touchStartY: this.data.touchStartY,
      screenDeltaY: touch.clientY - this.data.touchStartY,
      // scrollDelta, // 已禁用自动滚动
      deltaY,
      rowsMoved
      // scrollTop: this.data.scrollTop, // 已禁用 scrollTop 维护
      // touchStartScrollTop: this.data.touchStartScrollTop // 已禁用 scrollTop 维护
    });
    
    const startRow = Math.floor(this.data.dragStartIndex / this.data.itemsPerRow);
    const startCol = this.data.dragStartIndex % this.data.itemsPerRow;
    
    const targetRow = startRow + rowsMoved;
    const targetCol = startCol + colsMoved;
    
    const validCol = Math.max(0, Math.min(targetCol, this.data.itemsPerRow - 1));
    
    let newIndex = targetRow * this.data.itemsPerRow + validCol;
    newIndex = Math.max(0, Math.min(newIndex, this.data.tempSubscriptionList.length - 1));
    
    if (newIndex !== this.data.dragCurrentIndex && newIndex >= 0 && newIndex < this.data.tempSubscriptionList.length) {
      this.moveItem(this.data.dragCurrentIndex, newIndex);
      this.setData({
        dragCurrentIndex: newIndex
      });
    }
  },

  // 触摸结束
  onTouchEnd(e) {
    if (!this.data.isEditing) return;
    
    // 清除长按定时器
    if (this.data.longPressTimer) {
      clearTimeout(this.data.longPressTimer);
    }
    
    // 直接使用当前的 scrollTop（onScroll 会持续更新，应该是最新的）- 已禁用 scrollTop 维护
    // const currentScrollTop = this.data.scrollTop;
    // console.log('触摸结束，保持滚动位置:', currentScrollTop);
    
    this.stopAutoScroll();
    
    const tempSubscriptionList = this.data.tempSubscriptionList.map(item => ({
      ...item,
      isDragging: false
    }));
    
    this.setData({
      tempSubscriptionList,
      subscriptionList: tempSubscriptionList,
      dragStartIndex: -1,
      dragCurrentIndex: -1,
      isDragging: false,
      longPressTimer: null,
      // scrollTop: currentScrollTop, // 确保 scrollTop 是最新的，保持滚动位置（已禁用 scrollTop 维护）
      enableScroll: true // 恢复手动滚动
    });
  },

  // 滚动事件处理（优化性能：减少更新频率）- 已禁用 scrollTop 维护
  // onScroll(e) {
  //   // 不管什么模式都维护 scrollTop
  //   const newScrollTop = e.detail.scrollTop;
  //   
  //   // 清除之前的定时器
  //   if (this.data.scrollUpdateTimer) {
  //     clearTimeout(this.data.scrollUpdateTimer);
  //   }
  //   
  //   // 使用节流，减少 setData 频率（约60fps）
  //   const scrollUpdateTimer = setTimeout(() => {
  //     // 只在值真正改变时才更新，避免不必要的 setData
  //     // 拖动状态下也更新，但频率较低，不会影响自动滚动（已禁用）
  //     if (Math.abs(newScrollTop - this.data.scrollTop) > 2) {
  //       this.setData({
  //         scrollTop: newScrollTop
  //       });
  //     }
  //     this.setData({
  //       scrollUpdateTimer: null
  //     });
  //   }, 16);
  //   
  //   this.setData({
  //     scrollUpdateTimer: scrollUpdateTimer
  //   });
  // },


  // 其他方法保持不变...
  moveItem(fromIndex, toIndex) {
    const tempSubscriptionList = [...this.data.tempSubscriptionList];
    const movedItem = tempSubscriptionList[fromIndex];
    tempSubscriptionList.splice(fromIndex, 1);
    tempSubscriptionList.splice(toIndex, 0, movedItem);
    
    this.setData({ 
      tempSubscriptionList,
      subscriptionList: tempSubscriptionList 
    });
  },

  deleteSubscription(e) {
    const index = e.currentTarget.dataset.index;
    const target = this.data.tempSubscriptionList[index];
    const subscriptionId = target?.id;

    if (!subscriptionId) {
      wx.showToast({ title: '订阅ID无效，无法删除', icon: 'none' });
      return;
    }

    wx.showModal({
      title: '确认删除',
      content: '确定要取消关注这个公众号吗？',
      success: (res) => {
        if (!res.confirm) return;

        wx.showLoading({ title: '正在取消...', mask: true });

        request.deleteSubscription(subscriptionId)
          .then(() => {
            const tempSubscriptionList = [...this.data.tempSubscriptionList];
            tempSubscriptionList.splice(index, 1);
            this.setData({
              tempSubscriptionList,
              subscriptionList: tempSubscriptionList
            });
            // 删除后重新计算滚动范围
            this.calculateMaxScrollTop();
            wx.showToast({ title: '已取消关注', icon: 'success' });
          })
          .catch((err) => {
            console.error('取消订阅失败：', err);
            wx.showToast({ title: '取消失败，请重试', icon: 'none' });
          })
          .finally(() => {
            wx.hideLoading();
          });
      }
    });
  },

  exitEditMode() {
    // 清除长按定时器
    if (this.data.longPressTimer) {
      clearTimeout(this.data.longPressTimer);
    }
    
    this.stopAutoScroll();
    this.saveNewOrder();
  
    const subscriptionList = this.data.tempSubscriptionList.map(item => ({
      ...item,
      isShaking: false,
      isDragging: false
    }));
    
    this.setData({
      isEditing: false,
      subscriptionList,
      tempSubscriptionList: [],
      dragStartIndex: -1,
      dragCurrentIndex: -1,
      enableScroll: true, // 退出编辑模式后恢复滚动
      isDragging: false,
      longPressTimer: null
      // scrollTop 保持当前值，不重置
    });
  },

  async saveNewOrder() {
    try {
      const orders = this.data.tempSubscriptionList.map((item, index) => ({
        subscription_id: item.id,
        order: index + 1
      }));
      
      const requestData = {
        orders: orders
      };
      
      console.log('保存新的排序顺序:', requestData);
      await request.sortSubscriptions(requestData);
      
      wx.showToast({
        title: '排序已更新',
        icon: 'success',
        duration: 1000
      });
    } catch (error) {
      console.error('保存排序失败:', error);
      wx.showToast({
        title: '保存失败',
        icon: 'none'
      });
    }
  },

  // 其他现有方法...
  onUnload() {
    // 清除长按定时器
    if (this.data.longPressTimer) {
      clearTimeout(this.data.longPressTimer);
    }
    this.stopAutoScroll();
  },

  onHide() {
    
    // 清除长按定时器
    if (this.data.longPressTimer) {
      clearTimeout(this.data.longPressTimer);
    }
    this.stopAutoScroll();
    // this.clearPageData();
  },

  clearPageData() {
    this.stopAutoScroll();
    this.setData({
      searchContent: '',
      selectionList: [],
      officialList: [],
      isLoading: false,
      start_rank: 0,
      reach_end: false,
      subscriptionList: [],
      tempSubscriptionList: [],
      // scrollTop: 0, // 已禁用 scrollTop 维护
      maxScrollTop: 0, // 重置最大滚动距离
      enableScroll: true ,// 确保非编辑模式下滚动可用
      currentSort :'time',
    });
  },

  onShow() {
    console.log('自选页面加载完成');
    if (this.data.currentSort === 'time') {
      this.loadCustomizedArticles(true);
    } else {
      this.getSubscriptionList(true);
    }
  },


  onSearchInput(e) {
    this.setData({
      searchContent: e.detail.value
    });
  },

  handleLoadMore() {
    console.log('父页面接收到加载更多事件');
    this.loadCustomizedArticles(false); // false=追加数据
  },

  async loadCustomizedArticles(reset = false) {
    if (this.data.isLoading || this.data.reach_end) return; 
    this.setData({ 
        isLoading: true,
        showLoadingAnimation: true ,// 显示加载动画
      });
    console.log('开始加载自选文章...');
    
    try {
      let start_rank = reset ? 0 : this.data.start_rank;
      console.log('请求start_rank:', start_rank);
      const response = await request.getCustomizedLatestArticles(start_rank);

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
      } else {
        console.warn('接口返回数据格式异常：', response);
        wx.showToast({ title: '数据加载异常', icon: 'none' });
        this.setData({ isLoading: false });
      }
    } catch (error) {
      console.error('加载自选文章失败：', error);
      wx.showToast({ title: '加载失败: ' + error, icon: 'none' });
      this.setData({
        selectionList: []
      });
    } finally {
      console.log('加载完成，设置 isLoading = false');
      this.setData({ 
        showLoadingAnimation: false,
        isLoading: false
      });
    }
  },

  async getSubscriptionList() {
    this.setData({ 
        showLoadingAnimation: true // 显示加载动画
      });
    try {
      const list = await request.getSubscriptionList();
      this.setData({ subscriptionList: list });
      console.log('订阅列表数据（含 id）：', list);
      if (list.length > 0) console.log('第一个订阅的 id：', list[0].id);
    } catch (err) {
      wx.showToast({ title: '获取订阅列表失败', icon: 'none' });
      console.error('获取订阅失败：', err);
    }
    this.setData({ 
        showLoadingAnimation: false
      });
  },

  switchSort(e) {
    const sortType = e.currentTarget.dataset.type;
    if (this.data.currentSort === sortType) return;
    
    if (this.data.isEditing) {
      this.cancelEditMode();
    }
    
    this.setData({
      searchContent: '',
      currentSort: sortType,
      start_rank: 0,
      reach_end: false,
      officialList: [],
      selectionList: [],
      // scrollTop: 0, // 已禁用 scrollTop 维护
      enableScroll: true // 切换排序时确保滚动可用
    });
    
    if (sortType === 'time') {
      this.loadCustomizedArticles(true);
    } else {
      this.getSubscriptionList(true);
    }
  },

  cancelEditMode() {
    // 清除长按定时器
    if (this.data.longPressTimer) {
      clearTimeout(this.data.longPressTimer);
    }
    
    this.stopAutoScroll();
    
    const subscriptionList = this.data.subscriptionList.map(item => ({
      ...item,
      isShaking: false,
      isDragging: false
    }));
    
    this.setData({
      isEditing: false,
      subscriptionList,
      tempSubscriptionList: [],
      dragStartIndex: -1,
      dragCurrentIndex: -1,
      enableScroll: true, // 取消编辑模式后恢复滚动
      isDragging: false,
      longPressTimer: null
      // scrollTop 保持当前值，不重置
    });
  },

  async loadFilteredCustomizedArticles(reset = false) {
    if (this.data.isLoading) return;
    this.setData({ 
        isLoading: true,
        showLoadingAnimation: true ,// 显示加载动画
      });
    console.log('开始加载筛选的自选文章...');
    
    try {
      const start_rank = reset ? 0 : this.data.start_rank;
      const response = await request.getFilteredCustomizedLatestArticles(start_rank, this.data.searchContent);
      console.log('获取自选最新文章：', response);

      if (response && response.articles) {
        const newList = reset ? response.articles : [...this.data.selectionList, ...response.articles];
        this.setData({
          selectionList: newList
        });
      } else {
        console.warn('接口返回数据格式异常：', response);
        wx.showToast({ title: '数据加载异常', icon: 'none' });
        this.setData({ isLoading: false });
      }
    } catch (error) {
      console.error('加载自选文章失败：', error);
      wx.showToast({ title: '加载失败: ' + error, icon: 'none' });
      this.setData({
        selectionList: []
      });
    } finally {
      console.log('加载完成，设置 isLoading = false');
      this.setData({ 
        showLoadingAnimation: false,
        isLoading: false
      });
    }
  },
  async getFilteredSubscriptionList() {
    const response = await request.searchSubscriptions(this.data.searchContent);
    if (response) {
      this.setData({
        subscriptionList: response
      })
    } else {
      console.log("未搜索到订阅信息");
    }
  },

  /*
  onPullDownRefresh() {
    const app = getApp();
    console.log(app.globalData.isPetDragging);
    // 如果正在拖动桌宠，直接停止刷新，不执行任何操作
    if (app.globalData.isPetDragging) {
      wx.stopPullDownRefresh();
      console.log(app.globalData.isPetDragging);
      return;
    };  
    if (this.data.isEditing) {
        wx.stopPullDownRefresh();
        return;
      };
    console.log('下拉刷新，重置和公众号列表');
    this.setData({
        searchContent: '',
        isLoading: false,
        reachEnd: false,
        maxScrollTop: 0, // 重置最大滚动距离
        enableScroll: true ,// 确保非编辑模式下滚动可用
        currentSort :'time',
        start_rank: 0,
        reachEnd: false
      });
    Promise.all([this.loadCustomizedArticles(true)],[ this.getSubscriptionList(true)]) // 重置数据
      .finally(() => wx.stopPullDownRefresh());
  },*/
  

  preventNavigation() {
    return false;
  },

  goToAdd() {
    this.clearPageData();
    wx.navigateTo({ url: '/packageA/add/add' });
  },

  goToHome() {
    this.clearPageData();
    wx.switchTab({ url: '/pages/home/home' });
  },
  
  goToCampus() {
    this.clearPageData();
    wx.switchTab({ url: '/pages/campus/campus' });
  },
  
  goToUser() {
    this.clearPageData();
    wx.switchTab({ url: '/pages/user/user' });
  }
});