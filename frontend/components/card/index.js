// card.js
const request = require('../../utils/request');

Component({
  options: {
    addGlobalClass: true,
  },
  properties: {
    id_: Number,       // 文章唯一ID
    title: String,    // 文章标题
    time: String,     // 发布时间
    tags: {           // Array默认空数组
        type: Array,
        value: []
      },      
    desc: String,     // 文章描述
    url: String,      // 文章链接
    name: String,      // 公众号名称
    key_info: String,      // 关键词
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
  },

  lifetimes: {
    detached() {
        if (this.data.tipTimer) clearTimeout(this.data.tipTimer);
      }
  },

  methods: { 
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
          console.log('收藏夹列表设置完成：', { validList, defaultCollection });
          // 无默认收藏夹时提示（不清楚是否会正常创建默认收藏夹）
          if (!defaultCollection) {
            wx.showToast({ title: '未找到默认收藏夹', icon: 'none' });
          }
        } catch (err) {
          console.error('获取收藏夹列表失败：', err);
          wx.showToast({ title: '获取收藏夹失败', icon: 'none' });
        }
      },

    // 收藏/取消收藏逻辑（对接 POST /api/user/favorites/ 和 DELETE /api/user/favorites/{id}/）
    async onFavourite() {
      const articleId = this.properties.id_;
      console.log(articleId);
      if (!articleId) {
        wx.showToast({ title: '操作失败：文章ID无效', icon: 'none' });
        return;
      }
      try {
        if (this.properties.is_favorited) {
          // 取消收藏：调用 DELETE 接口
          this.setData({ animateStar: true });
          await request.deleteFavourite(this.properties.is_favorited);
          this.setData({ is_favorited: 0 });
          wx.showToast({ title: '取消收藏成功' });
          setTimeout(() => {
            this.setData({ animateStar: false });
          }, 300);
        } else {
          // 添加收藏：调用 POST 接口
          const articleData = {
            article_id: articleId,
            // 关联默认收藏夹（如果接口支持）
            collection_id: this.data.defaultCollection?.id || ''
          };
          this.setData({ animateStar: true });
          const response = await request.addFavourite(articleData);
          this.setData({ 
            is_favorited: response.id,
            currentFavoriteId: response.id // 记录收藏ID，用于后续移动
          });
          this.showFavTipPopup();
          setTimeout(() => {
            this.setData({ animateStar: false });
          }, 300);
        }
      } catch (err) {
        console.error('收藏操作失败：', err);
        wx.showToast({ title: err || '操作失败', icon: 'none' });
      }
    },
    /* 
    //收藏按钮，只显示动画
    async onFavourite() {
        const articleId = this.properties.id_;
        if (!articleId) {
          wx.showToast({ title: '操作失败：文章ID无效', icon: 'none' });
          return;
        }
      
        // 核心：直接反转现有 is_favorited 状态（0→1，1→0），无需新增变量
        const currentFavState = this.properties.is_favorited;
        const newFavState = currentFavState ? 0 : 1;
      
        try {
          // 1. 先更新状态（图标即时切换，优先满足视觉需求）
          this.setData({ is_favorited: newFavState });
          this.setData({ animateStar: true });
          wx.showToast({ title: newFavState ? '收藏成功' : '取消收藏成功' });
          setTimeout(() => {
            this.setData({ animateStar: false });
          }, 300);
      
          // 2. 调用Mock接口（成功与否不影响状态切换，忽略全局共享）
          if (newFavState) {
            // 收藏：传递必要字段调用接口（无需依赖返回ID）
            await request.addFavourite({ id: articleId });
          } else {
            // 取消收藏：用当前状态的ID（或直接传articleId，Mock不校验则不影响）
            await request.deleteFavourite(currentFavState || articleId);
          }
        } catch (err) {
          console.error('收藏接口调用失败（状态已切换）：', err);
          // 接口失败不回滚状态，仅提示（符合“只关心切换”的需求）
          wx.showToast({ title: '接口调用失败，状态已更新', icon: 'none' });
        }
      },
      */
    /**
     * 展开/收起逻辑（添加历史记录，对接 POST /api/user/history/）
     */

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
        this.setData({ tipTimer: timer });
      },

    // 打开收藏夹选择弹窗
    openCollectionSelect() {
        this.getCollectionList();
        // 清理定时器
        if (this.data.tipTimer) {
        clearTimeout(this.data.tipTimer);
        this.setData({ tipTimer: null });
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
          this.setData({ tipTimer: null });
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
        const { currentFavoriteId } = this.data;
        console.log('移动收藏', {
            currentFavoriteId, 
            targetCollectionId, 
            targetType: typeof targetCollectionId,
            collectionList: this.data.collectionList.map(item => item.id)
          });
        if (!currentFavoriteId || !targetCollectionId) {
            wx.showToast({ title: '参数错误', icon: 'none' });
            return;
        }
    
        try {
            wx.showLoading({ title: '移动中...' });
            // 调用移动收藏接口
            await request.moveFavourite(currentFavoriteId, targetCollectionId);
            wx.hideLoading();
            wx.showToast({ title: '移动成功' });
            // 关闭所有弹窗
            this.closeAllPopups();
        } catch (err) {
            wx.hideLoading();
            console.error('移动收藏失败：', err);
            wx.showToast({ title: err || '移动失败', icon: 'none' });
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
            wx.showToast({ title: '记录失败：文章ID无效', icon: 'none' });
            return;
          } try {
          // 添加历史记录：调用 POST 接口
          const historyData = {
            article_id: articleId,
          };
            await request.addHistory(historyData);
          } catch (err) {
            console.error('添加历史记录失败：', err);
            wx.showToast({ title: err || '记录失败', icon: 'none' });
          }
        }
        
        // 动画结束后清除动画状态
        setTimeout(() => {
          this.setData({
            isAnimating: false
          });
        }, 400); // 与CSS动画时间匹配
      }
  }
});