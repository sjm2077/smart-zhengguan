// 数据加载器 - 从后端 API 获取 Excel 数据
// 启动方式: node server.js，然后打开 http://localhost:3000

let personnelData = [];
let dataLoaded = false;
let dataLoading = false;
let loadCallbacks = [];

/**
 * 从服务器 API 加载数据
 * @param {Function} callback - 数据加载完成后的回调
 */
function loadPersonnelData(callback) {
  if (dataLoaded) {
    if (callback) callback(personnelData);
    return;
  }

  if (callback) loadCallbacks.push(callback);

  if (dataLoading) return;
  dataLoading = true;

  fetch('/api/personnel')
    .then(response => {
      if (!response.ok) throw new Error('HTTP ' + response.status);
      return response.json();
    })
    .then(data => {
      personnelData = data;
      dataLoaded = true;
      dataLoading = false;
      console.log(`已加载 ${personnelData.length} 名教职工数据`);
      loadCallbacks.forEach(cb => cb(personnelData));
      loadCallbacks = [];
    })
    .catch(err => {
      dataLoading = false;
      console.error('数据加载失败:', err.message);
      // 如果 API 不可用，尝试使用内嵌数据回退
      if (typeof personnelDataFallback !== 'undefined') {
        console.warn('使用内嵌回退数据');
        personnelData = personnelDataFallback;
        dataLoaded = true;
        loadCallbacks.forEach(cb => cb(personnelData));
        loadCallbacks = [];
      }
    });
}