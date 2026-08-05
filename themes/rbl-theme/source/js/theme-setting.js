// RBL 主题配置脚本
// 主题色跟随系统偏好
(function() {
    var isNight = false;
    var hour = new Date().getHours();
    if (hour >= 19 || hour < 7) {
        isNight = true;
    }
    if (isNight) {
        document.body.className += ' night';
    }
})();
