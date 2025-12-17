const Mock = require('./mock.js');

// 新增：统一文章数据源管理（方便收藏时同步状态）
const allArticleSources = {
  mockLatestArticles: [],
  mockRecommendedArticles: [],
  mockCustomizedLatestArticles: [],
  mockCampusLatestArticles: [],
  mockArticles: []
};

// 模拟用户数据库（存储注册用户，用于登录校验）
let mockUsers = [
  { id: 1, username: "test", password: "123456" },
  { id: 2, username: "1", password: "1" }
];

// 首页推荐文章（轮播图）- 统一ID+完善is_favorited
let mockRecommendedArticles = [
  {
    id: 1001, // 改为数字ID，避免字符串ID问题
    title: "2025年AI技术发展白皮书发布",
    image: "/assets/icons/add.svg",
    article_url: "https://example.com/article/ai-development-2025",
    summary: "权威机构发布AI技术发展报告，揭秘大模型落地应用新趋势...",
    is_favorited: 0, // 初始未收藏（0=未收藏，收藏后为数字ID）
    account_name: "科技前沿",
    publish_time: "2025-11-18",
    tags: "科技",
    avatar: "/assets/icons/default-avatar.png"
  },
  {
    id: 1002,
    title: "全国大学生创新创业大赛启动",
    image: "https://www.vcg.com/creative/1424031120.html",
    article_url: "https://example.com/article/innovation-competition-2025",
    summary: "覆盖科技、文创、环保等多个赛道，最高可获50万创业基金",
    is_favorited: 0,
    account_name: "创新创业平台",
    publish_time: "2025-11-17",
    tags: "创业",
    avatar: "/assets/icons/default-avatar.png"
  },
  {
    id: 1003,
    title: "校园数字化升级：智慧校园2.0上线",
    image: "/assets/images/banner3.jpg",
    article_url: "https://example.com/article/smart-campus-2.0",
    summary: "选课、考勤、消费全流程数字化，师生可享一站式服务",
    is_favorited: 0,
    account_name: "校园服务中心",
    publish_time: "2025-11-16",
    tags: "校园",
    avatar: "/assets/icons/default-avatar.png"
  }
];

