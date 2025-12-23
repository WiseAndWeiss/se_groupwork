const baseUrl = 'https://403app.xyz/api';
export const resourceUrl = "https://403app.xyz/";

// 兼容 TextDecoder 不可用的场景，保证流式响应可读
const decodeBuffer = (buffer) => {
  try {
    return new TextDecoder('utf-8').decode(buffer);
  } catch (err) {
    let result = '';
    const view = new Uint8Array(buffer || []);
    for (let i = 0; i < view.length; i += 1) {
      result += String.fromCharCode(view[i]);
    }
    try {
      return decodeURIComponent(escape(result));
    } catch (e) {
      return result;
    }
  }
};

let access_token = wx.getStorageSync('access_token') || '';
let refresh_token = wx.getStorageSync('refresh_token') || '';
const LOGIN_URL = '/user/auth/login/';
const REGISTER_URL = '/user/auth/register/';
const TOKEN_REFRESH_URL = '/user/auth/token/refresh/';
let refreshPromise = null;
const MOCK_ENABLE = false; // 核心：关闭Mock，启用真实后端请求
const mockApi = require('./mockConfig.js'); // 保留（若需临时开启Mock）

const shouldSkipAuthHeader = (url) => [LOGIN_URL, REGISTER_URL, TOKEN_REFRESH_URL].includes(url);

const persistTokens = ({
  access,
  refresh
}) => {
  if (refresh) {
    refresh_token = refresh;
    wx.setStorageSync('refresh_token', refresh);
  }
  if (access) {
    access_token = access;
    wx.setStorageSync('access_token', access);
  }
};

const clearTokens = () => {
  access_token = '';
  refresh_token = '';
  wx.removeStorageSync('access_token');
  wx.removeStorageSync('refresh_token');
};

const refreshAccessToken = () => {
  if (!refresh_token) {
    return Promise.reject('缺少 refresh token');
  }

  if (refreshPromise) return refreshPromise;

  refreshPromise = new Promise((resolve, reject) => {
    wx.request({
      url: `${baseUrl}${TOKEN_REFRESH_URL}`,
      method: 'POST',
      data: {
        refresh: refresh_token
      },
      header: {
        'Content-Type': 'application/json'
      },
      success: (res) => {
        if (res.statusCode >= 200 && res.statusCode < 300 && (res.data?.access || res.data?.refresh)) {
          persistTokens({
            access: res.data.access,
            refresh: res.data.refresh
          });
          resolve(res.data.access || access_token);
          return;
        }
        clearTokens();
        reject(res.data?.detail || res.data?.message || '刷新失败');
      },
      fail: (err) => {
        clearTokens();
        reject(err.errMsg || '网络失败');
      }
    });
  }).finally(() => {
    refreshPromise = null;
  });

  return refreshPromise;
};

const trySilentRefresh = async () => {
  if (!refresh_token) return false;
  try {
    await refreshAccessToken();
    return true;
  } catch (err) {
    return false;
  }
};

