// ai-chat.js
const request = require('../../utils/request');

Page({
  data: {
    messages: [], // 消息列表
    inputText: '', // 输入框内容
    isLoading: false, // 是否正在加载
    scrollTop: 0, // 滚动位置
    iconUrl: '', // 缓存后的图片路径
    fallbackIconUrl: '' 
  },

  onLoad() {
    // 初始化欢迎消息
    this.setData({
      messages: [
        {
          type: 'ai',
          content: '你好！我是你的AI助手，有什么可以帮助你的吗？',
          time: this.getCurrentTime()
        }
      ]
    });
    this.getPetGifCache();
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

  // 发送消息
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
      time: this.getCurrentTime()
    };

    const messages = [...this.data.messages, userMessage];
    this.setData({
      messages,
      inputText: '',
      isLoading: true
    });

    // 滚动到底部
    this.scrollToBottom();

    try {
      // 调用AI接口
      const response = await request.chatWithAI({
        question: inputText
      });

      // 添加AI回复
      const aiMessage = {
        type: 'ai',
        content: response.answer || response.reply || response.message || '抱歉，我暂时无法理解你的问题。',
        referencesArticles: response['references-articles'] || [],
        time: this.getCurrentTime()
      };

      this.setData({
        messages: [...messages, aiMessage],
        isLoading: false
      });

      // 滚动到底部
      this.scrollToBottom();
    } catch (error) {
      console.error('AI对话失败：', error);
      wx.showToast({
        title: error || '发送失败，请重试',
        icon: 'none'
      });

      // 添加错误消息
      const errorMessage = {
        type: 'ai',
        content: '抱歉，发送消息时出现了错误，请稍后再试。',
        time: this.getCurrentTime()
      };

      this.setData({
        messages: [...messages, errorMessage],
        isLoading: false
      });
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
      // 对URL进行编码
      const encodedUrl = encodeURIComponent(url);
      console.log('打开文章链接：', url);
      wx.navigateTo({
        url: `/pages/webview/webview?url=${encodedUrl}`
      });
    }
  }
});

