// RBL 全局工具函数
Storage.prototype.setExpire = function(key, value, expire) {
    var obj = { data: value, time: Date.now(), expire: expire };
    localStorage.setItem(key, JSON.stringify(obj));
};
Storage.prototype.getExpire = function(key) {
    var val = localStorage.getItem(key);
    if (!val) return null;
    try {
        var obj = JSON.parse(val);
        if (Date.now() - obj.time > obj.expire) {
            localStorage.removeItem(key);
            return null;
        }
        return obj.data;
    } catch(e) {
        return val;
    }
};
