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
    petGifUrl: '',
    isLongPressMode: false,
    isImgLoading: true, // 新增：图片加载状态
    fallbackGifUrl: 'https://403app.xyz/static/pet.gif' // 兜底地址
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
  // 设备比例缓存（避免重复计算）
  rpxRatio: 1,
  // 图片加载重试相关
  imgLoadRetryTimes: 0,
  maxRetryTimes: 3, // 最大重试次数

  lifetimes: {
    attached() {
      this.initSystemInfo();
      this.initPosition();
      this.startPositionWatcher();
      // 优先加载兜底图片，再异步加载缓存图片
      this.setData({
        petGifUrl: this.data.fallbackGifUrl,
        isImgLoading: false
      });
      // 延迟加载缓存（适配非首页资源加载优先级）
      setTimeout(() => {
        this.getPetGifCache();
      }, 100);
      // 注册全局拖动状态（供页面判断）
      this.setPetDraggingStatus(false);
    },

    detached() {
      this.savePosition();
      clearTimeout(this.saveTimer);
      if (this.pendingUpdate) {
        clearTimeout(this.pendingUpdate);
        this.pendingUpdate = null;
      }
      this.stopPositionWatcher();
      // 清除拖动状态
      this.setPetDraggingStatus(false);
      // 清除重试定时器
      if (this.imgRetryTimer) clearTimeout(this.imgRetryTimer);
    }
  },

  methods: {
    // 新增：设置全局桌宠拖动状态
    setPetDraggingStatus(status) {
      const app = getApp({
        allowDefault: true
      });
      if (app?.globalData) {
        app.globalData.isPetDragging = status;
      }
    },

    // 优化：图片加载逻辑（增加重试、兜底、预加载）
    getPetGifCache() {
      const gifUrl = this.data.fallbackGifUrl;
      // 1. 预加载图片（解决原生组件加载延迟）
      this.preloadImage(gifUrl).then(() => {
        console.log('兜底图片预加载完成');
      }).catch(err => {
        console.warn('兜底图片预加载失败:', err);
      });

      // 2. 尝试获取缓存（兼容非首页App实例问题）
      let app;
      try {
        app = getApp({
          allowDefault: true
        });
      } catch (e) {
        console.warn('非首页未获取到App实例，使用兜底图片:', e);
        return;
      }

      if (app?.getImgCache) {
        app.getImgCache(gifUrl)
          .then((cachePath) => {
            // 验证缓存路径有效性
            this.checkImageValid(cachePath).then(() => {
              this.setData({
                petGifUrl: cachePath,
                isImgLoading: false
              });
              console.log('非首页pet.gif缓存路径:', cachePath);
            }).catch(() => {
              // 缓存文件无效，重试或使用兜底
              this.retryLoadImage();
            });
          })
          .catch((err) => {
            console.error('非首页获取图片缓存失败:', err);
            this.retryLoadImage();
          });
      } else {
        // 无缓存方法，直接使用兜底并预加载
        this.preloadImage(gifUrl).then(() => {
          this.setData({
            petGifUrl: gifUrl,
            isImgLoading: false
          });
        });
      }
    },

    // 新增：图片预加载（解决原生组件加载延迟）
    preloadImage(url) {
      return new Promise((resolve, reject) => {
        wx.getImageInfo({
          src: url,
          success: (res) => {
            resolve(res);
          },
          fail: (err) => {
            reject(err);
          }
        });
      });
    },

    // 新增：验证图片有效性（避免缓存文件损坏）
    checkImageValid(url) {
      return new Promise((resolve, reject) => {
        wx.getImageInfo({
          src: url,
          success: () => resolve(),
          fail: () => reject()
        });
      });
    },

    // 新增：图片加载失败重试
    retryLoadImage() {
      if (this.imgLoadRetryTimes >= this.maxRetryTimes) {
        console.warn('图片加载重试次数用尽，使用兜底图片');
        this.setData({
          petGifUrl: this.data.fallbackGifUrl,
          isImgLoading: false
        });
        return;
      }

      this.imgLoadRetryTimes++;
      console.log(`图片加载重试第${this.imgLoadRetryTimes}次`);

      // 延迟重试（避免频繁请求）
      this.imgRetryTimer = setTimeout(() => {
        this.getPetGifCache();
      }, 500 * this.imgLoadRetryTimes);
    },

    /* 初始化屏幕尺寸 */
    initSystemInfo() {
      const info = wx.getWindowInfo();
      // 缓存rpx转换比例（避免重复计算）
      this.rpxRatio = 750 / (info.windowWidth || 375);

      // 使用 screenHeight 而不是 windowHeight，确保所有页面使用相同的屏幕高度
      const screenHeight = info.screenHeight || info.windowHeight;

      this.setData({
        windowWidth: 750,
        windowHeight: screenHeight * this.rpxRatio
      });
    },

    /* 只在组件创建时读取一次位置 */
    initPosition() {
      let app = null;
      try {
        app = getApp({
          allowDefault: true
        });
      } catch (e) {
        console.warn('非首页未获取到App实例:', e);
      }

      let pos = null;
      // 优先级：全局数据 > 缓存 > 默认值
      if (app?.globalData?.petPosition) {
        pos = app.globalData.petPosition;
      } else {
        try {
          pos = wx.getStorageSync('floatingPetPosition');
        } catch (e) {
          console.warn('非首页读取宠物位置缓存失败:', e);
        }
      }

      // 如果没有保存的位置，设置默认位置（屏幕右侧中间）
      if (!pos) {
        const navBarHeight = 170; // 导航栏高度 rpx
        const petSize = this.data.petSize || 180;
        pos = {
          x: 750 - petSize - 20, // 右侧留20rpx边距
          y: navBarHeight + 200 // 导航栏下方200rpx
        };
      }

      this.latestPosition = {
        ...pos
      };
      if (app?.globalData) {
        app.globalData.petPosition = {
          ...pos
        };
      }

      // ⚠️ 只在这里 setData
      this.setData({
        x: pos.x,
        y: pos.y
      });

      console.log('非首页桌宠位置初始化:', pos);
    },

    /* 触摸开始 - 简化逻辑，适配原生组件 */
    onTouchStart(e) {
      console.log('start touch');
      // 1. 停止位置监听
      this.stopPositionWatcher();
      // 2. 标记开始拖动
      this.setPetDraggingStatus(true);

      const touch = e.touches[0];
      // 原生组件使用 pageX/pageY 更稳定（clientX/Y在部分设备有偏移）
      this.touchStartX = touch.pageX;
      this.touchStartY = touch.pageY;
      this.touchStartPetX = this.latestPosition?.x || this.data.x;
      this.touchStartPetY = this.latestPosition?.y || this.data.y;
      this.isDragging = false;

      // 原生组件必须返回false才能阻止默认行为（补充方案）
      return false;
    },

    /* 触摸移动 - 适配原生组件，简化节流 */
    onTouchMove(e) {
      const touch = e.touches[0];
      const deltaX = touch.pageX - this.touchStartX;
      const deltaY = touch.pageY - this.touchStartY;

      // 降低拖动阈值（适配手机端灵敏性）
      if (Math.abs(deltaX) > 2 || Math.abs(deltaY) > 2) {
        this.isDragging = true;
      }

      if (this.isDragging) {
        // 使用缓存的rpx比例，避免重复获取系统信息
        let newX = this.touchStartPetX + deltaX * this.rpxRatio;
        let newY = this.touchStartPetY + deltaY * this.rpxRatio;

        // 优化边界计算（适配不同手机屏幕）
        const petSize = this.data.petSize;
        const minX = 0; // 取消负边距，避免超出屏幕
        const maxX = this.data.windowWidth - petSize;
        const minY = 0; // 取消导航栏限制，让用户可拖动到顶部
        const maxY = this.data.windowHeight - petSize - 20; // 底部留20rpx

        // 严格限制在屏幕内
        newX = Math.max(minX, Math.min(newX, maxX));
        newY = Math.max(minY, Math.min(newY, maxY));

        // 更新位置状态
        this.latestPosition = {
          x: newX,
          y: newY
        };
        const app = getApp({
          allowDefault: true
        });
        if (app?.globalData) {
          app.globalData.petPosition = {
            x: newX,
            y: newY
          };
        }

        // 简化节流：每16ms更新一次，直接更新（原生组件不需要延迟）
        const now = Date.now();
        if (now - this.lastUpdateTime >= 16) {
          this.setData({
            x: newX,
            y: newY
          });
          this.lastUpdateTime = now;
        }
      }

      // 阻止原生滚动（关键：返回false）
      return false;
    },

    /* 触摸结束 - 完善逻辑 */
    onTouchEnd(e) {
      // 清除拖动状态
      this.setPetDraggingStatus(false);

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
        // 重启位置监听
        this.startPositionWatcher();
      } else {
        // 如果没有拖动，认为是点击
        this.onPetTap();
      }

      return false;
    },

    // 新增：处理触摸取消（比如离开屏幕）
    onTouchCancel(e) {
      this.setPetDraggingStatus(false);
      this.isDragging = false;
      this.startPositionWatcher();
      if (this.pendingUpdate) {
        clearTimeout(this.pendingUpdate);
        this.pendingUpdate = null;
      }
      return false;
    },

    savePosition() {
      if (!this.latestPosition) return;
      try {
        wx.setStorageSync('floatingPetPosition', this.latestPosition);
        const app = getApp({
          allowDefault: true
        });
        if (app?.globalData) {
          app.globalData.petPosition = this.latestPosition;
        }
      } catch (e) {
        console.error('非首页保存宠物位置失败:', e);
      }
    },

    onPetTap() {
      try {
        wx.navigateTo({
          url: '/pages/ai-chat/ai-chat'
        });
      } catch (e) {
        // 兼容页面栈满的情况
        wx.redirectTo({
          url: '/pages/ai-chat/ai-chat'
        });
      }
    },

    /* 启动全局位置监听器（降低频率，减少干扰） */
    startPositionWatcher() {
      const app = getApp({
        allowDefault: true
      });
      // 降低监听频率，减少性能消耗
      this.positionWatcher = setInterval(() => {
        if (this.isDragging) return;

        const globalPos = app?.globalData?.petPosition;
        if (globalPos && this.latestPosition) {
          if (globalPos.x !== this.latestPosition.x || globalPos.y !== this.latestPosition.y) {
            this.latestPosition = {
              ...globalPos
            };
            this.setData({
              x: globalPos.x,
              y: globalPos.y
            });
          }
        }
      }, 200); // 每200ms检查一次
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