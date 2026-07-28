/* global hexo */
const createLogger = require('hexo-log');
const logger = createLogger.default();

logger.info('RBL主题已启动！');

// 注册 helper、generator、filter 等扩展
require('../include/register')(hexo);