const request = (url, method = 'GET', data = {}, isFileUpload = false) => {
  return new Promise((resolve, reject) => {
    const needAuthHeader = !shouldSkipAuthHeader(url);

    // 检查是否是文件上传请求（通过特殊字段标识）
    if (!MOCK_ENABLE && data.__isFileUpload) {
      // 确保 data 是对象类型
      const uploadData = typeof data === 'string' ? {
        filePath: data
      } : data;

      // 提取必要的参数
      const filePath = uploadData.filePath;
      const fieldName = uploadData.fieldName || 'file';
      const formData = uploadData.formData || {};

      // 验证 filePath 是否为字符串
      if (typeof filePath !== 'string') {
        reject('filePath 必须是字符串类型');
        return;
      }

      const upload = (isRetry = false) => new Promise((resolveUpload, rejectUpload) => {
        wx.uploadFile({
          url: `${baseUrl}${url}`,
          filePath: filePath,
          name: fieldName, // 动态字段名
          header: {
            ...(needAuthHeader && access_token ? {
              'Authorization': `Bearer ${access_token}`
            } : {})
          },
          formData: formData,
          success: (res) => {
            if (res.statusCode >= 200 && res.statusCode < 300) {
              try {
                resolveUpload(JSON.parse(res.data));
              } catch (e) {
                resolveUpload(res.data);
              }
              return;
            }

            if (res.statusCode === 401 && needAuthHeader && refresh_token && !isRetry) {
              refreshAccessToken()
                .then(() => upload(true).then(resolveUpload).catch(rejectUpload))
                .catch((err) => rejectUpload(err || '登录已过期，请重新登录'));
              return;
            }

            if (res.statusCode === 413) {
              rejectUpload({
                statusCode: res.statusCode,
                data: '文件过大，头像不能超过1MB',
                error: '文件过大，头像不能超过1MB',
                message: '上传失败'
              });
              return;
            }

            let errorMsg = '上传失败';
            if (res.data) {
              try {
                const parsedData = typeof res.data === 'string' ? JSON.parse(res.data) : res.data;
                errorMsg = parsedData.error || parsedData.detail || parsedData.message || '上传失败';
              } catch (e) {
                errorMsg = res.data;
              }
            }

            rejectUpload({
              statusCode: res.statusCode,
              data: res.data,
              error: errorMsg,
              message: errorMsg
            });
          },
          fail: (err) => {
            rejectUpload({
              statusCode: 0,
              data: null,
              error: err.errMsg || '网络失败',
              message: err.errMsg || '网络失败'
            });
          }
        });
      });

      upload().then(resolve).catch(reject);
      return;
    }
    if (MOCK_ENABLE) {
      // 推荐文章 Mock 匹配 /api/articles/recommended
      if (url === '/articles/recommended' && method === 'GET') {
        setTimeout(() => {
          const res = mockApi.mockGetRecommendedArticles();
          console.log('Mock - 推荐文章返回：', res);
          res.code === 200 ? resolve(res.data) : reject(res.msg);
        }, 200);
        return;
      }
      // 首页最新文章 Mock 匹配 /api/articles/latest/
      if (url === '/articles/latest/' && method === 'GET') {
        setTimeout(() => {
          const res = mockApi.mockGetLatestArticles();
          console.log('Mock - 首页文章返回：', res);
          res.code === 200 ? resolve(res.data) : reject(res.msg);
        }, 200);
        return;
      }
      // 自选最新文章 Mock 匹配 /api/articles/customized-latest/
      if (url === '/articles/customized-latest/' && method === 'GET') {
        setTimeout(() => {
          const res = mockApi.mockGetCustomizedLatestArticles();
          console.log('Mock - 自选文章返回：', res);
          res.code === 200 ? resolve(res.data) : reject(res.msg);
        }, 200);
        return;
      }

      // 校园最新文章 Mock 匹配 /api/articles/campus-latest/
      if (url === '/articles/campus-latest/' && method === 'GET') {
        setTimeout(() => {
          const res = mockApi.mockGetCampusLatestArticles();
          console.log('Mock 返回：', res); // 添加调试日志
          res.code === 200 ? resolve(res.data) : reject(res.msg);
        }, 200);
        return;
      }

      // 筛选文章 Mock 匹配 /api/articles/filter/
      if (url === '/articles/filter/' && method === 'POST') {
        setTimeout(() => {
          const res = mockApi.mockGetFilteredArticles(data);
          console.log('Mock - 筛选文章返回：', res);
          res.code === 200 ? resolve(res.data) : reject(res.msg);
        }, 200);
        return;
      }

      if (url === '/articles/by-account/' && method === 'GET' && data.accountId) {
        setTimeout(() => {
          // 从Mock文章库中筛选对应公众号的文章
          const articles = mockAccountArticles.filter(item => item.accountId === data.accountId);
          // 按时间倒序排列（最新文章在前）（在后端筛选）
          articles.sort((a, b) => new Date(b.time) - new Date(a.time));
          resolve({
            list: articles,
            total: articles.length
          });
        }, 200);
        return;
      }
      // 获取校园公众号列表（GET /api/campus-accounts/）
      if (url === '/webspider/public-accounts/campus' && method === 'GET') {
        setTimeout(() => {
          console.log('Mock - 命中校园公众号列表请求，返回 Mock 数据');
          const res = mockApi.mockGetCampusAccounts(); // 复用原 Mock 数据方法
          // 关键：组件需要直接接收数组（list），而非嵌套对象，所以返回 res.data.list
          res.code === 200 ? resolve(res.data.list) : reject(res.msg);
        }, 200);
        return;
      }
      // 获取订阅列表（GET /api/user/subscriptions/）
      if (url === '/user/subscriptions/' && method === 'GET') {
        setTimeout(() => {
          const res = mockApi.mockGetSubscriptions();
          resolve(res.data.list);
        }, 200);
        return;
      }

      // 添加新订阅（POST /api/user/subscriptions/）
      if (url === '/user/subscriptions/' && method === 'POST') {
        setTimeout(() => {
          const res = mockApi.mockAddSubscription(data);
          res.code === 200 ? resolve(res.data) : reject(res.msg);
        }, 200);
        return;
      }

      // 删除单条订阅（DELETE /api/user/subscriptions/{id}/）
      if (url.match(/^\/api\/user\/subscriptions\/(.+)\/$/) && method === 'DELETE') {
        const id = url.match(/^\/api\/user\/subscriptions\/(.+)\/$/)[1]; // 提取 id
        console.log('Mock - 命中单条删除订阅，id：', id); // 加日志验证
        setTimeout(() => {
          const res = mockApi.mockDeleteSubscription(id);
          resolve(res.data);
        }, 200);
        return;
      }

      // 删除所有订阅（DELETE /api/user/subscriptions/）
      if (url === '/user/subscriptions/' && method === 'DELETE') {
        setTimeout(() => {
          const res = mockApi.mockDeleteAllSubscriptions();
          res.code === 200 ? resolve(res.data) : reject(res.msg);
        }, 200);
        return;
      }

      // 删除所有历史记录（DELETE /user/history/all/）
      if (url === '/user/history/all/' && method === 'DELETE') {
        setTimeout(() => {
          const res = mockApi.mockDeleteAllHistory();
          res.code === 200 ? resolve(res.data) : reject(res.msg);
        }, 200);
        return;
      }

      // 删除所有收藏（DELETE /user/favorites/all/）
      if (url === '/user/favorites/all/' && method === 'DELETE') {
        setTimeout(() => {
          const res = mockApi.mockDeleteAllFavourite();
          res.code === 200 ? resolve(res.data) : reject(res.msg);
        }, 200);
        return;
      }
      //  新增收藏（POST /user/favorites/）
      if (url === '/user/favorites/' && method === 'POST') {
        setTimeout(() => {
          const res = mockApi.mockAddFavourite(data);
          console.log('Mock - 新增收藏返回：', res);
          res.code === 200 ? resolve(res.data) : reject(res.msg);
        }, 200);
        return;
      }

      // 取消收藏（DELETE /user/favorites/{id}/）
      if (url.match(/^\/user\/favorites\/(.+)\/$/) && method === 'DELETE') {
        const favId = url.match(/^\/user\/favorites\/(.+)\/$/)[1]; // 提取收藏ID（支持下划线）
        setTimeout(() => {
          const res = mockApi.mockDeleteFavourite(favId);
          console.log('Mock - 取消收藏返回：', res);
          res.code === 200 ? resolve(res.data) : reject(res.msg);
        }, 200);
        return;
      }

      // 获取收藏列表（GET /user/favorites/）
      if (url === '/user/favorites/' && method === 'GET') {
        setTimeout(() => {
          const res = mockApi.mockGetFavouriteList();
          res.code === 200 ? resolve(res.data) : reject(res.msg);
        }, 200);
        return;
      }

      // 新增历史记录（POST /user/history/）
      if (url === '/user/history/' && method === 'POST') {
        setTimeout(() => {
          const res = mockApi.mockAddHistory(data);
          console.log('Mock - 新增历史返回：', res);
          res.code === 200 ? resolve(res.data) : reject(res.msg);
        }, 200);
        return;
      }

      // 删除历史记录（DELETE /user/history/{id}/）
      if (url.match(/^\/user\/history\/(\d+)\/$/) && method === 'DELETE') {
        const articleId = url.match(/^\/user\/history\/(\d+)\/$/)[1]; // 提取URL中的id
        setTimeout(() => {
          const res = mockApi.mockDeleteHistory(articleId);
          res.code === 200 ? resolve(res.data) : reject(res.msg);
        }, 200);
        return;
      }

      // 获取历史记录列表（GET /user/history/）
      if (url === '/user/history/' && method === 'GET') {
        setTimeout(() => {
          const res = mockApi.mockGetHistoryList();
          const historyList = res.data.list || []; // 兜底空数组，避免报错
          res.code === 200 ? resolve(historyList) : reject(res.msg);
        }, 200);
        return;
      }

      // 登录接口（POST /user/auth/login/）
      if (url === '/user/auth/login/' && method === 'POST') {
        setTimeout(() => {
          const res = mockApi.mockLogin(data);
          res.code === 200 ? resolve(res.data) : reject(res.msg);
        }, 200);
        return;
      }

      // 注册接口（POST /user/auth/register/）
      if (url === '/user/auth/register/' && method === 'POST') {
        setTimeout(() => {
          const res = mockApi.mockRegister(data);
          res.code === 201 ? resolve(res.data) : reject(res.msg);
        }, 200);
        return;
      }

      // 获取用户资料（GET /user/auth/profile/）
      if (url === '/user/auth/profile/' && method === 'GET') {
        setTimeout(() => resolve(mockApi.getMockUserInfo()), 200);
        return;
      }

      // 修改用户名（PATCH /user/update/username/）
      if (url === '/user/update/username/' && method === 'PATCH') {
        setTimeout(() => {
          const res = mockApi.mockUpdateUsername(data);
          res.code === 200 ? resolve(res.data) : reject(res.msg);
        }, 200);
        return;
      }

      // 修改邮箱（POST /user/update/email/）
      if (url === '/user/update/email/' && method === 'POST') {
        setTimeout(() => {
          const res = mockApi.mockUpdateEmail(data);
          res.code === 200 ? resolve(res.data) : reject(res.msg);
        }, 200);
        return;
      }

      // 修改手机号（POST /user/update/phone/）
      if (url === '/user/update/phone/' && method === 'POST') {
        setTimeout(() => {
          const res = mockApi.mockUpdatePhone(data);
          res.code === 200 ? resolve(res.data) : reject(res.msg);
        }, 200);
        return;
      }

      // 修改密码（POST /user/update/password/）
      if (url === '/user/update/password/' && method === 'POST') {
        setTimeout(() => {
          const res = mockApi.mockUpdatePassword(data);
          res.code === 200 ? resolve(res.data) : reject(res.msg);
        }, 200);
        return;
      }

      // 移动收藏（POST /user/favorites/{id}/move/）
      if (url.match(/^\/user\/favorites\/(.+)\/move\/$/) && method === 'POST') {
        const favoriteId = url.match(/^\/user\/favorites\/(.+)\/move\/$/)[1];
        const targetCollectionId = data.target_collection_id;
        setTimeout(() => {
          const res = mockApi.mockMoveFavourite(favoriteId, targetCollectionId);
          console.log('Mock - 移动收藏返回：', res);
          res.code === 200 ? resolve(res.data) : reject(res.msg);
        }, 200);
        return;
      }

      // 更新收藏夹（PUT /user/collections/{id}/）
      if (url.match(/^\/user\/collections\/(\d+)\/$/) && method === 'PUT') {
        const collectionId = url.match(/^\/user\/collections\/(\d+)\/$/)[1]; // 提取收藏夹ID
        setTimeout(() => {
          const res = mockApi.mockUpdateCollection(collectionId, data);
          console.log('Mock - 更新收藏夹返回：', res);
          res.code === 200 ? resolve(res.data) : reject(res.msg);
        }, 200);
        return;
      }

      // 获取收藏夹列表（GET /user/collections/）
      if (url === '/user/collections/' && method === 'GET') {
        setTimeout(() => {
          const res = mockApi.mockGetCollections();
          console.log('Mock - 收藏夹列表返回：', res);
          res.code === 200 ? resolve(res.data) : reject(res.msg);
        }, 200);
        return;
      }

      // 添加收藏夹（POST /user/collections/）
      if (url === '/user/collections/' && method === 'POST') {
        setTimeout(() => {
          const res = mockApi.mockAddCollection(data);
          console.log('Mock - 添加收藏夹返回：', res);
          res.code === 200 ? resolve(res.data) : reject(res.msg);
        }, 200);
        return;
      }


      // 删除收藏夹（DELETE /user/collections/{id}/）
      if (url.match(/^\/user\/collections\/(\d+)\/$/) && method === 'DELETE') {
        const collectionId = url.match(/^\/user\/collections\/(\d+)\/$/)[1]; // 提取收藏夹ID
        setTimeout(() => {
          const res = mockApi.mockDeleteCollection(collectionId);
          console.log('Mock - 删除收藏夹返回：', res);
          res.code === 200 ? resolve(res.data) : reject(res.msg);
        }, 200);
        return;
      }

      // 获取收藏夹文章（GET /user/collections/{id}/）
      if (url.match(/^\/user\/collections\/(\d+)\/$/) && method === 'GET') {
        const collectionId = url.match(/^\/user\/collections\/(\d+)\/$/)[1]; // 提取收藏夹ID
        console.log('Mock - 收藏夹文章请求，collectionId：', collectionId);
        setTimeout(() => {
          const res = mockApi.mockGetCollectionArticles(collectionId, data.start_rank || 0);
          console.log('Mock - 收藏夹文章返回：', res);
          res.code === 200 ? resolve(res.data) : reject(res.msg);
        }, 200);
        return;
      }

      if (url === '/webspider/public-accounts/search' && method === 'GET' && data.name) {
        setTimeout(() => {
          console.log('Mock - 命中公众号搜索请求，搜索内容：', data.name);
          const searchContent = data.name.trim();
          // 仅允许输入「111」，其他输入返回空列表
          if (searchContent === '111') {
            // 搜索111返回的结果（字段匹配 WXML 绑定）
            const searchResults = [{
                id: "tsinghua_111",
                accountid: 11,
                icon: "/assets/icons/add.svg",
                is_subscribed: 0,
                name: "清华111测试号", // 名称含111，匹配搜索
                fakeid: "MzA4OTIyMzgxMw==",
                is_default: false,
                last_crawl_time: "2025-11-20T21:26:51.028515+08:00",
                created_at: "2025-11-20T21:26:51.028515+08:00"
              },
              {
                id: "campus_111_service",
                accountid: 12,
                icon: "http://127.0.0.1:8000/media/account_avatars/campus.png",
                is_subscribed: 0,
                name: "111校园服务号", // 名称含111，匹配搜索
                fakeid: "MzIxOTg0MTg2NQ==",
                is_default: false,
                last_crawl_time: "2025-11-20T21:26:54.028515+08:00",
                created_at: "2025-11-20T21:26:54.028515+08:00"
              },
              {
                id: "guangdong_111_hqzx",
                accountid: 13,
                icon: "http://127.0.0.1:8000/media/account_avatars/%E5%B9%BF%E4%B8%9C%E5%8D%8E%E4%BE%A8%E4%B8%AD%E5%AD%A6.png",
                is_subscribed: 0,
                name: "广东华侨111中学", // 名称含111，匹配搜索
                fakeid: "MzAxMDEwNzg1NQ==",
                is_default: false,
                last_crawl_time: "2025-11-20T21:26:57.028515+08:00",
                created_at: "2025-11-20T21:26:57.028515+08:00"
              }
            ];
            // 匹配组件接收格式：{ public_accounts: 公众号数组 }
            resolve({
              public_accounts: searchResults
            });
          } else {
            // 非111输入返回空列表，无报错
            resolve({
              public_accounts: []
            });
            wx.showToast({
              title: '仅支持搜索「111」',
              icon: 'none'
            });
          }
        }, 200);
        return;
      }

      // 修改头像（PATCH /user/update/avatar/）
      if (url === '/user/update/avatar/' && method === 'PATCH') {
        setTimeout(() => {
          const res = mockApi.mockUpdateAvatar(data);
          res.code === 200 ? resolve(res.data) : reject(res.msg);
        }, 200);
        return;
      }

      // AI对话接口（POST /ai/ask/）
      if (url === '/ai/ask/' && method === 'POST') {
        setTimeout(() => {
          const question = data.question || '';

          // Mock测试样例数据
          let response = {
            question: question,
            answer: '',
            'references-articles': []
          };

          // 测试样例1: 自我介绍类问题
          if (question.includes('你是谁') || question.includes('介绍') || question.includes('介绍自己')) {
            response.answer = '我是面向校园生活领域的信息整合和总结专家，专门为师生提供清华大学软件学院相关的信息服务，例如心理咨询、学生组织动态等。我的回答基于提供的知识库内容，确保信息准确可靠。如需帮助，请随时告诉我你想了解的具体内容！ 😊';
            response['references-articles'] = [{
                id: 11,
                title: '软见心语丨心理咨询预约渠道全面升级！',
                article_url: 'http://mp.weixin.qq.com/s?__biz=MjM5NDMyNzcwNQ==&mid=2649873817&idx=2&sn=618ae575925e4084e49da77b4e373354#rd'
              },
              {
                id: 10,
                title: '清华大学软件学院第二十三届学生科协主席候选人公示',
                article_url: 'http://mp.weixin.qq.com/s?__biz=MjM5NDMyNzcwNQ==&mid=2649873817&idx=1&sn=69df39451056736f3ac38a7b30c81326#rd'
              }
            ];
          }
          // 测试样例2: 心理咨询相关问题
          else if (question.includes('心理') || question.includes('咨询') || question.includes('预约')) {
            response.answer = '清华大学软件学院提供心理咨询服务，预约渠道已全面升级。你可以通过以下方式预约心理咨询：1. 线上预约系统；2. 电话预约；3. 现场预约。如需了解更多详情，请查看相关文章。';
            response['references-articles'] = [{
              id: 11,
              title: '软见心语丨心理咨询预约渠道全面升级！',
              article_url: 'http://mp.weixin.qq.com/s?__biz=MjM5NDMyNzcwNQ==&mid=2649873817&idx=2&sn=618ae575925e4084e49da77b4e373354#rd'
            }];
          }
          // 测试样例3: 学生组织相关问题
          else if (question.includes('学生会') || question.includes('科协') || question.includes('学生组织') || question.includes('主席')) {
            response.answer = '清华大学软件学院有多个学生组织，包括学生会和学生科协。近期有学生会主席团和科协主席的候选人公示，你可以查看相关文章了解详细信息。';
            response['references-articles'] = [{
                id: 10,
                title: '清华大学软件学院第二十三届学生科协主席候选人公示',
                article_url: 'http://mp.weixin.qq.com/s?__biz=MjM5NDMyNzcwNQ==&mid=2649873817&idx=1&sn=69df39451056736f3ac38a7b30c81326#rd'
              },
              {
                id: 2,
                title: '清华大学软件学院第二十四次学代会简报',
                article_url: 'http://mp.weixin.qq.com/s?__biz=MjM5NDMyNzcwNQ==&mid=2649873886&idx=1&sn=774de9b0e96fb62cde45411b1dcabf34#rd'
              },
              {
                id: 5,
                title: '清华大学软件学院第二十四届学生会主席团候选人简介——叶思萌',
                article_url: 'http://mp.weixin.qq.com/s?__biz=MjM5NDMyNzcwNQ==&mid=2649873860&idx=3&sn=fead22634dea6e508e9e3b4dba562c6b#rd'
              },
              {
                id: 8,
                title: '清华大学软件学院第二十三届学生科协主席候选人简介——李天笑',
                article_url: 'http://mp.weixin.qq.com/s?__biz=MjM5NDMyNzcwNQ==&mid=2649873860&idx=6&sn=4d0accd838bb27f1d8bfe35ae51b23ff#rd'
              }
            ];
          }
          // 测试样例4: 学代会相关问题
          else if (question.includes('学代会') || question.includes('代表大会')) {
            response.answer = '清华大学软件学院第二十四次学生代表大会已成功召开。学代会是学生参与学院民主管理的重要平台，你可以查看相关简报了解会议内容和决议。';
            response['references-articles'] = [{
              id: 2,
              title: '清华大学软件学院第二十四次学代会简报',
              article_url: 'http://mp.weixin.qq.com/s?__biz=MjM5NDMyNzcwNQ==&mid=2649873886&idx=1&sn=774de9b0e96fb62cde45411b1dcabf34#rd'
            }];
          }
          // 测试样例5: 问候类问题（无参考文章）
          else if (question.includes('你好') || question.includes('hello') || question.includes('hi')) {
            response.answer = '你好！我是面向校园生活领域的信息整合和总结专家，专门为师生提供清华大学软件学院相关的信息服务。有什么可以帮助你的吗？';
            response['references-articles'] = [];
          }
          // 测试样例6: 帮助类问题（无参考文章）
          else if (question.includes('帮助') || question.includes('help') || question.includes('功能')) {
            response.answer = '我可以帮助你解答关于清华大学软件学院的各种问题，包括心理咨询、学生组织动态、校园活动等信息。你可以直接问我任何相关问题，我会基于知识库为你提供准确的答案和相关文章链接。';
            response['references-articles'] = [];
          }
          // 测试样例7: 默认回复（带参考文章）
          else {
            response.answer = `我理解你的问题是："${question}"。作为面向校园生活领域的信息整合专家，我基于知识库为你提供相关信息。以下是一些可能相关的文章，你可以查看获取更多详情。`;
            response['references-articles'] = [{
                id: 11,
                title: '软见心语丨心理咨询预约渠道全面升级！',
                article_url: 'http://mp.weixin.qq.com/s?__biz=MjM5NDMyNzcwNQ==&mid=2649873817&idx=2&sn=618ae575925e4084e49da77b4e373354#rd'
              },
              {
                id: 10,
                title: '清华大学软件学院第二十三届学生科协主席候选人公示',
                article_url: 'http://mp.weixin.qq.com/s?__biz=MjM5NDMyNzcwNQ==&mid=2649873817&idx=1&sn=69df39451056736f3ac38a7b30c81326#rd'
              }
            ];
          }

          console.log('Mock - AI对话返回：', response);
          resolve(response);
        }, 500);
        return;
      }
    }

    // 后端接口逻辑（MOCK_ENABLE=false 时生效）
    const doRequest = (isRetry = false) => new Promise((resolveRequest, rejectRequest) => {
      wx.request({
        url: `${baseUrl}${url}`,
        method,
        data,
        header: {
          'Content-Type': 'application/json',
          ...(needAuthHeader && access_token ? {
            'Authorization': `Bearer ${access_token}`
          } : {})
        },

        success: (res) => {
          console.log('实际请求响应:', res);
          if (res.statusCode >= 200 && res.statusCode < 300) {
            resolveRequest(res.data);
            return;
          }

          if (res.statusCode === 401 && needAuthHeader && refresh_token && !isRetry) {
            refreshAccessToken()
              .then(() => doRequest(true).then(resolveRequest).catch(rejectRequest))
              .catch((err) => rejectRequest(err || '登录已过期，请重新登录'));
            return;
          }

          let errorMsg = '请求失败';
          if (res.data) {
            // 尝试多种可能的错误信息字段
            errorMsg = res.data.error ||
              res.data.detail ||
              res.data.message ||
              (typeof res.data === 'string' ? res.data : JSON.stringify(res.data));
          }

          rejectRequest({
            statusCode: res.statusCode,
            data: res.data,
            error: errorMsg,
            message: errorMsg
          });
        },
        fail: (err) => {
          // reject 一个结构化的错误对象
          rejectRequest({
            statusCode: 0, // 网络错误没有状态码
            data: null,
            error: err.errMsg || '网络失败',
            message: err.errMsg || '网络失败',
            errMsg: err.errMsg
          });
        }
      });
    });

    doRequest().then(resolve).catch(reject);
  });
};

