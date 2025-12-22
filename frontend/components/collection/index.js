const request = require('../../utils/request');

const MAX_NAME_LENGTH = 10; // 标题最大10字
const MAX_DESC_LENGTH = 30; // 描述最大30字

Component({
  options: {
    addGlobalClass: true,
  },
  properties: {
    item: {
      type: Object,
      value: {},
      required: true
    }
  },

  data: {
    showEditPopup: false, // 底部升起的编辑浮窗
    tempName: '', // 临时存储修改的名称
    tempDesc: '', // 临时存储修改的描述
    remainNameCount: 10, // 标题最大10字
    remainDescCount: 30 // 描述最大30字
  },

  // 监听输入栏变化
  observers: {
    'item': function (newItem) {
      if (newItem) {
        // 初始化时截取超出的字符
        const initName = (newItem.name || '').substring(0, MAX_NAME_LENGTH);
        const initDesc = (newItem.description || '').substring(0, MAX_DESC_LENGTH);

        this.setData({
          tempName: initName,
          tempDesc: initDesc,
          remainNameCount: MAX_NAME_LENGTH - initName.length,
          remainDescCount: MAX_DESC_LENGTH - initDesc.length
        });
      }
    }
  },

  methods: {
    // 收藏夹卡片点击跳转方法
    navigateToCollectionDetail() {
      // 从properties中获取收藏夹ID和名称
      const collectionId = String(this.properties.item.id || '').trim();
      const collectionName = this.properties.item.name || '';

      if (!collectionId) {
        wx.showToast({
          title: '收藏夹ID无效',
          icon: 'none'
        });
        return;
      }

      // 拼接URL并跳转（encodeURIComponent处理特殊字符）
      wx.navigateTo({
        url: `/packageA/collection/collection?collectionid=${encodeURIComponent(collectionId)}&name=${encodeURIComponent(collectionName)}`
      });
    },

    // 点击编辑图标打开编辑浮窗
    openEditPopup() {
      const initName = (this.properties.item.name || '').substring(0, MAX_NAME_LENGTH);
      const initDesc = (this.properties.item.description || '').substring(0, MAX_DESC_LENGTH);

      this.setData({
        showEditPopup: true,
        tempName: initName,
        tempDesc: initDesc,
        remainNameCount: MAX_NAME_LENGTH - initName.length,
        remainDescCount: MAX_DESC_LENGTH - initDesc.length
      });
      // 通知父组件编辑弹窗已打开
      this.triggerEvent('editPopupOpened');
    },

    // 名称输入处理
    onNameInput(e) {
      const inputValue = e.detail.value.substring(0, MAX_NAME_LENGTH); // 强制截取不超10字
      this.setData({
        tempName: inputValue,
        remainNameCount: MAX_NAME_LENGTH - inputValue.length
      });
    },

    // 描述输入处理
    onDescInput(e) {
      const inputValue = e.detail.value.substring(0, MAX_DESC_LENGTH); // 强制截取不超30字
      this.setData({
        tempDesc: inputValue,
        remainDescCount: MAX_DESC_LENGTH - inputValue.length
      });
    },

    // 关闭底部编辑浮窗
    closeEditPopup() {
      this.setData({
        showEditPopup: false
      });
      // 通知父组件编辑弹窗已关闭
      this.triggerEvent('editPopupClosed');
    },

    // 保存收藏夹修改
    async saveCollectionEdit() {
      const collectionId = String(this.properties.item.id || '').trim();
      const {
        tempName,
        tempDesc
      } = this.data;

      // 名称不能为空
      if (!tempName.trim()) {
        wx.showToast({
          title: '收藏夹名称不能为空',
          icon: 'none'
        });
        return;
      }
      if (tempName.length > MAX_NAME_LENGTH) {
        wx.showToast({
          title: `名称不能超过${MAX_NAME_LENGTH}个字`,
          icon: 'none'
        });
        return;
      }
      if (tempDesc.length > MAX_DESC_LENGTH) {
        wx.showToast({
          title: `描述不能超过${MAX_DESC_LENGTH}个字`,
          icon: 'none'
        });
        return;
      }

      try {
        // 调用更新接口
        const updatedData = await request.updateCollection(collectionId, {
          name: tempName.trim(),
          description: tempDesc.trim()
        });
        // 更新成功
        wx.showToast({
          title: '修改成功',
          icon: 'success'
        });
        this.setData({
          showEditPopup: false
        });
        // 通知父组件编辑弹窗已关闭
        this.triggerEvent('editPopupClosed');
        // 刷新列表
        this.triggerEvent('collectionUpdated', {
          id: collectionId,
          data: updatedData
        });
      } catch (err) {
        console.error('更新收藏夹失败：', err);
        wx.showToast({
          title: err || '修改失败',
          icon: 'none'
        });
      }
    },

    // 删除收藏夹
    async deleteCollection() {
      const collectionId = String(this.properties.item.id || '').trim();
      const collectionName = this.properties.item.name || '该收藏夹';

      // 禁止删除默认收藏夹
      if (this.properties.item.is_default) {
        wx.showToast({
          title: '默认收藏夹不可删除',
          icon: 'none'
        });
        return;
      }

      // 二次确认删除
      wx.showModal({
        title: '确认删除',
        content: `是否删除收藏夹「${collectionName}」？删除后该收藏夹下的所有内容将一并移除`,
        cancelText: '取消',
        confirmText: '删除',
        confirmColor: '#ff4d4f',
        success: async (res) => {
          if (res.confirm) {
            try {
              wx.showLoading({
                title: '删除中...'
              });
              // 调用删除收藏夹接口
              await request.deleteCollection(collectionId);
              wx.hideLoading();
              wx.showToast({
                title: '删除成功',
                icon: 'success'
              });

              // 关闭浮窗
              this.setData({
                showEditPopup: false
              });
              // 通知父组件编辑弹窗已关闭
              this.triggerEvent('editPopupClosed');
              // 触发事件通知父组件刷新收藏夹列表
              this.triggerEvent('collectionDeleted', {
                id: collectionId
              });
            } catch (err) {
              wx.hideLoading();
              wx.showToast({
                title: err || '删除失败',
                icon: 'none'
              });
              console.error('删除收藏夹失败：', err);
            }
          }
        }
      });
    }
  }
});