// 首页最新文章（卡片）- 确保is_favorited字段存在
let mockLatestArticles = [
  {
    id: 1,
    title: "多次加印，清华这本教材“接地气”！",
    account_name: "清华大学",
    article_url: "https://mp.weixin.qq.com/s?__biz=MzA4OTIyMzgxMw==&mid=2659376767&idx=1&sn=3f1f161a9082841d31df49d6c6f95c4d&chksm=8a5cf4ecd3327cf83914bbc5d7161303d89d352b4e0f558a983d067732090b307a1339fd15c6#rd",
    publish_time: "2025-11-17 09:02:39",
    cover: "http://127.0.0.1:8000/media/media/article_covers/%E5%A4%9A%E6%AC%A1%E5%8A%A0%E5%8D%B0%EF%BC%8C%E6%B8%85%E5%8D%8E%E8%BF%99%E6%9C%AC%E6%95%99%E6%9D%90%E2%80%9C%E6%8E%A5%E5%9C%B0%E6%B0%94%E2%80%9D%EF%BC%81.jpeg",
    summary: "清华大学法学院教授王亚新、陈杭平与中国政法大学刘君博教授合作编写的《中国民事诉讼法重点讲义》是一本创新教材...",
    tags: ["其他内容"],
    key_info: "民事诉讼法,教材,清华大学,法学教育,案例教学",
    is_favorited: 0,
    avatar: "http://127.0.0.1:8000/media/account_avatars/tsinghua.png"
  },
  {
    id: 2,
    title: "多次加印，清华这本教材“接地气”！",
    account_name: "清华大学",
    article_url: "https://mp.weixin.qq.com/s?__biz=MzA4OTIyMzgxMw==&mid=2659376767&idx=1&sn=3f1f161a9082841d31df49d6c6f95c4d&chksm=8a5cf4ecd3327cf83914bbc5d7161303d89d352b4e0f558a983d067732090b307a1339fd15c6#rd",
    publish_time: "2025-11-17 09:02:39",
    cover: "http://127.0.0.1:8000/media/media/article_covers/%E5%A4%9A%E6%AC%A1%E5%8A%A0%E5%8D%B0%EF%BC%8C%E6%B8%85%E5%8D%8E%E8%BF%99%E6%9C%AC%E6%95%99%E6%9D%90%E2%80%9C%E6%8E%A5%E5%9C%B0%E6%B0%94%E2%80%9D%EF%BC%81.jpeg",
    summary: "清华大学法学院教授王亚新、陈杭平与中国政法大学刘君博教授合作编写的《中国民事诉讼法重点讲义》是一本创新教材...",
    tags: ["其他内容"],
    key_info: "民事诉讼法,教材,清华大学,法学教育,案例教学",
    is_favorited: 0,
    avatar: "http://127.0.0.1:8000/media/account_avatars/tsinghua.png"
  },
  {
    id: 13,
    title: "多次加印，清华这本教材“接地气”！",
    account_name: "清华大学",
    article_url: "https://mp.weixin.qq.com/s?__biz=MzA4OTIyMzgxMw==&mid=2659376767&idx=1&sn=3f1f161a9082841d31df49d6c6f95c4d&chksm=8a5cf4ecd3327cf83914bbc5d7161303d89d352b4e0f558a983d067732090b307a1339fd15c6#rd",
    publish_time: "2025-11-17 09:02:39",
    cover: "http://127.0.0.1:8000/media/media/article_covers/%E5%A4%9A%E6%AC%A1%E5%8A%A0%E5%8D%B0%EF%BC%8C%E6%B8%85%E5%8D%8E%E8%BF%99%E6%9C%AC%E6%95%99%E6%9D%90%E2%80%9C%E6%8E%A5%E5%9C%B0%E6%B0%94%E2%80%9D%EF%BC%81.jpeg",
    summary: "清华大学法学院教授王亚新、陈杭平与中国政法大学刘君博教授合作编写的《中国民事诉讼法重点讲义》是一本创新教材...",
    tags: ["其他内容"],
    key_info: "民事诉讼法,教材,清华大学,法学教育,案例教学",
    is_favorited: 0,
    avatar: "http://127.0.0.1:8000/media/account_avatars/tsinghua.png"
  },
  {
    id: 14,
    title: "多次加印，清华这本教材“接地气”！",
    account_name: "清华大学",
    article_url: "https://mp.weixin.qq.com/s?__biz=MzA4OTIyMzgxMw==&mid=2659376767&idx=1&sn=3f1f161a9082841d31df49d6c6f95c4d&chksm=8a5cf4ecd3327cf83914bbc5d7161303d89d352b4e0f558a983d067732090b307a1339fd15c6#rd",
    publish_time: "2025-11-17 09:02:39",
    cover: "http://127.0.0.1:8000/media/media/article_covers/%E5%A4%9A%E6%AC%A1%E5%8A%A0%E5%8D%B0%EF%BC%8C%E6%B8%85%E5%8D%8E%E8%BF%99%E6%9C%AC%E6%95%99%E6%9D%90%E2%80%9C%E6%8E%A5%E5%9C%B0%E6%B0%94%E2%80%9D%EF%BC%81.jpeg",
    summary: "清华大学法学院教授王亚新、陈杭平与中国政法大学刘君博教授合作编写的《中国民事诉讼法重点讲义》是一本创新教材...",
    tags: ["其他内容"],
    key_info: "民事诉讼法,教材,清华大学,法学教育,案例教学",
    is_favorited: 0,
    avatar: "http://127.0.0.1:8000/media/account_avatars/tsinghua.png"
  },
  {
    id: 15,
    title: "多次加印，清华这本教材“接地气”！",
    account_name: "清华大学",
    article_url: "https://mp.weixin.qq.com/s?__biz=MzA4OTIyMzgxMw==&mid=2659376767&idx=1&sn=3f1f161a9082841d31df49d6c6f95c4d&chksm=8a5cf4ecd3327cf83914bbc5d7161303d89d352b4e0f558a983d067732090b307a1339fd15c6#rd",
    publish_time: "2025-11-17 09:02:39",
    cover: "http://127.0.0.1:8000/media/media/article_covers/%E5%A4%9A%E6%AC%A1%E5%8A%A0%E5%8D%B0%EF%BC%8C%E6%B8%85%E5%8D%8E%E8%BF%99%E6%9C%AC%E6%95%99%E6%9D%90%E2%80%9C%E6%8E%A5%E5%9C%B0%E6%B0%94%E2%80%9D%EF%BC%81.jpeg",
    summary: "清华大学法学院教授王亚新、陈杭平与中国政法大学刘君博教授合作编写的《中国民事诉讼法重点讲义》是一本创新教材...",
    tags: ["其他内容"],
    key_info: "民事诉讼法,教材,清华大学,法学教育,案例教学",
    is_favorited: 0,
    avatar: "http://127.0.0.1:8000/media/account_avatars/tsinghua.png"
  },
  {
    id: 16,
    title: "多次加印，清华这本教材“接地气”！",
    account_name: "清华大学",
    article_url: "https://mp.weixin.qq.com/s?__biz=MzA4OTIyMzgxMw==&mid=2659376767&idx=1&sn=3f1f161a9082841d31df49d6c6f95c4d&chksm=8a5cf4ecd3327cf83914bbc5d7161303d89d352b4e0f558a983d067732090b307a1339fd15c6#rd",
    publish_time: "2025-11-17 09:02:39",
    cover: "http://127.0.0.1:8000/media/media/article_covers/%E5%A4%9A%E6%AC%A1%E5%8A%A0%E5%8D%B0%EF%BC%8C%E6%B8%85%E5%8D%8E%E8%BF%99%E6%9C%AC%E6%95%99%E6%9D%90%E2%80%9C%E6%8E%A5%E5%9C%B0%E6%B0%94%E2%80%9D%EF%BC%81.jpeg",
    summary: "清华大学法学院教授王亚新、陈杭平与中国政法大学刘君博教授合作编写的《中国民事诉讼法重点讲义》是一本创新教材...",
    tags: ["其他内容"],
    key_info: "民事诉讼法,教材,清华大学,法学教育,案例教学",
    is_favorited: 0,
    avatar: "http://127.0.0.1:8000/media/account_avatars/tsinghua.png"
  },
  {
    id: 17,
    title: "多次加印，清华这本教材“接地气”！",
    account_name: "清华大学",
    article_url: "https://mp.weixin.qq.com/s?__biz=MzA4OTIyMzgxMw==&mid=2659376767&idx=1&sn=3f1f161a9082841d31df49d6c6f95c4d&chksm=8a5cf4ecd3327cf83914bbc5d7161303d89d352b4e0f558a983d067732090b307a1339fd15c6#rd",
    publish_time: "2025-11-17 09:02:39",
    cover: "http://127.0.0.1:8000/media/media/article_covers/%E5%A4%9A%E6%AC%A1%E5%8A%A0%E5%8D%B0%EF%BC%8C%E6%B8%85%E5%8D%8E%E8%BF%99%E6%9C%AC%E6%95%99%E6%9D%90%E2%80%9C%E6%8E%A5%E5%9C%B0%E6%B0%94%E2%80%9D%EF%BC%81.jpeg",
    summary: "清华大学法学院教授王亚新、陈杭平与中国政法大学刘君博教授合作编写的《中国民事诉讼法重点讲义》是一本创新教材...",
    tags: ["其他内容"],
    key_info: "民事诉讼法,教材,清华大学,法学教育,案例教学",
    is_favorited: 0,
    avatar: "http://127.0.0.1:8000/media/account_avatars/tsinghua.png"
  },
  {
    id: 18,
    title: "多次加印，清华这本教材“接地气”！",
    account_name: "清华大学",
    article_url: "https://mp.weixin.qq.com/s?__biz=MzA4OTIyMzgxMw==&mid=2659376767&idx=1&sn=3f1f161a9082841d31df49d6c6f95c4d&chksm=8a5cf4ecd3327cf83914bbc5d7161303d89d352b4e0f558a983d067732090b307a1339fd15c6#rd",
    publish_time: "2025-11-17 09:02:39",
    cover: "http://127.0.0.1:8000/media/media/article_covers/%E5%A4%9A%E6%AC%A1%E5%8A%A0%E5%8D%B0%EF%BC%8C%E6%B8%85%E5%8D%8E%E8%BF%99%E6%9C%AC%E6%95%99%E6%9D%90%E2%80%9C%E6%8E%A5%E5%9C%B0%E6%B0%94%E2%80%9D%EF%BC%81.jpeg",
    summary: "清华大学法学院教授王亚新、陈杭平与中国政法大学刘君博教授合作编写的《中国民事诉讼法重点讲义》是一本创新教材...",
    tags: ["其他内容"],
    key_info: "民事诉讼法,教材,清华大学,法学教育,案例教学",
    is_favorited: 0,
    avatar: "http://127.0.0.1:8000/media/account_avatars/tsinghua.png"
  },
  {
    id: 19,
    title: "多次加印，清华这本教材“接地气”！",
    account_name: "清华大学",
    article_url: "https://mp.weixin.qq.com/s?__biz=MzA4OTIyMzgxMw==&mid=2659376767&idx=1&sn=3f1f161a9082841d31df49d6c6f95c4d&chksm=8a5cf4ecd3327cf83914bbc5d7161303d89d352b4e0f558a983d067732090b307a1339fd15c6#rd",
    publish_time: "2025-11-17 09:02:39",
    cover: "http://127.0.0.1:8000/media/media/article_covers/%E5%A4%9A%E6%AC%A1%E5%8A%A0%E5%8D%B0%EF%BC%8C%E6%B8%85%E5%8D%8E%E8%BF%99%E6%9C%AC%E6%95%99%E6%9D%90%E2%80%9C%E6%8E%A5%E5%9C%B0%E6%B0%94%E2%80%9D%EF%BC%81.jpeg",
    summary: "清华大学法学院教授王亚新、陈杭平与中国政法大学刘君博教授合作编写的《中国民事诉讼法重点讲义》是一本创新教材...",
    tags: ["其他内容"],
    key_info: "民事诉讼法,教材,清华大学,法学教育,案例教学",
    is_favorited: 0,
    avatar: "http://127.0.0.1:8000/media/account_avatars/tsinghua.png"
  },
  {
    id: 111,
    title: "多次加印，清华这本教材“接地气”！",
    account_name: "清华大学",
    article_url: "https://mp.weixin.qq.com/s?__biz=MzA4OTIyMzgxMw==&mid=2659376767&idx=1&sn=3f1f161a9082841d31df49d6c6f95c4d&chksm=8a5cf4ecd3327cf83914bbc5d7161303d89d352b4e0f558a983d067732090b307a1339fd15c6#rd",
    publish_time: "2025-11-17 09:02:39",
    cover: "http://127.0.0.1:8000/media/media/article_covers/%E5%A4%9A%E6%AC%A1%E5%8A%A0%E5%8D%B0%EF%BC%8C%E6%B8%85%E5%8D%8E%E8%BF%99%E6%9C%AC%E6%95%99%E6%9D%90%E2%80%9C%E6%8E%A5%E5%9C%B0%E6%B0%94%E2%80%9D%EF%BC%81.jpeg",
    summary: "清华大学法学院教授王亚新、陈杭平与中国政法大学刘君博教授合作编写的《中国民事诉讼法重点讲义》是一本创新教材...",
    tags: ["其他内容"],
    key_info: "民事诉讼法,教材,清华大学,法学教育,案例教学",
    is_favorited: 0,
    avatar: "http://127.0.0.1:8000/media/account_avatars/tsinghua.png"
  },
  {
    id: 112,
    title: "多次加印，清华这本教材“接地气”！",
    account_name: "清华大学",
    article_url: "https://mp.weixin.qq.com/s?__biz=MzA4OTIyMzgxMw==&mid=2659376767&idx=1&sn=3f1f161a9082841d31df49d6c6f95c4d&chksm=8a5cf4ecd3327cf83914bbc5d7161303d89d352b4e0f558a983d067732090b307a1339fd15c6#rd",
    publish_time: "2025-11-17 09:02:39",
    cover: "http://127.0.0.1:8000/media/media/article_covers/%E5%A4%9A%E6%AC%A1%E5%8A%A0%E5%8D%B0%EF%BC%8C%E6%B8%85%E5%8D%8E%E8%BF%99%E6%9C%AC%E6%95%99%E6%9D%90%E2%80%9C%E6%8E%A5%E5%9C%B0%E6%B0%94%E2%80%9D%EF%BC%81.jpeg",
    summary: "清华大学法学院教授王亚新、陈杭平与中国政法大学刘君博教授合作编写的《中国民事诉讼法重点讲义》是一本创新教材...",
    tags: ["其他内容"],
    key_info: "民事诉讼法,教材,清华大学,法学教育,案例教学",
    is_favorited: 0,
    avatar: "http://127.0.0.1:8000/media/account_avatars/tsinghua.png"
  },
  {
    id: 113,
    title: "多次加印，清华这本教材“接地气”！",
    account_name: "清华大学",
    article_url: "https://mp.weixin.qq.com/s?__biz=MzA4OTIyMzgxMw==&mid=2659376767&idx=1&sn=3f1f161a9082841d31df49d6c6f95c4d&chksm=8a5cf4ecd3327cf83914bbc5d7161303d89d352b4e0f558a983d067732090b307a1339fd15c6#rd",
    publish_time: "2025-11-17 09:02:39",
    cover: "http://127.0.0.1:8000/media/media/article_covers/%E5%A4%9A%E6%AC%A1%E5%8A%A0%E5%8D%B0%EF%BC%8C%E6%B8%85%E5%8D%8E%E8%BF%99%E6%9C%AC%E6%95%99%E6%9D%90%E2%80%9C%E6%8E%A5%E5%9C%B0%E6%B0%94%E2%80%9D%EF%BC%81.jpeg",
    summary: "清华大学法学院教授王亚新、陈杭平与中国政法大学刘君博教授合作编写的《中国民事诉讼法重点讲义》是一本创新教材...",
    tags: ["其他内容"],
    key_info: "民事诉讼法,教材,清华大学,法学教育,案例教学",
    is_favorited: 0,
    avatar: "http://127.0.0.1:8000/media/account_avatars/tsinghua.png"
  },
  {
    id: 21,
    title: "61→512，清华创造新世界纪录！",
    account_name: "清华大学",
    article_url: "https://mp.weixin.qq.com/s?__biz=MzA4OTIyMzgxMw==&mid=2659376528&idx=1&sn=7354214a5304183cbbf71867b9a0a664&chksm=8a0180fcbc1d2fe07404dda628d285f14c95b5ed4e1e706b447efc923b153965b2ceec03ac01#rd",
    publish_time: "2025-11-14 09:19:26",
    cover: "http://127.0.0.1:8000/media/media/article_covers/61%E2%86%92512%EF%BC%8C%E6%B8%85%E5%8D%8E%E5%88%9B%E9%80%A0%E6%96%B0%E4%B8%96%E7%95%8C%E7%BA%AA%E5%BD%95%EF%BC%81.jpeg",
    summary: "清华大学交叉信息研究院段路明院士团队在离子量子计算机研究中取得重大进展...",
    tags: ["其他内容"],
    key_info: "量子计算,离子阱,清华大学,科研突破,世界纪录,自然期刊",
    is_favorited: 0,
    avatar: "http://127.0.0.1:8000/media/account_avatars/tsinghua.png"
  },
  {
    id: 31,
    title: "清华好物分享！",
    account_name: "清华大学",
    article_url: "https://mp.weixin.qq.com/s?__biz=MzA4OTIyMzgxMw==&mid=2659376296&idx=1&sn=75544b6d349b297ef89854dbaa2ca5e0&chksm=8a949eedff6bfd3fcfdb559def29b854c4842dfb1d9839d433d7a7be2ccd743c8bbef62c2e14#rd",
    publish_time: "2025-11-13 09:09:21",
    cover: "http://127.0.0.1:8000/media/media/article_covers/%E6%B8%85%E5%8D%8E%E5%A5%BD%E7%89%A9%E5%88%86%E4%BA%AB%EF%BC%81.jpeg",
    summary: "本文分享了清华大学的多件历史物品，包括运动服、照相机、计算尺、计算机和书桌等...",
    tags: ["其他内容"],
    key_info: "清华历史,体育精神,学术设备,爱国情怀,校园文化",
    is_favorited: 0,
    avatar: "http://127.0.0.1:8000/media/account_avatars/tsinghua.png"
  }
];