// 接口方法
// 收藏夹
const getCollections = () => request('/user/collections/', 'GET');
const addCollection = (data) => request('/user/collections/', 'POST', data);
const getCollectionArticles = (collectionId, startRank = 0) => {
  return request(`/user/collections/${collectionId}/`, 'GET');
};
const updateCollection = (collectionId, data) => {
  return request(`/user/collections/${collectionId}/`, 'PUT', data);
};
const deleteCollection = (collectionId) => request(`/user/collections/${collectionId}/`, 'DELETE');
const moveFavourite = (favoriteId, targetCollectionId) => {
  return request(`/user/favorites/${favoriteId}/move/`, 'POST', {
    collection_id: targetCollectionId
  });
};
// 待办（Todo）
const getTodos = (date) => {
  // 正确定义params：有date则传date参数，无则传空对象
  let params = {};
  if (date) {
    params.date = date;
  }
  // GET请求，参数作为query传递
  return request('/user/todos/', 'GET', params);
};
const addTodo = (data) => request('/user/todos/', 'POST', data);
const updateTodo = (todoId, data) => request(`/user/todos/${todoId}/`, 'PATCH', data);
const deleteTodo = (todoId) => request(`/user/todos/${todoId}/`, 'DELETE');
const getArticleDetail = (articleId) => request(`/webspider/articles/${articleId}/`, 'GET');
// 收藏
const addFavourite = (data) => request('/user/favorites/', 'POST', data);
const deleteFavourite = (articleId) => request(`/user/favorites/${articleId}/`, 'DELETE');
const getFavouriteList = () => request('/user/favorites/', 'GET');
const deleteAllFavourite = () => request('/user/favorites/', 'DELETE');
//历史
const addHistory = (data) => request('/user/history/', 'POST', data);
const deleteHistory = (articleId) => request(`/user/history/${articleId}/`, 'DELETE');
const getHistoryList = (startRank = 0) => request('/user/history/', 'GET', {
  start_rank: startRank
});
const deleteAllHistory = () => request('/user/history/', 'DELETE');
//登陆与注册
const login = (data) => {
  return request('/user/auth/login/', 'POST', data).then(res => {
    // 登录成功后，存储refresh和access
    if (res.refresh) {
      wx.setStorageSync('refresh_token', res.refresh);
      refresh_token = res.refresh; // 更新全局变量
      console.log('登录成功，令牌已存储:', res.refresh);
    }
    if (res.access) {
      wx.setStorageSync('access_token', res.access);
      access_token = res.access; // 更新全局变量
      console.log('登录成功，令牌已存储:', res.access);
    }
    return res;
  });
}
// 找到 request 模块中的 register 函数，替换为以下代码
const register = (data) => {
  return new Promise((resolve, reject) => {
    wx.request({
      url: `${baseUrl}/user/auth/register/`, // 拼接后完整URL：http://49.232.208.99/api/user/auth/register/
      method: 'POST',
      data: data,
      header: {
        'Content-Type': 'application/json' // 仅保留 Content-Type，移除 Authorization
      },
      success: (res) => {
        console.log('注册接口响应：', res); // 打印详细响应
        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve(res.data);
        } else {
          // 打印后端返回的具体错误信息（关键！）
          const errorDetail = res.data?.detail || res.data?.message || JSON.stringify(res.data);
          console.error('注册失败详情：', errorDetail);
          reject(`注册失败：${errorDetail}`);
        }
      },
      fail: (err) => {
        console.error('注册网络失败：', err);
        reject('网络错误，无法连接服务器');
      }
    });
  });
};
//用户资料
const getProfile = () => request('/user/auth/profile/', 'GET');
const updateUsername = (data) => request('/user/update/username/', 'PATCH', data);
const updateEmail = (data) => request('/user/update/email/', 'POST', data);
const updatePhone = (data) => request('/user/update/phone/', 'POST', data);
const updatePassword = (data) => request('/user/update/password/', 'POST', data);
const updateAvatar = (filePath) => {
  return request('/user/update/avatar/', 'PATCH', {
    __isFileUpload: true, // 标识为文件上传
    filePath: filePath,
    fieldName: 'avatar' // 动态指定字段名
  });
};
//订阅
const getSubscriptionList = () => request('/user/subscriptions/', 'GET');
const getFilteredSubscriptionList = (name) => request('/user/subscriptions/search/', 'GET', {
  name: name
});
const addSubscription = (data) => request('/user/subscriptions/', 'POST', data);
const deleteSubscription = (id) => request(`/user/subscriptions/${id}/`, 'DELETE');
const deleteAllSubscriptions = () => request('/user/subscriptions/', 'DELETE');
const sortSubscriptions = (data) => request('/user/subscriptions/sort/', 'POST', data);
const searchSubscriptions = (name) => request('/user/subscriptions/search/', 'GET', {
  name: name
});
//公众号
const getCampusAccountList = () => request('/webspider/public-accounts/campus', 'GET');
const getAccountsByName = (name) => request('/webspider/public-accounts/search', 'GET', {
  name: name
});
const getMoreAccountsByName = (name) => request('/webspider/new-accounts/search', 'GET', {
  name: name
});
//文章推送
const getArticlesByAccount = (data) => request('/articles/by-account/', 'GET', data);
const getCampusLatestArticles = (startRank = 0) => request('/articles/campus-latest/', 'GET', {
  start_rank: startRank
});
const getCustomizedLatestArticles = (startRank = 0) => request('/articles/customized-latest/', 'GET', {
  start_rank: startRank
});
const getFilteredCustomizedLatestArticles = (startRank = 0, search_content = "") => request('/articles/customized-latest/search', 'GET', {
  start_rank: startRank,
  search_content: search_content
});
const getLatestArticles = (data = {}) => request('/articles/latest/', 'GET', data);
const getRecommendedArticles = () => request('/articles/recommended', 'GET');
const getFilteredArticles = (data) => request('/articles/filter/', 'POST', data);

