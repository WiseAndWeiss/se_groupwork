// 全局共享的卡片测试数据（多个页面可引用）
module.exports = {
    // 共享新闻数据
    sharedNewsList: [
      {
        id: 1,
        title: '全局测试文章试文章试文章试文章试文章试文章试文章试文章',
        author: '清华大学',
        time: '2025-11-01',
        tags: ['全局', '测试', '共享'],
        desc: '这是全局共享的测试数据，多个页面可复用',
        url: 'https://example.com/shared1',
      },
      {
        id: 2,
        title: '全局测试文章 2',
        author: '清华大学',
        time: '2025-11-02',
        tags: ['全局', '测试', '共享'],
        desc: '无需在每个页面重复写，直接引用即可',
        url: 'https://example.com/shared2',
      },
      {
        id: 3,
        title: '全局测试文章 1',
        author: '清华大学',
        time: '2025-11-03',
        tags: ['全局', '测试', '共享'],
        desc: '这是全局共享的测试数据，多个页面可复用',
        url: 'https://example.com/shared1',
      },
      {
        id: 4,
        title: '全局测试文章 1',
        author: '清华大学',
        time: '2025-11-04',
        tags: ['全局', '测试', '共享'],
        desc: '这是全局共享的测试数据，多个页面可复用',
        url: 'https://example.com/shared1',
      },
      {
        id: 5,
        title: '全局测试文章 1',
        author: '清华大学',
        time: '2025-11-04',
        tags: ['全局', '测试', '独享'],
        desc: '这是全局共享的测试数据，多个页面可复用',
        url: 'https://example.com/shared1',
      },
      {
        id: 6,
        title: '全局测试文章 1',
        author: '清华大学',
        time: '2025-11-05',
        tags: ['全局', '测试', '共享'],
        desc: '这是全局共享的测试数据，多个页面可复用',
        url: 'https://example.com/shared1',
      },
      {
        id: 7,
        title: '全局测试文章 1',
        author: '清华大学',
        time: '2025-11-06',
        tags: ['全局', '测试', '独享'],
        desc: '这是全局共享的测试数据，多个页面可复用',
        url: 'https://example.com/shared1',
      },
    ],

    campusOfficialTestList: [
        {
          id: 1, // 唯一标识，用于wx:key
          name: '清华大学官方号', // 公众号名称
          avatar: '/assets/campus/tsinghua.png' 
        },
        {
          id: 2,
          name: '紫荆公寓服务号',
          avatar: '/assets/campus/zijing.jpg' 
        },
        {
          id: 3,
          name: '社会实践',
          avatar: '/assets/campus/social.jpg' 
        },
        {
          id: 4,
          name: '学生社团联合会',
          avatar: '/assets/campus/club.jpg' 
        },
        {
          id: 5,
          name: '校学生会',
          avatar: '/assets/campus/union.jpg' 
        }
      ]
  };