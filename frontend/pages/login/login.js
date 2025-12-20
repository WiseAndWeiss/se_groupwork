const request = require('../../utils/request');
const app = getApp();

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
    },
    
    // 密码强度相关状态
    passwordStrength: '未输入',  // 强度文本：未输入/弱/中/强
    strengthClass: 'strength-default',  // 强度样式
    
    // 动画相关状态
    showLoadingAnimation: false,

    iconUrl: '', // 缓存后的图片路径
    fallbackIconUrl: '' 
  },

  // click() {
  //   wx.createSelectorQuery().select('#canvas').node(res => {
  //     const canvas = res.node
  //     const context = canvas.getContext('2d')
  //     canvas.width = 300
  //     canvas.height = 300
  //     lottie.setup(canvas)

  //     lottie.loadAnimation({
  //       loop: true,
  //       autoplay: true,
  //       path:'/assets/lottie/cycling.json',
  //       rendererSettings:{
  //         context
  //       }
  //     })
  //   }).exec()
  // },

  // 切换到登录
  switchToLogin: function() {
    this.setData({ isLogin: true });
  },

  // 切换到注册
  switchToRegister: function() {
    this.setData({ isLogin: false });
  },

  // 登录表单输入处理
  onLoginUsernameInput: function(e) {
    this.setData({ 'loginData.username': e.detail.value });
  },

  // 用户名输入框获得焦点时触发动画
  onLoginUsernameFocus: function() {
    this.playLoadingAnimation();
  },

  onLoginPasswordInput: function(e) {
    this.setData({ 'loginData.password': e.detail.value });
  },

  // 注册表单输入处理
  onRegisterUsernameInput: function(e) {
    this.setData({ 'registerData.username': e.detail.value });
  },

  // 注册用户名输入框获得焦点时触发动画
  onRegisterUsernameFocus: function() {
    this.playLoadingAnimation();
  },

  // 注册密码输入处理
  onRegisterPasswordInput: function(e) {
    const password = e.detail.value;
    // 更新密码数据
    this.setData({ 
        'registerData.password': password,
    });
    // 实时检测密码强度
    this.checkPasswordStrength(password);
  },

  onRegisterConfirmPasswordInput: function(e) {
    this.setData({ 'registerData.confirmPassword': e.detail.value });
  },
  
  // 检测密码中是否包含非法特殊字符
  hasIllegalSpecialChars: function(password) {
    // 允许的8种特殊字符
    const ALLOWED_SPECIAL_CHARS = '!@#$%^&*';
    const illegalCharRegex = new RegExp(`[^a-zA-Z0-9${ALLOWED_SPECIAL_CHARS}]`);
    return illegalCharRegex.test(password);
  },  

  // 密码强度检测方法
  checkPasswordStrength: function(password) {
    const minLen = 8;
    const maxLen = 16;
    const isLenTooShort = password.length < minLen;
    const isLenTooLong = password.length > maxLen;
    const isLenValid = !isLenTooShort && !isLenTooLong;
    const hasIllegalChars = this.hasIllegalSpecialChars(password);
    const optionalRules = [
      /\d/,             // 数字
      /[a-z]/,          // 小写字母
      /[A-Z]/,          // 大写字母
      /[!@#$%^&*]/    // 特殊字符
    ];

    // 计算得分
    let optionalPassedCount = 0; // 可选规则通过数量
    optionalRules.forEach(rule => {
      if (rule.test(password)) optionalPassedCount++;
    });
    
    // 根据得分判定强度和样式
    let passwordStrength = '';
    let strengthClass = '';

    if (password.length === 0) {
      passwordStrength = '未输入';
      strengthClass = 'strength-default';
    } else if (hasIllegalChars) {
        passwordStrength = '含非法特殊字符';
        strengthClass = 'strength-default'; 
    } else if (isLenTooShort || isLenTooLong) {
      passwordStrength = '密码应在8-16位之间';
      strengthClass = 'strength-default';
    } else if (optionalPassedCount < 2) {
      passwordStrength = '弱';
      strengthClass = 'strength-weak';
    } else if (optionalPassedCount === 2) {
      passwordStrength = '中';
      strengthClass = 'strength-medium';
    } else { 
      passwordStrength = '强';
      strengthClass = 'strength-strong';
    }

    // 更新强度状态到视图
    this.setData({ 
      passwordStrength, 
      strengthClass 
    });
  },

  // 登录处理
  handleLogin: async function() {
    const { username, password } = this.data.loginData;
    
    if (!username || !password) {
      wx.showToast({ title: '请填写完整信息', icon: 'none' });
      return;
    }

    try {
      await request.login({ username, password });
      wx.showToast({ title: '登录成功', icon: 'success' });
      wx.reLaunch({ url: '/pages/home/home' });
    } catch (err) {
      console.error('登录失败：', err);
      wx.showToast({ title: err || '登录失败', icon: 'none' });
    }
  },

  // 注册处理
  handleRegister: async function() {
    const { username, password, confirmPassword } = this.data.registerData;
    
    // 基础校验
    if (!username || !password || !confirmPassword) {
      wx.showToast({ title: '请填写完整信息', icon: 'none' });
      return;
    }
    if (password !== confirmPassword) {
      wx.showToast({ title: '两次密码输入不一致', icon: 'none' });
      return;
    }

    // 检测是否包含非法特殊字符
    const hasIllegalChars = this.hasIllegalSpecialChars(password);
    if (hasIllegalChars) {
      wx.showModal({
        title: '密码包含非法字符',
        content: `密码仅允许包含字母、数字和特殊字符：!@#$%^&*（共8种），请移除其他特殊字符（如？、！、￥等）`,
        showCancel: false,
        confirmText: '知道了'
      });
      return;
    }

    // 密码强度校验（长度为8-16，剩余条件四选二）
    const requiredRule = /.{8,16}/; // 长度>=8
    const optionalRules = [/\d/, /[a-z]/, /[A-Z]/, /[!@#$%^&*]/]; 
    const optionalPassedCount = optionalRules.filter(rule => rule.test(password)).length;
    
    if (!requiredRule.test(password) || optionalPassedCount < 2) {
      wx.showModal({
        title: '密码要求',
        content: '密码长度应不小于8位，且包含数字、大小写字母、特殊字符"!@#$%^&*"中至少2种',
        showCancel: false,
        confirmText: '知道了'
      });
      return;
    }

    try {
      await request.register({ username, password });
      wx.showToast({ title: '注册成功', icon: 'success' });
      // 注册成功后自动登录
      await request.login({ username, password });
      wx.reLaunch({ url: '/pages/home/home' });
    } catch (err) {
      console.error('注册失败：', err);
      wx.showToast({ title: err || '注册失败', icon: 'none' });
    }
  },

  onLoad: function() {
    console.log('登录页面加载完成');
    const targetImgUrl = 'https://403app.xyz/static/icon.png'; // 要缓存的网络图片地址
    app.getImgCache(targetImgUrl).then((cachePath) => {
      console.log('缓存图片路径：', cachePath);
      this.setData({ iconUrl: cachePath }); // 将缓存路径存入 data
    });
    this.tryAutoLogin();
  },

  async tryAutoLogin() {
    try {
      const autoLogin = await request.trySilentRefresh();
      if (autoLogin) {
        wx.showToast({ title: '已自动登录', icon: 'success' });
        wx.reLaunch({ url: '/pages/home/home' });
      }
    } catch (err) {
      console.log('自动登录失败：', err);
    }
  },

  // 播放加载动画
  playLoadingAnimation: function() {
    // 如果动画正在播放，不重复播放
    if (this.data.showLoadingAnimation) {
      return;
    }

    this.setData({ showLoadingAnimation: true });

    // 2秒后停止动画
    setTimeout(() => {
      this.setData({ showLoadingAnimation: false });
    }, 2000);
  }
});