// AI对话（流式）
const chatWithAIStream = ({
  question,
  onMessage,
  onReferences,
  onDone,
  onError
} = {}) => {
  let buffer = '';
  let finished = false;

  const processLines = (text) => {
    buffer += text;
    const lines = buffer.split('\n');
    buffer = lines.pop() || '';

    lines.forEach((line) => {
      let payload = line;

      // 去掉 data: 前缀但不整体 trim，保留前后空白换行信息
      if (payload.startsWith('data:')) {
        payload = payload.slice(5);
        if (payload.startsWith(' ')) payload = payload.slice(1);
      }

      // 去除行尾的回车符
      if (payload.endsWith('\r')) payload = payload.slice(0, -1);

      const sentinel = payload.trim();
      if (!payload && !sentinel) return;

      // 兼容后端直接输出文本 + [[REFERENCES]] JSON 的格式
      if (payload.includes('[[REFERENCES]]')) {
        const parts = payload.split('[[REFERENCES]]');
        const textPart = (parts[0] || '');
        const refsRaw = (parts[1] || '').trim();
        if (textPart && onMessage) {
          onMessage(textPart);
        }
        if (refsRaw) {
          try {
            const refs = JSON.parse(refsRaw);
            if (onReferences) {
              onReferences(refs);
            }
          } catch (err) {
            console.warn('refs parse failed', err, refsRaw);
          }
        }
        return;
      }

      if (sentinel === '[DONE]' || sentinel === '[done]') {
        finish();
        return;
      }

      try {
        const json = JSON.parse(payload);
        const delta = json.delta || json.answer || json.content || json.reply || '';
        if (delta && onMessage) {
          onMessage(delta);
        }
        const refs = json['references-articles'] || json.referencesArticles || json.references_articles || json.references;
        if (refs && onReferences) {
          onReferences(refs);
        }
        if (json.done === true) {
          finish();
        }
      } catch (e) {
        if (onMessage) {
          onMessage(payload);
        }
      }
    });
  };

  const finish = () => {
    if (finished) return;
    // 处理残留缓存，避免最后一段 refs 丢失
    if (buffer) {
      processLines('\n');
    }
    finished = true;
    if (onDone) onDone();
  };

  const requestTask = wx.request({
    url: `${baseUrl}/ask/stream/`,
    method: 'POST',
    data: {
      question
    },
    enableChunked: true,
    responseType: 'arraybuffer',
    header: {
      'Content-Type': 'application/json',
      // 406 兼容：让后端返回任意可用类型（流式 text/event-stream 或常规 JSON）
      'Accept': 'text/event-stream,application/json;q=0.9,*/*;q=0.8',
      'Authorization': access_token ? `Bearer ${access_token}` : ''
    },
    success: (res) => {
      if (res.statusCode >= 200 && res.statusCode < 300) {
        finish();
      } else {
        if (onError) onError({ statusCode: res.statusCode, message: res.data || '请求失败' });
        finish();
      }
    },
    fail: (err) => {
      if (onError) onError({ statusCode: 0, message: err.errMsg || '网络失败' });
      finish();
    }
  });

  if (requestTask && requestTask.onChunkReceived) {
    requestTask.onChunkReceived((res) => {
      const text = decodeBuffer(res.data);
      processLines(text);
    });
  } else if (onError) {
    onError('当前客户端不支持流式传输，请升级微信或使用非流式模式');
  }

  return requestTask;
};

