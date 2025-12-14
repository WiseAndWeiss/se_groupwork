// floating-pet.js
Component({
  options: {
    addGlobalClass: true,
  },

  data: {
    x: 0,
    y: 0,
    windowWidth: 750,
    windowHeight: 1334,
    petSize: 180,
  },

  // 只用来"记位置"，不直接驱动 UI
  latestPosition: null,
  // 全局位置监听器
  positionWatcher: null,
  // 拖动相关
  touchStartX: 0,
  touchStartY: 0,
  touchStartPetX: 0,
  touchStartPetY: 0,
  isDragging: false,
  // 节流相关
  lastUpdateTime: 0,
  pendingUpdate: null,

  lifetimes: {
    attached() {
      this.initSystemInfo();
      this.initPosition();
      this.startPositionWatcher();
    },

    detached() {
      this.savePosition();
      clearTimeout(this.saveTimer);
      if (this.pendingUpdate) {
        clearTimeout(this.pendingUpdate);
        this.pendingUpdate = null;
      }
      this.stopPositionWatcher();
    }
  },

  methods: {
    /* 初始化屏幕尺寸 */
    initSystemInfo() {
      const info = wx.getSystemInfoSync();
      const rpxRatio = 750 / info.windowWidth;
      
      // 使用 screenHeight 而不是 windowHeight，确保所有页面使用相同的屏幕高度
      // screenHeight 是屏幕总高度，不受页面导航栏配置影响
      const screenHeight = info.screenHeight || info.windowHeight;

      this.setData({
        windowWidth: 750,
        windowHeight: screenHeight * rpxRatio
      });
    },

    /* 只在组件创建时读取一次位置 */
    initPosition() {
      const app = getApp();

      let pos =
        app.globalData.petPosition ||
        wx.getStorageSync('floatingPetPosition') ||
        null;

      // 如果没有保存的位置，设置默认位置（屏幕右侧中间）
      if (!pos) {
        const navBarHeight = 170; // 导航栏高度 rpx
        const petSize = this.data.petSize || 180;
        pos = {
          x: 750 - petSize - 20, // 右侧留20rpx边距
          y: navBarHeight + 200 // 导航栏下方200rpx
        };
      }

      this.latestPosition = { ...pos };
      app.globalData.petPosition = { ...pos };

      // ⚠️ 只在这里 setData
      this.setData({
        x: pos.x,
        y: pos.y
      });
      
      console.log('桌宠位置初始化:', pos);
    },

    /* 触摸开始 */
    onTouchStart(e) {
      this.stopPositionWatcher();
      // 阻止事件冒泡，防止触发滚动
      if (e.stopPropagation) {
        e.stopPropagation();
      }
      
      const touch = e.touches[0];
      this.touchStartX = touch.clientX;
      this.touchStartY = touch.clientY;
      this.touchStartPetX = this.latestPosition ? this.latestPosition.x : this.data.x;
      this.touchStartPetY = this.latestPosition ? this.latestPosition.y : this.data.y;
      this.isDragging = false;
    },

    /* 触摸移动 */
    onTouchMove(e) {
      // 阻止事件冒泡，防止触发滚动
      if (e.stopPropagation) {
        e.stopPropagation();
      }
      
      const touch = e.touches[0];
      const deltaX = touch.clientX - this.touchStartX;
      const deltaY = touch.clientY - this.touchStartY;
      
      // 如果移动距离超过阈值，认为是拖动
      if (Math.abs(deltaX) > 5 || Math.abs(deltaY) > 5) {
        this.isDragging = true;
      }

      if (this.isDragging) {
        // 阻止默认滚动行为
        if (e.preventDefault) {
          e.preventDefault();
        }
        
        const info = wx.getSystemInfoSync();
        const rpxRatio = 750 / info.windowWidth;
        
        // 计算新位置（基于初始位置 + 移动距离，转换为 rpx）
        let newX = this.touchStartPetX + deltaX * rpxRatio;
        let newY = this.touchStartPetY + deltaY * rpxRatio;
        
        // 限制在屏幕范围内（考虑导航栏和底部栏）
        const navBarHeight = 170; // 导航栏高度 rpx
        const tabBarHeight = 130; // 底部栏高度 rpx
        const bottomMargin = 120; // 底部留一点边距，避免完全贴底
        const sideMargin = 15; // 左右边界各扩大15rpx
        const minX = -sideMargin; // 左边界允许超出15rpx
        const maxX = 750 - this.data.petSize + sideMargin; // 右边界允许超出15rpx
        // 允许拖动到更靠近底部，只留少量边距
        const maxY = this.data.windowHeight - this.data.petSize - bottomMargin;
        newX = Math.max(minX, Math.min(newX, maxX));
        newY = Math.max(navBarHeight, Math.min(newY, maxY));
        
        // 更新位置状态
        this.latestPosition = { x: newX, y: newY };
        getApp().globalData.petPosition = { x: newX, y: newY };
        
        // 使用节流优化 setData 频率（每16ms更新一次，约60fps）
        const now = Date.now();
        if (now - this.lastUpdateTime >= 16) {
          this.setData({
            x: newX,
            y: newY
          });
          this.lastUpdateTime = now;
          
          // 清除待处理的更新
          if (this.pendingUpdate) {
            clearTimeout(this.pendingUpdate);
            this.pendingUpdate = null;
          }
        } else {
          // 保存最新位置，延迟更新
          if (this.pendingUpdate) {
            clearTimeout(this.pendingUpdate);
          }
          this.pendingUpdate = setTimeout(() => {
            if (this.latestPosition) {
              this.setData({
                x: this.latestPosition.x,
                y: this.latestPosition.y
              });
            }
            this.pendingUpdate = null;
            this.lastUpdateTime = Date.now();
          }, 16);
        }
      }
    },

    /* 触摸结束 */
    onTouchEnd(e) {
      // 阻止事件冒泡
      if (e.stopPropagation) {
        e.stopPropagation();
      }
      
      // 清除待处理的更新
      if (this.pendingUpdate) {
        clearTimeout(this.pendingUpdate);
        this.pendingUpdate = null;
      }
      
      if (this.isDragging) {
        // 确保最终位置被更新
        if (this.latestPosition) {
          this.setData({
            x: this.latestPosition.x,
            y: this.latestPosition.y
          });
        }
        // 保存位置
        this.savePosition();
        this.isDragging = false;

        this.startPositionWatcher();
      } else {
        // 如果没有拖动，认为是点击
        this.onPetTap();
      }
    },

    savePosition() {
      if (!this.latestPosition) return;
      wx.setStorageSync('floatingPetPosition', this.latestPosition);
      getApp().globalData.petPosition = this.latestPosition;
    },

    onPetTap() {
      wx.navigateTo({
        url: '/pages/ai-chat/ai-chat'
      });
    },

    /* 启动全局位置监听器 */
    startPositionWatcher() {
      const app = getApp();
      // 使用定时器监听全局位置变化
      this.positionWatcher = setInterval(() => {
        // 如果正在拖动，跳过同步（避免干扰用户拖动）
        if (this.isDragging) {
          return;
        }
        
        const globalPos = app.globalData.petPosition;
        if (globalPos && this.latestPosition) {
          // 如果全局位置与当前实例位置不一致，同步位置
          if (globalPos.x !== this.latestPosition.x || globalPos.y !== this.latestPosition.y) {
            this.latestPosition = { ...globalPos };
            this.setData({
              x: globalPos.x,
              y: globalPos.y
            });
          }
        }
      }, 100); // 每100ms检查一次
    },

    /* 停止全局位置监听器 */
    stopPositionWatcher() {
      if (this.positionWatcher) {
        clearInterval(this.positionWatcher);
        this.positionWatcher = null;
      }
    }
  }
});