let mockArticles = [...mockLatestArticles];
let mockCustomizedLatestArticles = [...mockLatestArticles];
let mockCampusLatestArticles = [...mockLatestArticles];

// 初始化统一数据源管理
allArticleSources.mockArticles = mockArticles;
allArticleSources.mockRecommendedArticles = mockRecommendedArticles;
allArticleSources.mockLatestArticles = mockLatestArticles;
allArticleSources.mockCustomizedLatestArticles = mockCustomizedLatestArticles;
allArticleSources.mockCampusLatestArticles = mockCampusLatestArticles;

// 全局用户信息
let mockUserInfo = {
  avatarUrl: '/assets/icons/default-avatar.png',
  nickName: Mock.Random.ctitle(2, 6),
  gender: Mock.Random.integer(0, 2),
  school: Mock.Random.ctitle(4, 8) + '大学',
  studentId: '2025' + Mock.Random.integer(1000, 9999),
  email: Mock.Random.id() + '@school.com',
  phone: Mock.Random.integer(13000000000, 13999999999)
};

// ========== 收藏夹核心 Mock 数据 ==========
// 收藏夹列表（默认收藏夹id=1）
let mockCollectionList = [
  {
    "id": 5,
    "name": "收藏夹1",
    "description": "收藏夹",
    "is_default": false,
    "order": 0,
    "favorite_count": 0
  },
  {
    "id": 4,
    "name": "我的收藏夹",
    "description": "收藏夹",
    "is_default": false,
    "order": 0,
    "favorite_count": 0
  },
  {
    "id": 3,
    "name": "111",
    "description": "string",
    "is_default": false,
    "order": 0,
    "favorite_count": 0
  },
  {
    "id": 1,
    "name": "haha",
    "description": "ggqqqqqqqqqq",
    "is_default": true,
    "order": 0,
    "favorite_count": 0
  },
  {
    "id": 6,
    "name": "收藏夹",
    "description": "",
    "is_default": false,
    "order": 1,
    "favorite_count": 0
  },
  {
    "id": 7,
    "name": "收藏夹d",
    "description": "",
    "is_default": false,
    "order": 2,
    "favorite_count": 0
  }
];

