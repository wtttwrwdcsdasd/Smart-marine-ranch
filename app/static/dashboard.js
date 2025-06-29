/**
 * @param {string} canvasId - a canvas's id
 * @param {string} filename - the file's name
 */
function downloadChart(canvasId, filename) {
    const chartInstance = Chart.getChart(canvasId);
    if (chartInstance) {
        const url = chartInstance.toBase64Image('image/png', 1);
        const link = document.createElement('a');
        link.href = url;
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    } else {
        console.error('无法找到图表实例:', canvasId);
        alert('下载失败，无法找到图表实例。');
    }
}

// 水质数据图表配置
const generateMockData = () => {
  const dates = Array.from({length:7}, (_,i) => {
    const d = new Date(Date.now() - (6-i)*86400000);
    return d.toISOString().split('T')[0];
  });
  return {
    dates,
    ph: dates.map(() => Math.random()*2 + 8.5),
    oxygen: dates.map(() => Math.random()*5 + 10),
    turbidity: dates.map(() => Math.random()*5 + 8)
  };
};

const initWaterQualityChart = (startDate, endDate) => {
    const data = generateMockData();
    
    new Chart(document.getElementById('waterQualityChart'), {
        type: 'line',
        data: {
            labels: data.dates,
            datasets: [{
                label: 'pH值',
                data: data.ph,
                borderColor: '#4dc9f6',
                tension: 0.1
            },{
                label: '溶解氧',
                data: data.oxygen,
                borderColor: '#f67019',
                tension: 0.1
            },{
                label: '浊度',
                data: data.turbidity,
                borderColor: '#537bc4',
                tension: 0.1
            }]
        },
        options: {
            responsive: true,
            interaction: { mode: 'index' },
            scales: { y: { title: { display: true, text: '数值' } } }
        }
    });
};

// 初始化控制功能
const initChartControls = () => {
    const today = new Date().toISOString().split('T')[0];
    document.getElementById('startDate').value = new Date(Date.now() - 604800000).toISOString().split('T')[0];
    document.getElementById('endDate').value = today;

    document.getElementById('refreshChart').addEventListener('click', () => {
        const start = document.getElementById('startDate').value;
        const end = document.getElementById('endDate').value;
        initWaterQualityChart(start, end);
    });

    document.getElementById('exportData').addEventListener('click', () => {
        downloadChart('waterQualityChart', '水质数据趋势图.png');
    });
};

// 初始化鱼类分布饼图
const initFishDistributionChart = () => {
    new Chart(document.getElementById('fishDistributionChart'), {
        type: 'pie',
        data: {
            labels: ['Bream', 'Roach', 'WhiteFish', 'Parkki', 'Perch', 'Smelt'],
            datasets: [{
                data: [35, 20, 6, 11, 73, 14],
                backgroundColor: ['#4dc9f6', '#f67019', '#f53794', '#537bc4', '#acc236', '#8549ba']
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { position: 'bottom' }
            }
        }
    });
};

// 初始化视频控制功能
const initVideoControls = () => {
    const videoInput = document.getElementById('videoUpload');
    const videoPlayer = document.getElementById('localVideo');
    const playButton = document.getElementById('playVideo');

    videoInput.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (file && file.type.startsWith('video/')) {
            const url = URL.createObjectURL(file);
            videoPlayer.src = url;
            videoPlayer.style.display = 'block';
            document.querySelector('.video-placeholder').style.display = 'none';
        }
    });

    playButton.addEventListener('click', () => {
        if (videoPlayer.src) {
            videoPlayer.play();
            playButton.innerHTML = '<i class="bi bi-pause-fill"></i>';
        }
    });

    videoPlayer.addEventListener('play', () => {
        playButton.innerHTML = '<i class="bi bi-pause-fill"></i>';
    });

    videoPlayer.addEventListener('pause', () => {
        playButton.innerHTML = '<i class="bi bi-play-fill"></i>';
    });

    videoPlayer.loop = true;
};

// 初始化所有功能
initChartControls();
initVideoControls();
initWaterQualityChart(document.getElementById('startDate').value, document.getElementById('endDate').value);
initFishDistributionChart();

document.addEventListener('DOMContentLoaded', function() {
    // 为鱼类分布图表下载按钮添加监听
    const downloadFishBtn = document.getElementById('downloadFishChartBtn');
    if(downloadFishBtn) {
        downloadFishBtn.addEventListener('click', () => {
            downloadChart('fishDistributionChart', '鱼类分布图.png');
        });
    }

    // 为设备状态图表下载按钮添加监听
    const downloadDeviceStatusBtn = document.getElementById('downloadDeviceStatusBtn');
    if(downloadDeviceStatusBtn) {
        downloadDeviceStatusBtn.addEventListener('click', () => {
            downloadChart('deviceStatusChart', '设备状态图.png');
        });
    }
});