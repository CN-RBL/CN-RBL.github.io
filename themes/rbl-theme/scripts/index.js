/* global hexo */
const createLogger = require('hexo-log');
const logger = createLogger.default();

logger.info(`=============================
 🔴🔵 红蓝灯的主题 RBL Theme
=============================`);

// 注册 helper、generator、filter 等扩展
require('../include/register')(hexo);
