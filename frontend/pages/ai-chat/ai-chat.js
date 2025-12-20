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
    streamTask: null
  },

  onLoad() {
    // 初始化欢迎消息
    this.setData({
      messages: [
        {
          type: 'ai',
          content: '你好！我是你的AI助手，有什么可以帮助你的吗？',
          nodes: [],
          time: this.getCurrentTime()
        }
      ]
    });
    this.setData({
      'messages[0].nodes': this.formatContentToNodes(this.data.messages[0].content)
    });
    this.getPetGifCache();
  },

  onUnload() {
    this.abortStreamTask();
  },

  getPetGifCache() {
    const gifUrl = 'https://403app.xyz/static/pet.gif';
    // 兼容app未定义的情况
    if (typeof app !== 'undefined' && app.getImgCache) {
      app.getImgCache(gifUrl).then((cachePath) => {
        this.setData({ petGifUrl: cachePath });
        console.log('pet.gif 缓存路径:', cachePath);
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

    // 添加用户消息
    const userMessage = {
      type: 'user',
      content: inputText,
      nodes: this.formatContentToNodes(inputText),
      time: this.getCurrentTime()
    };

    const messages = [...this.data.messages, userMessage];
    const aiMessage = {
      type: 'ai',
      content: '',
      nodes: [],
      referencesArticles: [],
      time: this.getCurrentTime()
    };

    const finalMessages = [...messages, aiMessage];

    this.setData({
      messages: finalMessages,
      inputText: '',
      isLoading: true
    });

    // 滚动到底部
    this.scrollToBottom();
    const aiIndex = finalMessages.length - 1;
    this.startStream(inputText, aiIndex);
  },

  // 启动流式请求
  startStream(question, aiIndex) {
    this.abortStreamTask();

    const task = request.chatWithAIStream({
      question,
      onMessage: (delta) => this.appendAIContent(aiIndex, delta),
      onReferences: (refs) => this.updateAIReferences(aiIndex, refs),
      onDone: () => this.finishStreaming(),
      onError: (err) => this.handleStreamError(err, aiIndex)
    });

    if (task && task.onChunkReceived) {
      this.setData({ streamTask: task });
    } else {
      // 回退到非流式接口
      this.fetchAIOnce(question, aiIndex);
    }
  },

  // 非流式兜底
  async fetchAIOnce(question, aiIndex) {
    try {
      const response = await request.chatWithAI({ question });
      this.updateAIMessage(aiIndex, response);
    } catch (error) {
      this.handleStreamError(error, aiIndex);
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
        [`messages[${index}].nodes`]: this.formatContentToNodes(next)
    });
    this.scrollToBottom();
  },

  updateAIReferences(index, refs = []) {
    if (!this.data.messages[index]) return;
    const key = `messages[${index}].referencesArticles`;
    this.setData({ [key]: refs });
  },

  updateAIMessage(index, response = {}) {
    const content = response.answer || response.reply || response.message || '抱歉，我暂时无法理解你的问题。';
    const refs = response['references-articles'] || response.referencesArticles || [];
    this.setData({
      [`messages[${index}].content`]: content,
      [`messages[${index}].nodes`]: this.formatContentToNodes(content),
      [`messages[${index}].referencesArticles`]: refs,
      isLoading: false,
      streamTask: null
    });
    this.scrollToBottom();
  },

  finishStreaming() {
    if (!this.data.isLoading) return;
    this.setData({
      isLoading: false,
      streamTask: null
    });
  },

  handleStreamError(error, aiIndex) {
    console.error('AI对话失败：', error);
    wx.showToast({
      title: error || '发送失败，请重试',
      icon: 'none'
    });

    if (this.data.messages[aiIndex]) {
      this.setData({
        [`messages[${aiIndex}].content`]: '抱歉，发送消息时出现了错误，请稍后再试。',
        [`messages[${aiIndex}].nodes`]: this.formatContentToNodes('抱歉，发送消息时出现了错误，请稍后再试。')
      });
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
            children.push({ type: 'text', text: line });
            if (lIdx !== lines.length - 1) {
                children.push({ name: 'br' });
            }
        });
        nodes.push({
            name: 'p',
            attrs: { style: 'margin: 0 0 12rpx 0;' },
            children
        });
        if (pIdx !== paragraphs.length - 1) {
            nodes.push({ name: 'br' });
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
            messages: [
              {
                type: 'ai',
                content: '对话已清空，有什么可以帮助你的吗？',
                nodes: this.formatContentToNodes('对话已清空，有什么可以帮助你的吗？'),
                time: this.getCurrentTime()
              }
            ]
          });
        }
      }
    });
  },

  // 返回上一页
  goBack() {
    wx.navigateBack();
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

