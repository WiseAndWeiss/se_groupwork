App({
    globalData: {
      petPosition: null, // 桌宠位置
      isPetDragging: false,// 桌宠是否正在拖动
      // 图片缓存配置
      imgCache: {
        // 缓存过期时间
        expireTime: 24 * 60 * 60 * 1000,
        // 图片地址映射
        imgMap: {
          'https://403app.xyz/static/icon.png': '/assets/icon.png',
          'https://403app.xyz/static/loading.gif': '/assets/loading.gif',
          'https://403app.xyz/static/pet.gif': '/assets/pet.gif'
        }
      }
    },
  
    onLaunch() {
      wx.hideTabBar({
        animation: false,
        success: () => console.log("tabBar 全局隐藏成功"),
        fail: (err) => console.log("tabBar 隐藏失败", err)
      });
      // 初始化时清理过期缓存
      this.clearExpiredImgCache();
    },
  
    /**
     * 获取图片缓存（核心方法）
     * @param {string} imgUrl - 网络图片地址
     * @returns {Promise<string>} 本地缓存路径
     */
    getImgCache(imgUrl) {
      return new Promise(async (resolve) => {
        const fallbackUrl = this.globalData.imgCache.imgMap[imgUrl] || imgUrl;
        if (!imgUrl) return resolve(fallbackUrl);
  
        try {
          // 读取本地缓存记录
          const cacheKey = `img_cache_${this.md5(imgUrl)}`; // md5避免key过长
          const cacheInfo = wx.getStorageSync(cacheKey);
  
          //  缓存存在且未过期，直接返回本地路径
          if (cacheInfo && cacheInfo.path) {
            const now = Date.now();
            if (now - cacheInfo.time < this.globalData.imgCache.expireTime) {
              // 验证文件是否存在（防止手动删除）
              const fileStat = await this.checkFileExist(cacheInfo.path);
              if (fileStat) return resolve(cacheInfo.path);
            }
          }
  
          // 缓存不存在/过期/文件丢失，下载图片并缓存
          const tempFilePath = await this.downloadImg(imgUrl);
          if (tempFilePath) {
            // 保存到本地文件系统（持久化，临时文件会被清理）
            const saveRes = await wx.saveFile({ tempFilePath });
            // 更新缓存记录
            wx.setStorageSync(cacheKey, {
              path: saveRes.savedFilePath,
              time: Date.now()
            });
            return resolve(saveRes.savedFilePath);
          } else {
            // 下载失败，返回兜底路径
            resolve(fallbackUrl);
          }
        } catch (err) {
          console.error('图片缓存处理失败：', err);
          resolve(this.globalData.imgCache.imgMap[imgUrl] || imgUrl);
        }
      });
    },
  
    /**
     * 下载网络图片
     * @param {string} url - 图片地址
     * @returns {Promise<string>} 临时文件路径
     */
    downloadImg(url) {
      return new Promise((resolve) => {
        wx.downloadFile({
          url,
          timeout: 10000, // 10秒超时
          success: (res) => {
            // 下载成功（状态码200）
            if (res.statusCode === 200) resolve(res.tempFilePath);
            else resolve('');
          },
          fail: () => resolve('') // 下载失败返回空
        });
      });
    },
  
    /**
     * 检查本地文件是否存在
     * @param {string} filePath - 文件路径
     * @returns {Promise<boolean>}
     */
    checkFileExist(filePath) {
      return new Promise((resolve) => {
        wx.getFileSystemManager().getFileInfo({
          filePath,
          success: () => resolve(true),
          fail: () => resolve(false)
        });
      });
    },
  
    /**
     * 清理过期的图片缓存
     */
    clearExpiredImgCache() {
      const now = Date.now();
      const expireTime = this.globalData.imgCache.expireTime;
      const storageInfo = wx.getStorageInfoSync();
  
      // 遍历所有本地存储key，筛选图片缓存key
      storageInfo.keys.forEach((key) => {
        if (key.startsWith('img_cache_')) {
          const cacheInfo = wx.getStorageSync(key);
          if (cacheInfo && now - cacheInfo.time > expireTime) {
            // 删除过期的缓存记录和文件
            wx.removeStorageSync(key);
            wx.removeSavedFile({ filePath: cacheInfo.path });
          }
        }
      });
    },
  
    /**
     * 简易MD5（用于生成唯一缓存key，可替换为更严谨的实现）
     * @param {string} str - 原始字符串
     * @returns {string} MD5摘要
     */
    md5(str) {
      let hash = 0;
      if (str.length === 0) return hash.toString();
      for (let i = 0; i < str.length; i++) {
        const char = str.charCodeAt(i);
        hash = ((hash << 5) - hash) + char;
        hash = hash & hash; // 转换为32位整数
      }
      return Math.abs(hash).toString(16);
    }
  });