const baseUrl = 'https://403app.xyz/api';
export const resourceUrl = "https://403app.xyz/";

let access_token = wx.getStorageSync('access_token') || '';
let refresh_token = wx.getStorageSync('refresh_token') || '';
const MOCK_ENABLE = false; // 核心：关闭Mock，启用真实后端请求
const mockApi = require('./mockConfig.js'); // 保留（若需临时开启Mock）

const request = (url, method = 'GET', data = {}, isFileUpload = false) => {
  return new Promise((resolve, reject) => {
    // 检查是否是文件上传请求（通过特殊字段标识）
    if (!MOCK_ENABLE && data.__isFileUpload) {
       // 确保 data 是对象类型
       const uploadData = typeof data === 'string' ? { filePath: data } : data;
      
       // 提取必要的参数
       const filePath = uploadData.filePath;
       const fieldName = uploadData.fieldName || 'file';
       const formData = uploadData.formData || {};
      
       // 验证 filePath 是否为字符串
       if (typeof filePath !== 'string') {
         reject('filePath 必须是字符串类型');
         return;
       }
      wx.uploadFile({
        url: `${baseUrl}${url}`,
        filePath: filePath,
        name: fieldName, // 动态字段名
        header: {
          'Authorization': access_token ? `Bearer ${access_token}` : ''
        },
        formData: formData,
        success: (res) => {
          if (res.statusCode >= 200 && res.statusCode < 300) {
            try {
              resolve(JSON.parse(res.data));
            } catch (e) {
              resolve(res.data);
            }
          } else {
            reject(res.data || '上传失败');
          }
        },
        fail: (err) => reject(err.errMsg || '网络失败')
      });
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
            resolve({ list: articles, total: articles.length });
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
          const searchResults = [
            {
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
        resolve({ public_accounts: searchResults });
      } else {
        // 非111输入返回空列表，无报错
        resolve({ public_accounts: [] });
        wx.showToast({ title: '仅支持搜索「111」', icon: 'none' });
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

      // 待办相关 Mock
    // 1. 获取全量待办（无date参数）
    if (url === '/user/todos/' && method === 'GET' && !data.date) {
    setTimeout(() => {
        const res = mockApi.mockGetTodos();
        console.log('Mock - 获取全量待办返回：', res);
        res.code === 200 ? resolve(res.data) : reject(res.msg);
    }, 200);
    return;
    }

    // 3. 添加待办（原有逻辑保留）
    if (url === '/user/todos/' && method === 'POST') {
    setTimeout(() => {
        const res = mockApi.mockAddTodo(data);
        console.log('Mock - 添加待办返回：', res);
        res.code === 200 ? resolve(res.data) : reject(res.msg);
    }, 200);
    return;
    }

    // 4. 修改待办（修正为 PATCH 方法，匹配前端调用）
    if (url.match(/^\/user\/todos\/(\d+)\/$/) && method === 'PATCH') {
    const todoId = url.match(/^\/user\/todos\/(\d+)\/$/)[1];
    setTimeout(() => {
        const res = mockApi.mockUpdateTodo(todoId, data);
        console.log('Mock - 修改待办返回：', res);
        res.code === 200 ? resolve(res.data) : reject(res.msg);
    }, 200);
    return;
    }

    // 5. 删除待办（原有逻辑保留）
    if (url.match(/^\/user\/todos\/(\d+)\/$/) && method === 'DELETE') {
    const todoId = url.match(/^\/user\/todos\/(\d+)\/$/)[1];
    setTimeout(() => {
        const res = mockApi.mockDeleteTodo(todoId);
        console.log('Mock - 删除待办返回：', res);
        res.code === 200 ? resolve(res.data) : reject(res.msg);
    }, 200);
    return;
    }
   }

    // 后端接口逻辑（MOCK_ENABLE=false 时生效）
    wx.request({
      url: `${baseUrl}${url}`,
      method,
      data,
      header: {
        'Content-Type': 'application/json',
        'Authorization': access_token ? `Bearer ${access_token}` : ''
      },
      
      success: (res) => {
        console.log('实际请求响应:', res); // 添加调试日志
        // 根据HTTP状态码判断，2xx状态码都认为是成功
        if (res.statusCode >= 200 && res.statusCode < 300) {
            resolve(res.data); // 直接返回后端数据
        } 
        // 错误处理
        else {
            const errorMsg = res.data?.message || res.data?.detail || `请求失败`;
            reject(errorMsg);
        }
      },
      fail: (err) => reject(err.errMsg || '网络失败')
    });
  });
};

// 接口方法
// 收藏夹
const getCollections = () => request('/user/collections/', 'GET');
const addCollection = (data) => request('/user/collections/', 'POST', data);
const getCollectionArticles = (collectionId, startRank = 0) => {
    return request(`/user/collections/${collectionId}/`, 'GET');};
const updateCollection = (collectionId, data) => {
    return request(`/user/collections/${collectionId}/`, 'PUT', data);};
const deleteCollection = (collectionId) => request(`/user/collections/${collectionId}/`, 'DELETE');
const moveFavourite = (favoriteId, targetCollectionId) => {return request(`/user/favorites/${favoriteId}/move/`, 'POST', {collection_id: targetCollectionId});};
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
const getArticleDetail = ( articleId ) =>  request(`/webspider/articles/${articleId}/`, 'GET');
// 收藏
const addFavourite = (data) => request('/user/favorites/', 'POST', data);
const deleteFavourite = (articleId) => request(`/user/favorites/${articleId}/`, 'DELETE');
const getFavouriteList = () => request('/user/favorites/', 'GET');
const deleteAllFavourite = () => request('/user/favorites/', 'DELETE');
//历史
const addHistory = (data) => request('/user/history/', 'POST', data);
const deleteHistory = (articleId) => request(`/user/history/${articleId}/`, 'DELETE');
const getHistoryList = () => request('/user/history/', 'GET');
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
const getFilteredSubscriptionList = (name) => request('/user/subscriptions/search/', 'GET', {name: name});
const addSubscription = (data) => request('/user/subscriptions/', 'POST', data);
const deleteSubscription = (id) => request(`/user/subscriptions/${id}/`, 'DELETE');
const deleteAllSubscriptions = () => request('/user/subscriptions/', 'DELETE');
const sortSubscriptions = (data) => request('/user/subscriptions/sort/', 'POST', data);
const searchSubscriptions = (name) => request('/user/subscriptions/search/', 'GET', {name: name});
//公众号
const getCampusAccountList = () => request('/webspider/public-accounts/campus', 'GET');
const getAccountsByName = (name) => request('/webspider/public-accounts/search', 'GET', {name: name});
const getMoreAccountsByName = (name) => request('/webspider/new-accounts/search', 'GET', {name: name});
//文章推送
const getArticlesByAccount = (data) => request('/articles/by-account/', 'GET', data);
const getCampusLatestArticles = (startRank = 0) => request('/articles/campus-latest/', 'GET', {start_rank: startRank});
const getCustomizedLatestArticles = (startRank = 0) => request('/articles/customized-latest/', 'GET', {start_rank: startRank});
const getFilteredCustomizedLatestArticles = (startRank = 0, search_content = "") => request('/articles/customized-latest/search', 'GET', {start_rank: startRank, search_content: search_content});
const getLatestArticles = (data = {}) => request('/articles/latest/', 'GET', data);
const getRecommendedArticles = () => request('/articles/recommended', 'GET');
const getFilteredArticles = (data) => request('/articles/filter/', 'POST', data);

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
  getArticleDetail 
};