// 收藏夹-文章映射（key=收藏夹id，value=文章id数组）
const collectionArticleMap = {
  "1": [],  // 默认收藏夹（id=1）
  "4": [],
  "5": [],
  "3": [],
  "6": [],
  "7": []
};

// 收藏记录表（核心修改：收藏ID改为数字）
let mockFavorites = [];
// 生成数字收藏ID的计数器
let favIdCounter = 1000;

// 1. 重构mockTodos数据结构（匹配后端返回格式）
let mockTodos = [
    {
      id: 1,
      title: "完成日历",
      note: "软工日历", // 对应前端content
      start_time: "2025-12-12 09:00:00", // 前端需要的startTime源字段
      end_time: "2025-12-13 10:00:00",   // 前端需要的endTime源字段
      status: 0, 
      created_at: "2025-12-01 10:00:00",
      updated_at: "2025-12-01 10:00:00",
      remind: true,
      article: 0
    },
    {
      id: 2,
      title: "完成桌宠",
      note: "小程序桌宠",
      start_time: "2025-12-12 14:00:00",
      end_time: "2025-12-12 16:00:00",
      status: 0,
      created_at: "2025-12-01 11:00:00",
      updated_at: "2025-12-01 11:00:00",
      remind: true,
      article: 0
    },
    {
      id: 3,
      title: "图书馆借书",
      note: "借《金瓶梅》",
      start_time: "2025-12-10 15:00:00",
      end_time: "2025-12-10 16:00:00",
      status: 1,
      created_at: "2025-11-30 09:00:00",
      updated_at: "2025-12-10 10:00:00",
      remind: true,
      article: 0
    },
    {
      id: 4,
      title: "体育打卡",
      note: "校园跑3公里",
      start_time: "2025-12-15 08:00:00",
      end_time: "2025-12-15 09:00:00",
      status: 0,
      created_at: "2025-12-05 08:00:00",
      updated_at: "2025-12-05 08:00:00",
      remind: true,
      article: 0
    }
  ];
  
  // 获取指定日期的待办
  exports.mockGetTodos = (date) => {
    console.log('Mock - 获取待办，日期：', date);
    let filteredTodos = [...mockTodos];
    
    // 有date参数时：筛选「目标日期在待办时间范围内」的项（适配跨天）
    if (date) {
      filteredTodos = mockTodos.filter(todo => {
        if (!todo.start_time || !todo.end_time) return false;
        
        // 解析时间并标准化
        const startDate = new Date(todo.start_time);
        const endDate = new Date(todo.end_time);
        const targetDate = new Date(date);
        targetDate.setHours(0, 0, 0, 0); // 目标日期 00:00:00
        const targetEnd = new Date(targetDate);
        targetEnd.setHours(23, 59, 59, 999); // 目标日期 23:59:59
        
        // 核心逻辑：待办开始时间 ≤ 目标日期结束 且 待办结束时间 ≥ 目标日期开始
        return startDate <= targetEnd && endDate >= targetDate;
      });
    }
    
    // 按开始时间倒序排列
    filteredTodos.sort((a, b) => new Date(b.start_time) - new Date(a.start_time));
    
    // 移除空的创建/更新时间（非必须字段）
    const resultTodos = filteredTodos.map(todo => {
      const { created_at, updated_at, ...rest } = todo;
      const result = { ...rest };
      // 仅保留有值的创建/更新时间
      if (created_at) result.created_at = created_at;
      if (updated_at) result.updated_at = updated_at;
      return result;
    });
    
    return {
      code: 200,
      msg: "success",
      data: {
        list: resultTodos,
        total: resultTodos.length
      }
    };
  };
  
  // 添加待办
  exports.mockAddTodo = (data) => {
    
    
    // 1. 校验核心字段：标题、开始/结束时间
    if (!data.title?.trim()) {
        return { code: 400, msg: "待办标题不能为空" };
      }
      if (!data.start_time || !data.end_time) {
        return { code: 400, msg: "待办开始/结束时间不能为空" };
      }
      // 2. 校验时间格式（YYYY-MM-DD HH:MM:SS）
      const timeReg = /^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$/;
      if (!timeReg.test(data.start_time) || !timeReg.test(data.end_time)) {
        return { code: 400, msg: "时间格式错误，请使用YYYY-MM-DD HH:MM:SS" };
      }
      // 3. 校验结束时间晚于开始时间
      const startTime = new Date(data.start_time.replace(' ', 'T'));
      const endTime = new Date(data.end_time.replace(' ', 'T'));
      if (endTime <= startTime) {
        return { code: 400, msg: "结束时间需晚于开始时间" };
      }
      // 4. 模拟成功返回（生成唯一ID）
      const newTodo = {
        id: Date.now(), // 模拟后端生成的ID
        ...data,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      };
      return { code: 200, msg: "添加成功", data: newTodo };
  };
  
  // 修改待办
  exports.mockUpdateTodo = (todoId, data) => {
    console.log('Mock - 修改待办：', { todoId, data });
    const id = Number(todoId);
    
    // 查找待办
    const todoIndex = mockTodos.findIndex(todo => todo.id === id);
    if (todoIndex === -1) return { code: 400, msg: '待办不存在' };
    
    // 匹配前端传入的字段（note/start_time/end_time等）
    if (data.title) mockTodos[todoIndex].title = data.title;
    if (data.note) mockTodos[todoIndex].note = data.note; // 前端传note，对应后端字段
    if (data.status !== undefined) mockTodos[todoIndex].status = data.status;
    if (data.start_time) mockTodos[todoIndex].start_time = data.start_time;
    if (data.end_time) mockTodos[todoIndex].end_time = data.end_time;
    mockTodos[todoIndex].updated_at = new Date().toISOString().replace('T', ' ').substring(0, 19);
    
    const updatedTodo = mockTodos[todoIndex];
    console.log('Mock - 待办修改成功：', updatedTodo);
    
    return {
      code: 200,
      msg: '待办修改成功',
      data: updatedTodo
    };
  };
  
  // 删除待办
  exports.mockDeleteTodo = (todoId) => {
    console.log('Mock - 删除待办：', todoId);
    const id = Number(todoId);
    
    // 查找待办
    const todoIndex = mockTodos.findIndex(todo => todo.id === id);
    if (todoIndex === -1) return { code: 400, msg: '待办不存在' };
    
    // 删除
    mockTodos.splice(todoIndex, 1);
    console.log('Mock - 待办删除成功，剩余列表：', mockTodos);
    
    return {
      code: 200,
      msg: '待办删除成功',
      data: { id }
    };
  };