// AI对话（非流式兜底）
const chatWithAI = (data) => request('/ask/', 'POST', data);

const logout = () => clearTokens();
const getStoredTokens = () => ({
  access: access_token,
  refresh: refresh_token
});

// 所有方法
module.exports = {
  resourceUrl,
  login,
  register,
  getProfile,
  updateUsername,
  updateEmail,
  updatePhone,
  updatePassword,
  updateAvatar,
  addFavourite,
  deleteFavourite,
  getFavouriteList,
  addHistory,
  deleteHistory,
  getHistoryList,
  deleteAllHistory,
  deleteAllFavourite,
  getSubscriptionList,
  getFilteredSubscriptionList,
  addSubscription,
  deleteSubscription,
  deleteAllSubscriptions,
  sortSubscriptions,
  searchSubscriptions,
  getArticlesByAccount,
  getCampusLatestArticles,
  getCustomizedLatestArticles,
  getFilteredCustomizedLatestArticles,
  getLatestArticles,
  getRecommendedArticles,
  getCampusAccountList,
  getAccountsByName,
  getMoreAccountsByName,
  getFilteredArticles,
  getCollections,
  addCollection,
  getCollectionArticles,
  updateCollection,
  deleteCollection,
  moveFavourite,
  getTodos,
  addTodo,
  updateTodo,
  deleteTodo,
  getArticleDetail,
  chatWithAI,
  chatWithAIStream,
  trySilentRefresh,
  refreshToken: refreshAccessToken,
  logout,
  getStoredTokens
};