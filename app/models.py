from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(150), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='user')  # 'user' 或 'admin'
    
    def set_password(self, password):
        """创建哈希密码"""
        self.password_hash = generate_password_hash(password)

    # 3. 添加 check_password 方法
    def check_password(self, password):
        """检查哈希密码"""
        return check_password_hash(self.password_hash, password)

# 添加海洋牧场位置模型
class RanchLocation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    latitude = db.Column(db.Float, nullable=False)  # 纬度
    longitude = db.Column(db.Float, nullable=False)  # 经度
    description = db.Column(db.Text, nullable=True)
    
    def __repr__(self):
        return f'<RanchLocation {self.name}>'

# 添加天气数据模型
class WeatherData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    location_id = db.Column(db.Integer, db.ForeignKey('ranch_location.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    temperature = db.Column(db.Float, nullable=True)  # 温度，单位：摄氏度
    humidity = db.Column(db.Float, nullable=True)  # 湿度，百分比
    precipitation = db.Column(db.Float, nullable=True)  # 降水量，单位：mm
    wind_speed = db.Column(db.Float, nullable=True)  # 风速，单位：km/h
    wind_direction = db.Column(db.Float, nullable=True)  # 风向，单位：度
    pressure = db.Column(db.Float, nullable=True)  # 气压，单位：hPa
    cloud_cover = db.Column(db.Float, nullable=True)  # 云量，百分比
    visibility = db.Column(db.Float, nullable=True)  # 能见度，单位：km
    weather_code = db.Column(db.Integer, nullable=True)  # WMO天气代码
    
    def __repr__(self):
        return f'<WeatherData {self.timestamp}>'

class WaterQuality(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    province = db.Column(db.String(100))
    basin = db.Column(db.String(100))
    section_name = db.Column(db.String(200))
    # 关键改动：将 monitor_time 从字符串改为 DateTime 类型
    monitor_time = db.Column(db.DateTime, nullable=False, index=True)
    quality_level = db.Column(db.String(10))
    temperature = db.Column(db.Float)
    pH = db.Column(db.Float)
    dissolved_oxygen = db.Column(db.Float)
    conductivity = db.Column(db.Float)
    turbidity = db.Column(db.Float)
    permanganate_index = db.Column(db.Float)
    ammonia_nitrogen = db.Column(db.Float)
    total_phosphorus = db.Column(db.Float)
    total_nitrogen = db.Column(db.Float)
    chlorophyll_a = db.Column(db.Float)
    algae_density = db.Column(db.Float)
    station_status = db.Column(db.String(50))

    def __repr__(self):
        return f'<WaterQuality {self.section_name} @ {self.monitor_time}>'