// ========== 同步文章收藏状态函数 ==========
const updateArticleFavoriteStatus = (articleId, isFavorited, favoriteId = 0) => {
  const idType = typeof articleId === 'string' ? articleId : Number(articleId);
  // 同步所有数据源的收藏状态
  Object.values(allArticleSources).forEach(source => {
    const index = source.findIndex(item => item.id === idType);
    if (index !== -1) {
      // 收藏：设置为数字收藏ID；取消收藏：设置为0
      source[index].is_favorited = isFavorited ? favoriteId : 0;
    }
  });
  // 同步历史记录中的收藏状态
  mockHistories.forEach(history => {
    if (history.article.id == idType) {
      history.article.is_favorited = isFavorited ? favoriteId : 0;
    }
  });
};

// ========== 更新收藏夹数量 ==========
const updateCollectionCount = () => {
  mockCollectionList.forEach(collection => {
    const articleIds = collectionArticleMap[collection.id] || [];
    collection.favorite_count = articleIds.length;
  });
};

// ========== 移动收藏 Mock 函数 ==========
exports.mockMoveFavourite = function(favoriteId, targetCollectionId) {
  console.log('Mock - 移动收藏：', { favoriteId, targetCollectionId });
  
  // 统一转为数字ID（核心修复）
  const favId = Number(favoriteId);
  const targetId = Number(targetCollectionId);

  // 校验收藏ID是否存在
  const favIndex = mockFavorites.findIndex(item => item.id === favId);
  if (favIndex === -1) {
    return { code: 400, msg: '收藏记录不存在' };
  }

  // 校验目标收藏夹是否存在
  const collectionExist = mockCollectionList.some(item => item.id === targetId);
  if (!collectionExist) {
    return { code: 400, msg: '目标收藏夹不存在' };
  }

  // 获取收藏关联的文章ID
  const articleId = mockFavorites[favIndex].articleId;

  // 从原收藏夹移除文章
  Object.keys(collectionArticleMap).forEach(key => {
    const keyNum = Number(key);
    collectionArticleMap[keyNum] = collectionArticleMap[keyNum].filter(id => id !== articleId);
  });

  // 添加到新收藏夹
  if (!collectionArticleMap[targetId]) {
    collectionArticleMap[targetId] = [];
  }
  collectionArticleMap[targetId].push(articleId);

  // 更新收藏记录的收藏夹ID
  mockFavorites[favIndex].collectionId = targetId;

  // 更新收藏夹数量
  updateCollectionCount();

  return { code: 200, msg: '移动成功', data: { id: favId, target_collection_id: targetId } };
};

// ========== 获取收藏夹文章 ==========
exports.mockGetCollectionArticles = function(collectionId, startRank = 0) {
  const colId = Number(collectionId);
  const articleIds = collectionArticleMap[colId] || [];
  let allArticles = articleIds.map(articleId => {
    let article = mockArticles.find(item => item.id === articleId);
    if (!article) {
      article = mockLatestArticles.find(item => item.id === articleId) || 
                mockCustomizedLatestArticles.find(item => item.id === articleId) ||
                mockCampusLatestArticles.find(item => item.id === articleId) ||
                mockRecommendedArticles.find(item => item.id === articleId);
    }
    if (article) {
      return {
        id: article.id,
        title: article.title || '无标题',
        time: article.publish_time || article.time || '2025-01-01',
        tags: article.tags || [],
        desc: article.summary || article.desc || '无摘要',
        url: article.article_url || article.url || '',
        name: article.account_name || '未知作者',
        is_favorited: article.is_favorited || 0,
        cover: article.cover || article.image || 'http://127.0.0.1:8000/media/covers/default.jpg',
        avatar: article.avatar || 'http://127.0.0.1:8000/media/account_avatars/default.png'
      };
    }
    return null;
  }).filter(article => article !== null);

  const pageSize = 2;
  const paginatedArticles = allArticles.slice(startRank, startRank + pageSize);
  const hasMore = startRank + pageSize < allArticles.length;

  console.log(`Mock - 收藏夹${colId}文章：`, {
    total: allArticles.length,
    current: paginatedArticles.length,
    startRank,
    hasMore
  });

  return {
    code: 200,
    msg: "success",
    data: {
      articles: paginatedArticles,
      has_more: hasMore
    }
  };
};

// ========== 添加收藏 Mock 函数 ==========
exports.mockAddFavourite = (data) => {
  console.log('Mock - 新增收藏：', data);
  // 优先接收card组件传递的article_id
  const articleId = data.article_id || data.id || data.article?.id;
  
  if (!articleId) {
    return { code: 400, msg: '文章ID不能为空' };
  }

  const idType = typeof articleId === 'string' ? articleId : Number(articleId);
  // 检查是否已收藏
  const isExisted = mockFavorites.some(item => item.articleId === idType);
  if (isExisted) {
    const existingIndex = mockFavorites.findIndex(item => item.articleId === idType);
    const existingItem = mockFavorites.splice(existingIndex, 1)[0];
    mockFavorites.unshift(existingItem);
    console.log('Mock - 收藏已存在，更新位置：', mockFavorites);
    return { code: 200, msg: '收藏已存在', data: { id: existingItem.id } };
  }

  // 查找文章
  let articleInfo = mockLatestArticles.find(item => item.id === idType) ||
                    mockRecommendedArticles.find(item => item.id === idType) ||
                    mockCustomizedLatestArticles.find(item => item.id === idType) ||
                    mockCampusLatestArticles.find(item => item.id === idType) ||
                    mockArticles.find(item => item.id === idType);

  if (!articleInfo) {
    return { code: 400, msg: `未找到ID为${articleId}的文章` };
  }

  // 生成数字类型的收藏ID
  const favoriteId = favIdCounter++;
  // 获取默认收藏夹ID
  const defaultCollection = mockCollectionList.find(item => item.is_default);
  const defaultCollectionId = defaultCollection ? defaultCollection.id : 1;

  const newFavorite = {
    id: favoriteId, // 数字ID
    articleId: idType,
    collectionId: defaultCollectionId, // 关联默认收藏夹
    article: {
      id: articleInfo.id,
      title: articleInfo.title,
      publish_time: articleInfo.publish_time || articleInfo.time,
      tags: articleInfo.tags,
      desc: articleInfo.summary || articleInfo.desc || '无摘要',
      article_url: articleInfo.article_url || articleInfo.url || '',
      avatar: articleInfo.avatar || 'http://127.0.0.1:8000/media/account_avatars/default.png',
      account_name: articleInfo.account_name || articleInfo.name || '未知作者',
      is_favorited: favoriteId
    },
    createTime: new Date().toISOString().replace('T', ' ').substring(0, 19)
  };

  // 新增收藏
  mockFavorites.unshift(newFavorite);
  
  // 同步到默认收藏夹的文章映射
  if (!collectionArticleMap[defaultCollectionId]) {
    collectionArticleMap[defaultCollectionId] = [];
  }
  collectionArticleMap[defaultCollectionId].push(idType);

  // 更新收藏夹数量
  updateCollectionCount();

  // 同步文章收藏状态
  updateArticleFavoriteStatus(articleId, true, favoriteId);

  console.log('Mock - 收藏成功，当前收藏列表：', mockFavorites);
  console.log('Mock - 默认收藏夹文章映射：', collectionArticleMap[defaultCollectionId]);
  return { code: 200, msg: '收藏成功', data: { id: favoriteId } };
};

