const app = getApp();

Component({
  properties: {
    showLoading: {
      type: Boolean,
      value: false,
      // 监听属性变化
      observer(newVal, oldVal) {
        if (newVal === true) {
          this.startTimeoutTimer();
        } else {
          this.clearTimeoutTimer();
        }
      }
    }
  },
  data: {
    timeoutId: null, // 存储超时定时器ID
    loadingGifUrl: ''
  },
  lifetimes: {
    attached() {
      this.getLoadingGifCache();
    },
  },

  methods: {
    getLoadingGifCache() {
      const gifUrl = 'https://403app.xyz/static/loading.gif';
      // 兼容app未定义的情况
      if (typeof app !== 'undefined' && app.getImgCache) {
        app.getImgCache(gifUrl).then((cachePath) => {
          this.setData({
            loadingGifUrl: cachePath
          });
          console.log('.gif 缓存路径:', cachePath);
        });
      }
    },

    // 阻止遮罩层下的滚动和点击
    preventTouchMove() {
      return false;
    },
    // 开启动画
    show() {
      this.setData({
        showLoading: true
      });
    },
    // 关闭动画
    hide() {
      this.setData({
        showLoading: false
      });
    },
    // 启动5秒超时定时器
    startTimeoutTimer() {
      this.clearTimeoutTimer();
      const timerId = setTimeout(() => {
        this.handleTimeout();
      }, 5000);
      this.setData({
        timeoutId: timerId
      });
    },
    // 清除超时定时器
    clearTimeoutTimer() {
      if (this.data.timeoutId) {
        clearTimeout(this.data.timeoutId);
        this.setData({
          timeoutId: null
        });
      }
    },
    // 超时处理逻辑
    handleTimeout() {
      this.hide();
      this.triggerEvent('loadingTimeout', {
        msg: '加载超时（5秒）'
      });
      this.clearTimeoutTimer();
    }
  },
  // 组件销毁时清除定时器
  detached() {
    this.clearTimeoutTimer();
  }
});