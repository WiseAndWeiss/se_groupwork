const requestApi = require('../../../utils/request.js');

const MAX_NAME_LENGTH = 10; // 名称最大10字
const MAX_DESC_LENGTH = 30; // 描述最大30字

Page({
  data: {
    collectionList: [], // 收藏夹列表
    showCreatePopup: false, // 创建浮窗显隐
    hasEditPopupOpen: false, // 是否有编辑弹窗打开
    tempName: '', // 临时名称（默认：新建收藏夹n）
    tempDesc: '', // 临时描述
    remainNameCount: MAX_NAME_LENGTH, // 名称剩余字数
    remainDescCount: MAX_DESC_LENGTH // 描述剩余字数
  },

  onShow() {
    this.getCollectionList();
  },

  // 监听事件
  onFavouriteMoved() {
    this.getCollectionList();
    console.log('1111111111111');
  },

  onCollectionUpdated() {
    this.getCollectionList();
  },

  onCollectionDeleted() {
    this.getCollectionList();
  },

  // 监听编辑弹窗打开
  onEditPopupOpened() {
    this.setData({
      hasEditPopupOpen: true
    });
  },

  // 监听编辑弹窗关闭
  onEditPopupClosed() {
    this.setData({
      hasEditPopupOpen: false
    });
  },

  async getCollectionList() {
    wx.showLoading({
      title: '加载收藏夹...'
    });
    try {
      const res = await requestApi.getCollections();
      // 排序后赋值
      const sortedList = res.sort((a, b) => a.order - b.order);
      this.setData({
        collectionList: sortedList
      }, () => {
        console.log('收藏夹数量：', this.data.collectionList.length);
      });
    } catch (err) {
      wx.showToast({
        title: err || '加载失败',
        icon: 'error'
      });
      console.error('获取收藏夹失败：', err);
    } finally {
      wx.hideLoading();
    }
  },

  // 点击“添加收藏夹”
  handleAddCollection() {
    const {
      collectionList
    } = this.data;

    // 计算“新建收藏夹n”的最小n
    const newCollNames = collectionList
      .map(item => item.name)
      .filter(name => name.startsWith('新建收藏夹'));
    const usedNums = newCollNames.map(name => {
      const num = name.replace('新建收藏夹', '');
      return Number(num) || null;
    }).filter(num => !isNaN(num));
    let n = 1;
    while (usedNums.includes(n)) n++;
    const newCollName = `新建收藏夹${n}`;

    // 初始化创建浮窗的临时数据
    this.setData({
      showCreatePopup: true,
      tempName: newCollName,
      tempDesc: '',
      remainNameCount: MAX_NAME_LENGTH - newCollName.length,
      remainDescCount: MAX_DESC_LENGTH
    });
  },

  // 关闭创建
  closeCreatePopup() {
    this.setData({
      showCreatePopup: false,
      // 清空临时数据
      tempName: '',
      tempDesc: '',
      remainNameCount: MAX_NAME_LENGTH,
      remainDescCount: MAX_DESC_LENGTH
    });
  },

  // 浮窗名称
  onCreateNameInput(e) {
    const inputValue = e.detail.value.substring(0, MAX_NAME_LENGTH); // 不超10字
    this.setData({
      tempName: inputValue,
      remainNameCount: MAX_NAME_LENGTH - inputValue.length
    });
  },

  // 浮窗描述
  onCreateDescInput(e) {
    const inputValue = e.detail.value.substring(0, MAX_DESC_LENGTH); // 不超30字
    this.setData({
      tempDesc: inputValue,
      remainDescCount: MAX_DESC_LENGTH - inputValue.length
    });
  },

  // 新增：保存创建收藏夹（完成按钮）
  async saveCreateCollection() {
    const {
      collectionList,
      tempName,
      tempDesc
    } = this.data;

    // 校验：名称不能为空
    if (!tempName.trim()) {
      wx.showToast({
        title: '收藏夹名称不能为空',
        icon: 'none'
      });
      return;
    }
    // 校验：名称长度
    if (tempName.length > MAX_NAME_LENGTH) {
      wx.showToast({
        title: `名称不能超过${MAX_NAME_LENGTH}个字`,
        icon: 'none'
      });
      return;
    }

    wx.showLoading({
      title: '创建中...'
    });
    try {
      // 调用创建接口
      await requestApi.addCollection({
        name: tempName.trim(),
        description: tempDesc.trim(),
        is_default: false,
        order: collectionList.length > 0 ?
          Math.max(...collectionList.map(item => item.order)) + 1 :
          0
      });
      wx.showToast({
        title: '收藏夹创建成功',
        icon: 'success'
      });
      // 关闭浮窗+清空临时数据
      this.closeCreatePopup();
      // 刷新列表
      this.getCollectionList();
    } catch (err) {
      wx.showToast({
        title: err || '创建失败',
        icon: 'error'
      });
      console.error('添加收藏夹失败：', err);
    } finally {
      wx.hideLoading();
    }
  },

  goBack() {
    wx.navigateBack({
      delta: 1
    });
  }
});