// ========== 取消收藏 Mock 函数 ==========
exports.mockDeleteFavourite = (favId) => {
  console.log('Mock - 取消收藏：', favId);
  const favIdNum = Number(favId);
  
  // 查找对应收藏记录
  const favIndex = mockFavorites.findIndex(item => item.id === favIdNum);
  if (favIndex === -1) return { code: 400, msg: '该收藏不存在' };
  
  const { articleId, collectionId } = mockFavorites[favIndex];
  
  // 从收藏列表删除
  mockFavorites.splice(favIndex, 1);
  
  // 从收藏夹映射中移除文章
  if (collectionArticleMap[collectionId]) {
    collectionArticleMap[collectionId] = collectionArticleMap[collectionId].filter(id => id !== articleId);
  }

  // 更新收藏夹数量
  updateCollectionCount();
  
  // 同步收藏状态
  updateArticleFavoriteStatus(articleId, false);
  
  console.log('Mock - 取消收藏后列表：', mockFavorites);
  return { code: 200, msg: '取消收藏成功' };
};

// ========== 获取收藏列表 ==========
exports.mockGetFavouriteList = () => {
  console.log('Mock - 获取收藏列表：', mockFavorites);
  return {
    code: 200,
    data: {
      list: mockFavorites,
      total: mockFavorites.length
    }
  };
};

// ========== 其他 Mock 函数 ==========
let mockHistories = [];
let mockSubscriptions = [
  {
    id: "tsinghua_official",
    public_account: {
      id: "tsinghua_official",
      name: "清华大学",
      icon: "/assets/icons/add.svg"
    },
    createTime: "2025-11-10 09:30:00",
    isSubscribed: "1"
  },
  {
    id: "test2",
    public_account: {
      id: "test2",
      name: "test2",
      icon: "/assets/icons/add.svg"
    },
    createTime: "2025-11-10 09:30:00",
    isSubscribed: 2
  },
  {
    id: "test3",
    public_account: {
      id: "tset3",
      name: "一",
      icon: "/assets/icons/add.svg"
    },
    createTime: "2025-11-10 09:30:00",
    isSubscribed: 3
  },
  {
    id: "test4",
    public_account: {
      id: "test4",
      name: "一二",
      icon: "/assets/icons/add.svg"
    },
    createTime: "2025-11-10 09:30:00",
    isSubscribed: 4
  },
  {
    id: "test5",
    public_account: {
      id: "test5",
      name: "一二三",
      icon: "/assets/icons/add.svg"
    },
    createTime: "2025-11-10 09:30:00",
    isSubscribed: 5
  },
  {
    id: "test6",
    public_account: {
      id: "test6",
      name: "一二三四",
      icon: "/assets/icons/add.svg"
    },
    createTime: "2025-11-10 09:30:00",
    isSubscribed: 6
  },
  {
    id: "test7",
    public_account: {
      id: "test7",
      name: "一二三四五",
      icon: "/assets/icons/add.svg"
    },
    createTime: "2025-11-10 09:30:00",
    isSubscribed: 7
  },
  {
    id: "test8",
    public_account: {
      id: "test8",
      name: "一二三四五六",
      icon: "/assets/icons/add.svg"
    },
    createTime: "2025-11-10 09:30:00",
    isSubscribed: 8
  },
  {
    id: "test9",
    public_account: {
      id: "test9",
      name: "一二三四五六七",
      icon: "/assets/icons/add.svg"
    },
    createTime: "2025-11-10 09:30:00",
    isSubscribed: 9
  },
  {
    id: "test10",
    public_account: {
      id: "test10",
      name: "一二三四五六七八",
      icon: "/assets/icons/add.svg"
    },
    createTime: "2025-11-10 09:30:00",
    isSubscribed: 10
  },
  {
    id: "test11",
    public_account: {
      id: "test11",
      name: "一二三四五六七八九",
      icon: "/assets/icons/add.svg"
    },
    createTime: "2025-11-10 09:30:00",
    isSubscribed: 11
  },
  {
    id: "test12",
    public_account: {
      id: "test12",
      name: "一二三四五六七八九十",
      icon: "/assets/icons/add.svg"
    },
    createTime: "2025-11-10 09:30:00",
    isSubscribed: 12
  },
  {
    id: "test13",
    public_account: {
      id: "test13",
      name: "一二三四五六七八九十一",
      icon: "/assets/icons/add.svg"
    },
    createTime: "2025-11-10 09:30:00",
    isSubscribed: 13
  },
  {
    id: "test14",
    public_account: {
      id: "test14",
      name: "一二三四五六七八九十一二",
      icon: "/assets/icons/add.svg"
    },
    createTime: "2025-11-10 09:30:00",
    isSubscribed: 14
  },
  {
    id: "test15",
    public_account: {
      id: "test15",
      name: "一二三四五六七八九十一二三",
      icon: "/assets/icons/add.svg"
    },
    createTime: "2025-11-10 09:30:00",
    isSubscribed: 15
  },
  {
    id: "test16",
    public_account: {
      id: "test16",
      name: "一二三四五六七八九十一二三四",
      icon: "/assets/icons/add.svg"
    },
    createTime: "2025-11-10 09:30:00",
    isSubscribed: 16
  },
  {
    id: "test17",
    public_account: {
      id: "test17",
      name: "一二三四五六七八九十一二三四五",
      icon: "/assets/icons/add.svg"
    },
    createTime: "2025-11-10 09:30:00",
    isSubscribed: 17
  },
  {
    id: "test18",
    public_account: {
      id: "test18",
      name: "一二三四五六七八九十一二三四五六",
      icon: "/assets/icons/add.svg"
    },
    createTime: "2025-11-10 09:30:00",
    isSubscribed: 18
  },
  {
    id: "test19",
    public_account: {
      id: "test19",
      name: "一二三四五六七八九十一二三四五六七",
      icon: "/assets/icons/add.svg"
    },
    createTime: "2025-11-10 09:30:00",
    isSubscribed: 19
  },
];

