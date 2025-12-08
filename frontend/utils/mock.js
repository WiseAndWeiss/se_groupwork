
const Mock = {
    Random: {
      id() { return Math.random().toString(36).substr(2, 9); },
      ctitle(min, max) {
        const len = min + Math.floor(Math.random() * (max - min + 1));
        const chars = '一二三四五六七八九十甲乙丙丁戊己庚辛壬癸abcdefghijklmnopqrstuvwxyz';
        let title = '';
        for (let i = 0; i < len; i++) title += chars[Math.floor(Math.random() * chars.length)];
        return title;
      },
      datetime(format = 'yyyy-MM-dd HH:mm') {
        const date = new Date();
        return format.replace('yyyy', date.getFullYear())
          .replace('MM', (date.getMonth() + 1).toString().padStart(2, '0'))
          .replace('dd', date.getDate().toString().padStart(2, '0'))
          .replace('HH', date.getHours().toString().padStart(2, '0'))
          .replace('mm', date.getMinutes().toString().padStart(2, '0'));
      },
      integer(min, max) { return min + Math.floor(Math.random() * (max - min + 1)); }
    },
    mock(url, method, template) {
      // 存储 Mock 规则
      Mock.rules.push({ url, method: method.toUpperCase(), template });
    },
    rules: [],
    // 匹配 Mock 规则并返回数据
    match(url, method) {
      const rule = Mock.rules.find(r => 
        r.url === url && r.method === method.toUpperCase()
      );
      if (!rule) return null;
      // 解析模板生成数据（支持 | 语法，如 'list|3-5'）
      return Mock.parseTemplate(rule.template);
    },
    parseTemplate(template) {
      if (typeof template !== 'object') return template;
      const result = Array.isArray(template) ? [] : {};
      for (const key in template) {
        const value = template[key];
        if (typeof value === 'object') {
          result[key] = Mock.parseTemplate(value);
        } else if (typeof value === 'function') {
          result[key] = value.call(this);
        } else if (/\|/.test(key)) {
          // 处理 'list|3-5' 格式
          const [realKey, rule] = key.split('|');
          const [min, max] = rule.split('-').map(Number);
          if (Array.isArray(value)) {
            const len = max ? Mock.Random.integer(min, max) : min;
            result[realKey] = Array(len).fill(0).map(() => Mock.parseTemplate(value[0]));
          } else {
            result[realKey] = value;
          }
        } else {
          result[key] = value;
        }
      }
      return result;
    }
  };
  
  module.exports = Mock;