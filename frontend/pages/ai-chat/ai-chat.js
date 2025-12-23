// ai-chat.js
const request = require('../../utils/request');

Page({
  data: {
    messages: [], // 消息列表
    inputText: '', // 输入框内容
    isLoading: false, // 是否正在加载
    scrollTop: 0, // 滚动位置
    iconUrl: '', // 缓存后的图片路径
    fallbackIconUrl: '',
    streamTask: null,
    userAvatar: '', // 用户头像URL
    thinkingTimer: null, // 思考时间定时器
  },

  onLoad() {
    // 初始化欢迎消息
    this.setData({
      messages: [{
        type: 'ai',
        content: '你好！我是你的AI助手，有什么可以帮助你的吗？',
        nodes: [],
        time: this.getCurrentTime()
      }]
    });
    this.setData({
      'messages[0].nodes': this.formatContentToNodes(this.data.messages[0].content)
    });
    this.getPetGifCache();
    this.loadUserAvatar();
  },

  onUnload() {
    this.abortStreamTask();
    this.clearThinkingTimer();
  },

  // 页面返回拦截（微信小程序不支持，使用onHide或goBack）
  onHide() {
    // 页面隐藏时不清理，保持数据
  },

  // 清除思考时间定时器
  clearThinkingTimer() {
    if (this.data.thinkingTimer) {
      clearInterval(this.data.thinkingTimer);
      this.setData({
        thinkingTimer: null
      });
    }
  },

  // 开始思考时间计时
  startThinkingTimer(aiIndex, startTime) {
    // 清除之前的定时器
    this.clearThinkingTimer();

    // 每秒更新一次思考时间
    const timer = setInterval(() => {
      const thinkingTime = this.calculateThinkingTime(startTime);
      if (thinkingTime) {
        this.setData({
          [`messages[${aiIndex}].thinkingTime`]: thinkingTime
        });
      }
    }, 1000); // 每秒更新一次

    this.setData({
      thinkingTimer: timer
    });
  },

  getPetGifCache() {
    const gifUrl = 'https://403app.xyz/static/pet.gif';
    // 兼容app未定义的情况
    if (typeof app !== 'undefined' && app.getImgCache) {
      app.getImgCache(gifUrl).then((cachePath) => {
        this.setData({
          petGifUrl: cachePath
        });
        console.log('pet.gif 缓存路径:', cachePath);
      });
    }
  },

  // 加载用户头像
  async loadUserAvatar() {
    try {
      const userInfo = await request.getProfile();
      console.log('获取到的用户信息:', userInfo);

      // 获取头像URL，检查多个可能的字段名
      let avatarUrl = userInfo.avatar || userInfo.avatarUrl || '';

      // 处理头像URL
      if (avatarUrl) {
        // 如果已经是完整URL（http/https开头），直接使用
        if (avatarUrl.startsWith('http://') || avatarUrl.startsWith('https://')) {
          this.setData({
            userAvatar: avatarUrl
          });
        }
        // 如果是相对路径（以/开头），添加域名前缀
        else if (avatarUrl.startsWith('/')) {
          this.setData({
            userAvatar: `https://${avatarUrl}`
          });
        } else {
          this.setData({
            userAvatar: `https://${avatarUrl}`
          });
        }
        console.log('设置用户头像URL:', this.data.userAvatar);
      } else {
        console.log('用户未设置头像，使用默认文字');
        this.setData({
          userAvatar: ''
        });
      }
    } catch (err) {
      console.error('加载用户头像失败:', err);
      // 失败时使用空字符串，显示默认文字头像
      this.setData({
        userAvatar: ''
      });
    }
  },

  // 获取当前时间
  getCurrentTime() {
    const now = new Date();
    const hours = String(now.getHours()).padStart(2, '0');
    const minutes = String(now.getMinutes()).padStart(2, '0');
    return `${hours}:${minutes}`;
  },

  // 输入框内容改变
  onInputChange(e) {
    this.setData({
      inputText: e.detail.value
    });
  },

  // 发送消息（流式优先）
  async sendMessage() {
    const inputText = this.data.inputText.trim();
    if (!inputText) {
      wx.showToast({
        title: '请输入消息',
        icon: 'none'
      });
      return;
    }

    if (this.data.isLoading) {
      return;
    }

    // 记录开始时间
    const startTime = Date.now();

    // 添加用户消息
    const userMessage = {
      type: 'user',
      content: inputText,
      nodes: this.formatContentToNodes(inputText),
      time: this.getCurrentTime()
    };

    const messages = [...this.data.messages, userMessage];

    // 先添加一个 loading 状态的 AI 消息
    const loadingMessage = {
      type: 'ai',
      content: '',
      nodes: [],
      referencesArticles: [],
      time: this.getCurrentTime(),
      isLoading: true, // 标记为加载中
      startTime: startTime, // 记录开始时间
      thinkingTime: '' // 初始化思考时间
    };

    const finalMessages = [...messages, loadingMessage];

    this.setData({
      messages: finalMessages,
      inputText: '',
      isLoading: true
    });

    // 滚动到底部
    this.scrollToBottom();
    const aiIndex = finalMessages.length - 1;

    // 立即开始显示思考时间（每秒更新）
    this.startThinkingTimer(aiIndex, startTime);

    // 开始流式请求
    this.startStream(inputText, aiIndex, startTime);
  },

  // 启动流式请求
  startStream(question, aiIndex, startTime) {
    this.abortStreamTask();

    const task = request.chatWithAIStream({
      question,
      onMessage: (delta) => this.appendAIContent(aiIndex, delta),
      onReferences: (refs) => this.updateAIReferences(aiIndex, refs),
      onDone: () => {
        // 从消息对象中获取 startTime
        const message = this.data.messages[aiIndex];
        const msgStartTime = message ? message.startTime : startTime;
        this.finishStreaming(msgStartTime, aiIndex);
      },
      onError: (err) => {
        // 从消息对象中获取 startTime
        const message = this.data.messages[aiIndex];
        const msgStartTime = message ? message.startTime : startTime;
        this.handleStreamError(err, aiIndex, msgStartTime);
      }
    });

    if (task && task.onChunkReceived) {
      this.setData({
        streamTask: task
      });
    } else {
      // 回退到非流式接口
      this.fetchAIOnce(question, aiIndex, startTime);
    }
  },

  // 非流式兜底
  async fetchAIOnce(question, aiIndex, startTime) {
    try {
      const response = await request.chatWithAI({
        question
      });
      this.updateAIMessage(aiIndex, response, startTime);
    } catch (error) {
      this.handleStreamError(error, aiIndex, startTime);
    }
  },

  appendAIContent(index, delta = '') {
    if (!delta || !this.data.messages[index]) return;

    // 关键修改：将流式返回的 \n 转换为实际换行符
    const processedDelta = delta.replace(/\\n/g, '\n');

    const key = `messages[${index}].content`;
    const next = `${this.data.messages[index].content || ''}${processedDelta}`;
    this.setData({
      [key]: next,
      [`messages[${index}].nodes`]: this.formatContentToNodes(next),
      [`messages[${index}].isLoading`]: false // 确保移除 loading 状态
      // 注意：思考时间继续显示，由定时器更新
    });
    this.scrollToBottom();
  },

  // 计算并格式化思考时间
  calculateThinkingTime(startTime) {
    if (!startTime) return '';
    const endTime = Date.now();
    const duration = Math.round((endTime - startTime) / 1000); // 转换为秒
    return duration > 0 ? `已思考 ${duration} 秒` : '';
  },

  updateAIReferences(index, refs = []) {
    if (!this.data.messages[index]) return;
    const key = `messages[${index}].referencesArticles`;
    this.setData({
      [key]: refs
    });
  },

  updateAIMessage(index, response = {}, startTime) {
    const content = response.answer || response.reply || response.message || '抱歉，我暂时无法理解你的问题。';
    const refs = response['references-articles'] || response.referencesArticles || [];

    // 清除思考时间定时器
    this.clearThinkingTimer();

    this.setData({
      [`messages[${index}].content`]: content,
      [`messages[${index}].nodes`]: this.formatContentToNodes(content),
      [`messages[${index}].referencesArticles`]: refs,
      [`messages[${index}].isLoading`]: false, // 移除 loading 状态
      [`messages[${index}].thinkingTime`]: '', // 隐藏思考时间
      isLoading: false,
      streamTask: null
    });
    this.scrollToBottom();
  },

  finishStreaming(startTime, aiIndex) {
    if (!this.data.isLoading) return;

    // 清除思考时间定时器
    this.clearThinkingTimer();

    // 隐藏思考时间显示
    if (this.data.messages[aiIndex]) {
      this.setData({
        [`messages[${aiIndex}].thinkingTime`]: ''
      });
    }

    this.setData({
      isLoading: false,
      streamTask: null
    });
  },

  handleStreamError(error, aiIndex, startTime) {
    console.error('AI对话失败：', error);

    // 清除思考时间定时器
    this.clearThinkingTimer();

    // 检查是否为503状态码
    if (error.statusCode === 503) {
      // 直接让AI回复“接口繁忙，请稍后再试”
      this.setData({
        [`messages[${aiIndex}].content`]: '接口繁忙，请稍后再试',
        [`messages[${aiIndex}].nodes`]: this.formatContentToNodes('接口繁忙，请稍后再试'),
        [`messages[${aiIndex}].isLoading`]: false,
        [`messages[${aiIndex}].thinkingTime`]: ''
      });
    } else {
      wx.showToast({
        title: error.message || error || '发送失败，请重试',
        icon: 'none'
      });

      if (this.data.messages[aiIndex]) {
        this.setData({
          [`messages[${aiIndex}].content`]: '抱歉，发送消息时出现了错误，请稍后再试。',
          [`messages[${aiIndex}].nodes`]: this.formatContentToNodes('抱歉，发送消息时出现了错误，请稍后再试。'),
          [`messages[${aiIndex}].isLoading`]: false,
          [`messages[${aiIndex}].thinkingTime`]: ''
        });
      }
    }

    this.setData({
      isLoading: false,
      streamTask: null
    });
  },

  formatContentToNodes(content = '') {
    // 关键修改：将字面的 \n 字符串转换为实际的换行符
    let processedContent = String(content || '');

    // 将字面的 \n 转换为实际的换行符
    processedContent = processedContent.replace(/\\n/g, '\n');

    const paragraphs = processedContent.split(/\n\s*\n/); // 按空行切段
    const nodes = [];
    paragraphs.forEach((para, pIdx) => {
      const lines = para.split('\n');
      const children = [];
      lines.forEach((line, lIdx) => {
        children.push({
          type: 'text',
          text: line
        });
        if (lIdx !== lines.length - 1) {
          children.push({
            name: 'br'
          });
        }
      });
      nodes.push({
        name: 'p',
        attrs: {
          style: 'margin: 0 0 12rpx 0;'
        },
        children
      });
      if (pIdx !== paragraphs.length - 1) {
        nodes.push({
          name: 'br'
        });
      }
    });
    return nodes;
  },

  abortStreamTask() {
    if (this.data.streamTask && this.data.streamTask.abort) {
      this.data.streamTask.abort();
    }
  },

  // 滚动到底部
  scrollToBottom() {
    setTimeout(() => {
      const query = wx.createSelectorQuery();
      query.select('.message-list').boundingClientRect();
      query.exec((res) => {
        if (res[0]) {
          this.setData({
            scrollTop: res[0].height || 99999
          });
        }
      });
    }, 100);
  },

  // 清空对话
  clearChat() {
    wx.showModal({
      title: '提示',
      content: '确定要清空所有对话吗？',
      success: (res) => {
        if (res.confirm) {
          this.setData({
            messages: [{
              type: 'ai',
              content: '对话已清空，有什么可以帮助你的吗？',
              nodes: this.formatContentToNodes('对话已清空，有什么可以帮助你的吗？'),
              time: this.getCurrentTime()
            }]
          });
        }
      }
    });
  },

  // 返回上一页
  goBack() {
    // 弹出确认框
    wx.showModal({
      title: '退出确认',
      content: '退出后历史记录将不保留，确定要退出吗？',
      confirmText: '退出',
      cancelText: '取消',
      confirmColor: '#7b2ff7',
      success: (res) => {
        if (res.confirm) {
          // 用户确认退出，清理数据并返回
          this.abortStreamTask();
          this.clearThinkingTimer();
          wx.navigateBack();
        }
        // 用户取消，不做任何操作，留在当前页面
      }
    });
  },

  // 打开文章链接
  openArticle(e) {
    const url = e.currentTarget.dataset.url;
    if (url) {
      const encodedUrl = encodeURIComponent(url);
      console.log('打开文章链接：', url);
      wx.navigateTo({
        url: `/pages/webview/webview?url=${encodedUrl}`
      });
    }
  }
});