let mockAccountArticles = [
  {
    id: 1,
    accountId: 1,
    title: '清华大学 2025 年冬季学期选课通知',
    time: '2025-11-10',
    tags: ['选课', '通知'],
    desc: '2025 年冬季学期选课将于 11 月 15 日开启，请同学们及时登录教务系统完成选课。',
    url: 'https://example.com/article1',
    is_favorited: 0
  },
  {
    id: 2,
    accountId: 1,
    title: '清华大学 120 周年校庆倒计时 100 天',
    time: '2025-11-08',
    tags: ['校庆', '活动'],
    desc: '清华大学 120 周年校庆倒计时 100 天启动仪式将于 11 月 12 日举行。',
    url: 'https://example.com/article2',
    is_favorited: 0
  }
];

let mockCampusAccounts = [
  {
    id: "tsinghua_official",
    accountid: 10,
    icon: "assets/icons/add",
    is_subscribed: 1,
    name: "清华大学",
    fakeid: "MzA4OTIyMzgxMw==",
    is_default: true,
    last_crawl_time: "2025-11-19T21:26:51.028515+08:00",
    created_at: "2025-11-19T21:26:51.028515+08:00"
  },
  {
    id: "tsinghua_jiaowu",
    accountid: 8,
    icon: "/assets/icons/filter.svg",
    is_subscribed: 0, // 未订阅
    name: "清华教务处",
    fakeid: "MzUxMjEzNjc4OA==",
    is_default: false,
    last_crawl_time: "2025-11-19T21:26:57.028515+08:00",
    created_at: "2025-11-19T21:26:57.028515+08:00"
  },
  {
    id: "tsinghua_yjsy",
    accountid: 7,
    icon: "/assets/icons/search.svg",
    is_subscribed: 0,
    name: "清华研究生院",
    fakeid: "MzI0MjE4NjYxNg==",
    is_default: false,
    last_crawl_time: "2025-11-19T21:27:00.028515+08:00",
    created_at: "2025-11-19T21:27:00.028515+08:00"
  },
  {
    id: "tsinghua_xuesheng",
    accountid: 6,
    icon: "/assets/icons/heart.svg",
    is_subscribed: 1,
    name: "清华学生活动中心",
    fakeid: "MzYxNTk4NzUyMQ==",
    is_default: false,
    last_crawl_time: "2025-11-19T21:27:03.028515+08:00",
    created_at: "2025-11-19T21:27:03.028515+08:00"
  },
  {
    id: "pingan_tsinghua",
    accountid: 9,
    icon: "/assets/icons/return.svg",
    is_subscribed: 1,
    name: "平安清华",
    fakeid: "MzIxOTg0MTg2NQ==",
    is_default: true,
    last_crawl_time: "2025-11-19T21:26:54.028515+08:00",
    created_at: "2025-11-19T21:26:54.028515+08:00"
  }
];

// 筛选文章
exports.mockGetFilteredArticles = (data) => {
  console.log('Mock - 接收筛选参数：', data);
  const { tags = [], date_from, date_to } = data;
  let filtered = [...mockArticles];
  if (tags.length > 0) {
    filtered = filtered.filter(article => tags.some(tag => article.tags.includes(tag)));
  }
  if (date_from) filtered = filtered.filter(article => new Date(article.publish_time) >= new Date(date_from));
  if (date_to) filtered = filtered.filter(article => new Date(article.publish_time) <= new Date(date_to));
  filtered.sort((a, b) => new Date(b.publish_time) - new Date(a.publish_time));
  return { code: 200, data: { list: filtered, total: filtered.length } };
};

// 推荐文章
exports.mockGetRecommendedArticles = () => {
  console.log('Mock - 推荐文章列表：', mockRecommendedArticles);
  return { code: 200, data: { articles: mockRecommendedArticles, total: mockRecommendedArticles.length } };
};

// 首页最新文章
exports.mockGetLatestArticles = (startRank = 0, pageSize = 8) => {
  console.log('startrank(mock)(before)',startRank);
  const paginatedArticles = mockLatestArticles.slice(startRank, startRank + 10);
  startRank = startRank + mockLatestArticles.length;
  console.log('startrank(mock)(later)',startRank);
  const reach_end = startRank + pageSize >= mockLatestArticles.length;
  return { code: 200, data: { articles: paginatedArticles, total: mockLatestArticles.length, reach_end } };
};

// 自选/校园文章
exports.mockGetCustomizedLatestArticles = () => {
  const sortedArticles = [...mockCustomizedLatestArticles].sort((a, b) => new Date(b.publish_time) - new Date(a.publish_time));
  return { code: 200, data: { articles: sortedArticles, total: sortedArticles.length } };
};

exports.mockGetCampusLatestArticles = () => {
  const sortedArticles = [...mockCampusLatestArticles].sort((a, b) => new Date(b.publish_time) - new Date(a.publish_time));
  return { code: 200, data: { articles: sortedArticles, total: sortedArticles.length } };
};

// 获取指定公众号文章
exports.mockGetArticlesByAccount = (accountId) => {
  const articles = mockArticles.filter(item => item.accountid === accountId);
  articles.sort((a, b) => new Date(b.publish_time) - new Date(a.publish_time));
  return { code: 200, data: { list: articles, total: articles.length } };
};

// 订阅相关
exports.mockGetSubscriptions = () => {
  console.log('Mock - 获取订阅列表：', mockSubscriptions);
  return { code: 200, data: { list: mockSubscriptions, total: mockSubscriptions.length } };
};

exports.mockAddSubscription = (data) => {
  console.log('Mock - 添加新订阅：', data);
  mockSubscriptions.unshift(data);
  return { code: 200, msg: '订阅成功' };
};

exports.mockDeleteSubscription = (id) => {
  console.log('Mock - 删除单条订阅：', id);
  mockSubscriptions = mockSubscriptions.filter(item => item.id !== id);
  return { code: 200, msg: '删除订阅成功' };
};

exports.mockDeleteAllSubscriptions = () => {
  mockSubscriptions = [];
  return { code: 200, msg: '所有订阅删除成功' };
};

// 历史记录
exports.mockDeleteAllHistory = () => {
  mockHistories = [];
  return { code: 200, msg: '所有历史记录删除成功' };
};

