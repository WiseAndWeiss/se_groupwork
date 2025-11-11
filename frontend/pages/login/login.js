Page({
    data: {
      // 控制当前显示登录还是注册
      isLogin: true,
      
      // 登录表单数据
      loginData: {
        username: '',
        password: ''
      },
      
      // 注册表单数据
      registerData: {
        username: '',
        password: '',
        confirmPassword: ''
      }
    },
  
    // 切换到登录
    switchToLogin: function() {
      this.setData({
        isLogin: true
      });
    },
  
    // 切换到注册
    switchToRegister: function() {
      this.setData({
        isLogin: false
      });
    },
  
    // 登录表单输入处理
    onLoginUsernameInput: function(e) {
      this.setData({
        'loginData.username': e.detail.value
      });
    },
  
    onLoginPasswordInput: function(e) {
      this.setData({
        'loginData.password': e.detail.value
      });
    },
  
    // 注册表单输入处理
    onRegisterUsernameInput: function(e) {
      this.setData({
        'registerData.username': e.detail.value
      });
    },
  
    onRegisterPasswordInput: function(e) {
      this.setData({
        'registerData.password': e.detail.value
      });
    },
  
    onRegisterConfirmPasswordInput: function(e) {
      this.setData({
        'registerData.confirmPassword': e.detail.value
      });
    },
  
    // 登录处理
    handleLogin: function() {
      const { username, password } = this.data.loginData;
      
      // 简单的表单验证
      if (!username || !password) {
        wx.showToast({
          title: '请填写完整信息',
          icon: 'none'
        });
        return;
      }

      // 登录成功后的跳转
      wx.reLaunch({
        url: '/pages/home/home'
      });
      
      // 这里可以添加登录API调用
      console.log('登录数据:', this.data.loginData);
      wx.showToast({
        title: '登录成功',
        icon: 'success'
      });
    },
  
    // 注册处理
    handleRegister: function() {
      const { username, password, confirmPassword } = this.data.registerData;
      
      // 表单验证
      if (!username || !password || !confirmPassword) {
        wx.showToast({
          title: '请填写完整信息',
          icon: 'none'
        });
        return;
      }
      
      if (password !== confirmPassword) {
        wx.showToast({
          title: '两次密码输入不一致',
          icon: 'none'
        });
        return;
      }
      
      

      // 这里可以添加注册API调用
      console.log('注册数据:', this.data.registerData);
      wx.showToast({
        title: '注册成功',
        icon: 'success'
      });
      
      // 注册成功后的跳转
      wx.reLaunch({
        url: '/pages/home/home'
      });
    },
  
    onLoad: function() {
      // 页面加载时的初始化操作
      console.log('登录页面加载完成');
    }
  })