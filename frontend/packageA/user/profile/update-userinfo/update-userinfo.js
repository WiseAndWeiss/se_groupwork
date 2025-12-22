const request = require('../../../../utils/request');

Page({
  data: {
    form: {
      avatar: '',
      username: '',
      email: '',
      phone_number: ''
    },
    // 悬浮窗显示状态
    showAvatarModal: false,
    showUsernameModal: false,
    showEmailModal: false,
    showPhoneModal: false,
    showPwdModal: false,
    // 临时存储修改的数据
    tempAvatar: '',
    tempUsername: '',
    tempEmail: '',
    tempPhone: '',
    tempOldPwd: '',
    tempNewPwd: '',
    tempConfirmPwd: ''
  },

  onLoad() {
    const eventChannel = this.getOpenerEventChannel();
    eventChannel.on('passUserInfo', (data) => {
      console.log('修改页面接收的数据：', data.userInfo);

      const userInfo = data.userInfo;
      if (userInfo.avatar) {
        userInfo.avatar = this.processAvatarUrl(userInfo.avatar);
      }
      this.setData({
        form: data.userInfo,
        // 初始化临时数据为当前值
        tempUsername: data.userInfo.username || '',
        tempEmail: data.userInfo.email || '',
        tempPhone: data.userInfo.phone_number || ''
      });
    });
  },

  // ========== 悬浮窗显示/隐藏 ==========
  showAvatarModal() {
    this.setData({
      showAvatarModal: true,
      tempAvatar: this.data.form.avatar
    });
  },
  hideAvatarModal() {
    this.setData({
      showAvatarModal: false
    });
  },
  showUsernameModal() {
    this.setData({
      showUsernameModal: true
    });
  },
  hideUsernameModal() {
    this.setData({
      showUsernameModal: false
    });
  },
  showEmailModal() {
    this.setData({
      showEmailModal: true
    });
  },
  hideEmailModal() {
    this.setData({
      showEmailModal: false
    });
  },
  showPhoneModal() {
    this.setData({
      showPhoneModal: true
    });
  },
  hidePhoneModal() {
    this.setData({
      showPhoneModal: false
    });
  },
  showPwdModal() {
    this.setData({
      showPwdModal: true,
      tempOldPwd: '',
      tempNewPwd: '',
      tempConfirmPwd: ''
    });
  },
  hidePwdModal() {
    this.setData({
      showPwdModal: false
    });
  },

  // ========== 临时数据输入处理 ==========
  handleTempUsernameInput(e) {
    this.setData({
      tempUsername: e.detail.value
    });
  },
  handleTempEmailInput(e) {
    this.setData({
      tempEmail: e.detail.value
    });
  },
  handleTempPhoneInput(e) {
    this.setData({
      tempPhone: e.detail.value
    });
  },
  handleTempOldPwdInput(e) {
    this.setData({
      tempOldPwd: e.detail.value
    });
  },
  handleTempNewPwdInput(e) {
    this.setData({
      tempNewPwd: e.detail.value
    });
  },
  handleTempConfirmPwdInput(e) {
    this.setData({
      tempConfirmPwd: e.detail.value
    });
  },

  // ========== 头像选择与修改 ==========

  processAvatarUrl(url) {
    if (!url) return '';
    // 如果是本地临时路径，直接返回
    if (url.startsWith('wxfile://') || url.startsWith('http://tmp/')) {
      return url;
    }
    // 如果已经是完整URL，直接返回
    if (url.startsWith('http')) {
      return url;
    }
    // 如果是相对路径，拼接完整URL
    if (url.startsWith('/')) {
      return 'https://' + url;
    }
    // 其他情况，可能是服务器返回的相对路径
    return 'https://' + url;
  },
  chooseTempAvatar() {
    wx.chooseImage({
      count: 1,
      sourceType: ['album', 'camera'],
      success: (res) => {
        this.setData({
          tempAvatar: res.tempFilePaths[0]
        });
      }
    });
  },
  async confirmAvatarUpdate() {
    if (!this.data.tempAvatar) {
      wx.showToast({
        title: '请选择头像',
        icon: 'none'
      });
      return;
    }
    try {
      wx.showLoading({
        title: '修改中...'
      });
      const res = await request.updateAvatar(this.data.tempAvatar);
      if (res && res.error) {
        this.showErrorModal('头像修改失败', res.error);
        return;
      }
      this.setData({
        'form.avatar': this.data.tempAvatar,
        showAvatarModal: false
      });
      wx.showToast({
        title: '头像修改成功',
        icon: 'success'
      });
    } catch (err) {
      const errorMsg = this.extractErrorMessage(err);
      this.showErrorModal('头像修改失败', errorMsg);
      console.error('头像修改失败：', err);
    } finally {
      wx.hideLoading();
    }
  },

  // ========== 用户名修改 ==========
  validateUsername() {
    const {
      tempUsername
    } = this.data;
    if (!tempUsername) {
      wx.showToast({
        title: '请输入昵称',
        icon: 'none'
      });
      return false;
    }
    if (tempUsername.length < 2 || tempUsername.length > 10) {
      wx.showToast({
        title: '昵称长度需2-10字',
        icon: 'none'
      });
      return false;
    }
    return true;
  },
  async confirmUsernameUpdate() {
    if (!this.validateUsername()) return;
    try {
      wx.showLoading({
        title: '修改中...'
      });
      const res = await request.updateUsername({
        new_username: this.data.tempUsername.trim()
      });
      if (res && res.error) {
        this.showErrorModal('昵称修改失败', res.error);
        return;
      }
      this.setData({
        'form.username': this.data.tempUsername.trim(),
        showUsernameModal: false
      });
      wx.showToast({
        title: '昵称修改成功',
        icon: 'success'
      });
    } catch (err) {
      const errorMsg = this.extractErrorMessage(err);
      this.showErrorModal('昵称修改失败', errorMsg);
      console.error('昵称修改失败：', err);
    } finally {
      wx.hideLoading();
    }
  },

  // ========== 邮箱修改 ==========
  validateEmail() {
    const {
      tempEmail
    } = this.data;
    if (!tempEmail) {
      wx.showToast({
        title: '请输入邮箱',
        icon: 'none'
      });
      return false;
    }
    // 简单邮箱格式验证
    const emailReg = /^[a-zA-Z0-9._%-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
    if (!emailReg.test(tempEmail)) {
      wx.showToast({
        title: '请输入合法邮箱',
        icon: 'none'
      });
      return false;
    }
    return true;
  },
  async confirmEmailUpdate() {
    if (!this.validateEmail()) return;
    try {
      wx.showLoading({
        title: '修改中...'
      });
      const res = await request.updateEmail({
        new_email: this.data.tempEmail.trim()
      });
      if (res && res.error) {
        this.showErrorModal('邮箱修改失败', res.error);
        return;
      }
      this.setData({
        'form.email': this.data.tempEmail.trim(),
        showEmailModal: false
      });
      wx.showToast({
        title: '邮箱修改成功',
        icon: 'success'
      });
    } catch (err) {
      const errorMsg = this.extractErrorMessage(err);
      this.showErrorModal('邮箱修改失败', errorMsg);
      console.error('邮箱修改失败：', err);
    } finally {
      wx.hideLoading();
    }
  },

  // ========== 手机号修改 ==========
  validatePhone() {
    const {
      tempPhone
    } = this.data;
    if (!tempPhone) {
      wx.showToast({
        title: '请输入手机号',
        icon: 'none'
      });
      return false;
    }
    if (tempPhone.length !== 11) {
      wx.showToast({
        title: '请输入11位手机号',
        icon: 'none'
      });
      return false;
    }
    return true;
  },
  async confirmPhoneUpdate() {
    if (!this.validatePhone()) return;
    try {
      wx.showLoading({
        title: '修改中...'
      });
      const res = await request.updatePhone({
        new_phone: this.data.tempPhone.trim()
      });
      if (res && res.error) {
        this.showErrorModal('手机号修改失败', res.error);
        return;
      }
      this.setData({
        'form.phone_number': this.data.tempPhone.trim(),
        showPhoneModal: false
      });
      wx.showToast({
        title: '手机号修改成功',
        icon: 'success'
      });
    } catch (err) {
      const errorMsg = this.extractErrorMessage(err);
      this.showErrorModal('手机号修改失败', errorMsg);
      console.error('手机号修改失败：', err);
    } finally {
      wx.hideLoading();
    }
  },

  // ========== 密码修改 ==========
  hasIllegalSpecialChars(password) {
    const allowedRegex = /^[a-zA-Z0-9!@#$%^&*]+$/;
    return !allowedRegex.test(password);
  },
  validatePwd() {
    const {
      tempOldPwd,
      tempNewPwd,
      tempConfirmPwd
    } = this.data;
    if (!tempOldPwd || !tempNewPwd || !tempConfirmPwd) {
      wx.showToast({
        title: '请填写完整密码信息',
        icon: 'none'
      });
      return false;
    }
    if (tempNewPwd !== tempConfirmPwd) {
      wx.showToast({
        title: '两次新密码输入不一致',
        icon: 'none'
      });
      return false;
    }
    if (this.hasIllegalSpecialChars(tempNewPwd)) {
      wx.showModal({
        title: '密码包含非法字符',
        content: '密码仅允许包含字母、数字和特殊字符：!@#$%^&*，请移除其他特殊字符',
        showCancel: false
      });
      return false;
    }
    if (tempNewPwd.length < 8 || tempNewPwd.length > 16) {
      wx.showToast({
        title: '新密码长度应在8-16位之间',
        icon: 'none'
      });
      return false;
    }
    const optionalRules = [/\d/, /[a-z]/, /[A-Z]/, /[!@#$%^&*]/];
    const optionalPassedCount = optionalRules.filter(rule => rule.test(tempNewPwd)).length;
    if (optionalPassedCount < 2) {
      wx.showModal({
        title: '密码强度不足',
        content: '新密码需包含数字、大小写字母、特殊字符中至少两种类型',
        showCancel: false
      });
      return false;
    }
    return true;
  },
  async confirmPwdUpdate() {
    if (!this.validatePwd()) return;
    try {
      wx.showLoading({
        title: '修改中...'
      });
      const res = await request.updatePassword({
        old_password: this.data.tempOldPwd,
        new_password: this.data.tempNewPwd,
        confirm_password: this.data.tempConfirmPwd
      });
      if (res && res.error) {
        this.showErrorModal('密码修改失败', res.error);
        return;
      }
      this.setData({
        showPwdModal: false
      });
      wx.showToast({
        title: '密码修改成功',
        icon: 'success'
      });
      setTimeout(() => {
        wx.navigateBack();
      }, 1000);
    } catch (err) {
      const errorMsg = this.extractErrorMessage(err);
      this.showErrorModal('密码修改失败', errorMsg);
      console.error('密码修改失败：', err);
    } finally {
      wx.hideLoading();
    }
  },

  // ========== 新增：统一错误信息提取方法 ==========
  extractErrorMessage(err) {
    // 优先从响应数据中提取错误信息[1,4](@ref)
    if (err && err.data && err.data.error) {
      return err.data.error;
    }
    // 处理HTTP 400状态码的响应[7](@ref)
    if (err && err.statusCode === 400 && err.data && err.data.error) {
      return err.data.error;
    }
    // 检查错误对象本身的error属性
    if (err && err.error) {
      return err.error;
    }
    // 检查错误消息
    if (err && err.message) {
      return err.message;
    }
    // 检查errMsg（微信小程序API错误常见字段）
    if (err && err.errMsg) {
      return err.errMsg;
    }
    // 默认错误信息
    return '操作失败，请重试';
  },

  // ========== 新增：统一错误提示方法 ==========
  showErrorModal(title, content) {
    wx.showModal({
      title: title,
      content: content,
      showCancel: false,
      confirmText: '知道了'
    });
  },

  // 返回上一页
  goBack() {
    wx.navigateBack();
  }
});