exports.mockAddHistory = (data) => {
  console.log('Mock - 新增历史记录：', data);
  const articleId = data.article_id || data.id || data.article?.id;
  
  if (!articleId) {
    return { code: 400, msg: '文章ID不能为空' };
  }

  const idType = typeof articleId === 'string' ? articleId : Number(articleId);
  
  let articleInfo = mockLatestArticles.find(item => item.id === idType) ||
                    mockRecommendedArticles.find(item => item.id === idType) ||
                    mockCustomizedLatestArticles.find(item => item.id === idType) ||
                    mockCampusLatestArticles.find(item => item.id === idType) ||
                    mockArticles.find(item => item.id === idType);

  if (!articleInfo) {
    return { code: 400, msg: `未找到ID为${articleId}的文章` };
  }

  const existingIndex = mockHistories.findIndex(item => item.id == articleId);
  
  if (existingIndex !== -1) {
    const existingItem = mockHistories.splice(existingIndex, 1)[0];
    mockHistories.unshift(existingItem);
  } else {
    const newHistory = {
      id: articleId,
      article: {
        id: articleInfo.id,
        title: articleInfo.title,
        publish_time: articleInfo.publish_time || articleInfo.time,
        tags: articleInfo.tags,
        desc: articleInfo.summary || articleInfo.desc || '无摘要',
        article_url: articleInfo.article_url || articleInfo.url || '',
        account_name: articleInfo.account_name || articleInfo.name || '未知作者',
        is_favorited: articleInfo.is_favorited || 0,
        avatar: articleInfo.avatar || 'http://127.0.0.1:8000/media/account_avatars/default.png'
      }
    };
    mockHistories.unshift(newHistory);
  }

  if (mockHistories.length > 50) {
    mockHistories = mockHistories.slice(0, 50);
  }

  console.log('Mock - 新增历史后列表：', mockHistories);
  return { code: 200, msg: '历史记录添加成功', data: { id: articleId } };
};

exports.mockGetHistoryList = () => {
  console.log('Mock - 获取历史记录列表：', mockHistories);
  return {
    code: 200,
    data: {
      list: mockHistories,
      total: mockHistories.length
    }
  };
};

exports.mockDeleteHistory = (articleId) => {
  console.log('Mock - 删除历史记录：', articleId);

  if (!articleId) {
    return { code: 400, msg: '文章ID不能为空' };
  }

  const isExisted = mockHistories.some(item => item.id == articleId);
  if (!isExisted) {
    return { code: 400, msg: '该历史记录不存在' };
  }

  mockHistories = mockHistories.filter(item => item.id != articleId);
  console.log('Mock - 删除历史后列表：', mockHistories);
  return { code: 200, msg: '历史记录删除成功' };
};

// 收藏夹管理
exports.mockUpdateCollection = function(collectionId, data) {
  const collectionIndex = mockCollectionList.findIndex(item => item.id == collectionId);
  if (collectionIndex === -1) {
    return { code: 400, msg: '收藏夹不存在' };
  }

  if (data.name) mockCollectionList[collectionIndex].name = data.name;
  if (data.description) mockCollectionList[collectionIndex].description = data.description;

  const updatedCollection = mockCollectionList[collectionIndex];
  console.log('Mock - 更新收藏夹成功：', updatedCollection);
  return {
    code: 200,
    msg: '更新成功',
    data: updatedCollection
  };
};

exports.mockDeleteCollection = function(collectionId) {
  console.log('Mock - 删除收藏夹：', collectionId);
  const colId = Number(collectionId);
  
  const collectionIndex = mockCollectionList.findIndex(item => item.id === colId);
  if (collectionIndex === -1) {
    return { code: 400, msg: '收藏夹不存在' };
  }

  const targetCollection = mockCollectionList[collectionIndex];
  if (targetCollection.is_default) {
    return { code: 403, msg: '默认收藏夹不可删除' };
  }

  mockCollectionList.splice(collectionIndex, 1);

  delete collectionArticleMap[colId];

  console.log('Mock - 删除收藏夹成功，剩余收藏夹：', mockCollectionList);
  return { code: 200, msg: '删除成功' };
};

exports.mockGetCollections = function() {
  // 返回前更新收藏夹数量
  updateCollectionCount();
  return {
    code: 200,
    msg: "success",
    data: mockCollectionList 
  };
};

exports.mockAddCollection = function(data) {
  const maxId = mockCollectionList.length > 0 
    ? Math.max(...mockCollectionList.map(item => item.id)) 
    : 0;
  const newCollection = {
    id: maxId + 1,
    name: data.name,
    description: data.description || "",
    is_default: false,
    order: data.order || mockCollectionList.length,
    favorite_count: 0
  };
  mockCollectionList.push(newCollection);
  // 初始化收藏夹文章映射
  collectionArticleMap[newCollection.id] = [];
  return {
    code: 200,
    msg: "创建成功",
    data: newCollection
  };
};

exports.mockDeleteAllFavourite = () => {
  console.log('Mock - 删除所有收藏');
  const articleIds = mockFavorites.map(item => item.articleId);
  
  articleIds.forEach(articleId => updateArticleFavoriteStatus(articleId, false));
  
  // 清空收藏夹文章映射
  Object.keys(collectionArticleMap).forEach(key => {
    collectionArticleMap[key] = [];
  });
  // 更新收藏夹数量
  updateCollectionCount();
  
  mockFavorites = [];
  return { code: 200, msg: '所有收藏删除成功' };
};

// 登录/注册/用户信息
exports.mockRegister = (data) => {
  const { username, password } = data;
  const existUser = mockUsers.find(u => u.username === username);
  if (existUser) return { code: 400, msg: '用户名已存在' };
  const newUserId = mockUsers.length + 1;
  mockUsers.push({ id: newUserId, username, password });
  mockUserInfo.nickName = username;
  mockUserInfo.studentId = '2025' + Mock.Random.integer(1000, 9999);
  return { code: 200, msg: '注册成功', data: { token: `mock_token_${newUserId}` } };
};

exports.mockLogin = (data) => {
  const { username, password } = data;
  const user = mockUsers.find(u => u.username === username && u.password === password);
  if (!user) return { code: 400, msg: '用户名或密码错误' };
  mockUserInfo.nickName = username;
  return { code: 200, msg: '登录成功', data: { token: `mock_token_${user.id}` } };
};

exports.getMockUserInfo = () => {
  console.log('Mock - 获取用户资料：', mockUserInfo);
  return mockUserInfo;
};

exports.mockUpdateUsername = (data) => {
  if (data.username) {
    mockUserInfo.nickName = data.username;
    const currentUser = mockUsers.find(u => u.username === mockUserInfo.nickName);
    if (currentUser) currentUser.username = data.username;
  }
  return { code: 200, msg: '用户名修改成功' };
};

exports.mockUpdateEmail = (data) => {
  if (data.email) mockUserInfo.email = data.email;
  return { code: 200, msg: '邮箱修改成功' };
};

exports.mockUpdatePhone = (data) => {
  if (data.phone) mockUserInfo.phone = data.phone;
  return { code: 200, msg: '手机号修改成功' };
};

exports.mockUpdatePassword = (data) => {
  if (!data.old_password) return { code: 400, msg: '原密码不能为空' };
  if (data.new_password.length < 6) return { code: 400, msg: '新密码需6-16位' };
  const currentUser = mockUsers.find(u => u.username === mockUserInfo.nickName);
  if (currentUser) currentUser.password = data.new_password;
  return { code: 200, msg: '密码修改成功' };
};

exports.mockUpdateAvatar = (filePath) => {
  const newAvatarUrl = '/assets/icons/custom-avatar.png';
  mockUserInfo.avatarUrl = newAvatarUrl;
  return { code: 200, msg: '头像修改成功', data: { avatarUrl: newAvatarUrl } };
};

exports.mockGetCampusAccounts = () => {
    console.log('Mock - 校内公众号列表：', mockCampusAccounts);
    return {
      code: 200,
      msg: "success",
      data: {
        list: mockCampusAccounts, 
        total: mockCampusAccounts.length
      }
    };
  };