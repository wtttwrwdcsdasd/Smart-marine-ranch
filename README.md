# 智慧海洋牧场可视化系统

## 项目简介
基于Flask的智慧海洋牧场管理系统，实现海洋环境监测、设备管理、数据可视化等功能。

## 安装指南
1. 克隆项目仓库
```bash
git clone https://github.com/your-repo/Smart-marine-ranch-visualization-system.git
```
啊萨达萨达萨达是
2. 安装依赖
```bash
pip install -r requirements.txt
```

3. 初始化数据库
```bash
python init_db.py
```

4. 运行开发服务器
```bash
python run.py
```

## 项目结构
```
Smart-marine-ranch-visualization-system/
├── app/
│   ├── routes/            # 路由模块
│   ├── services/          # 业务逻辑服务
│   ├── static/            # 静态资源
│   └── templates/         # 前端模板
├── instance/              # 数据库文件
├── requirements.txt       # 依赖列表
└── run.py                 # 启动脚本
```

## 鱼类识别

可在**picture_to_identify**文件夹中选取图片进行识别

## 智能问答

需要配置的API_key在对应的txt中