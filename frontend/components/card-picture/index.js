Component({
    options: {
        addGlobalClass: true, 
      },
    properties: {
      avatar: {
        type: String,
      },
      name: {
        type: String,
      }
    },
  
    data: {},
    methods: {
        // 添加点击卡片事件
    onClick() {
        this.triggerEvent('click', { name: this.data.name }); 
      }
    }
  });