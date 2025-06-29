import requests
from datetime import datetime

class WeatherService:
    """简单的天气服务类"""
    
    BASE_URL = "https://api.open-meteo.com/v1/forecast"
    
    # 默认使用北京的坐标
    DEFAULT_LATITUDE = 39.9042
    DEFAULT_LONGITUDE = 116.4074
    
    @staticmethod
    def get_current_weather():
        """获取当前天气数据 - 使用固定位置"""
        params = {
            "latitude": WeatherService.DEFAULT_LATITUDE,
            "longitude": WeatherService.DEFAULT_LONGITUDE,
            "current": ["temperature_2m", "relative_humidity_2m", "precipitation", 
                        "wind_speed_10m", "wind_direction_10m", "weather_code",
                        "pressure_msl", "surface_pressure", "cloud_cover", 
                        "uv_index", "visibility", "is_day"],
            "timezone": "auto"
        }
        
        try:
            response = requests.get(WeatherService.BASE_URL, params=params)
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            print(f"获取天气数据失败: {str(e)}")
            return None
    
    @staticmethod
    def get_weather_forecast(days=7):
        """获取天气预报 - 使用固定位置"""
        params = {
            "latitude": WeatherService.DEFAULT_LATITUDE,
            "longitude": WeatherService.DEFAULT_LONGITUDE,
            "daily": ["temperature_2m_max", "temperature_2m_min", "precipitation_sum", 
                     "weather_code"],
            "timezone": "auto",
            "forecast_days": days
        }
        
        try:
            response = requests.get(WeatherService.BASE_URL, params=params)
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            print(f"获取天气预报失败: {str(e)}")
            return None
    
    @staticmethod
    def get_weather_code_description(code):
        """获取WMO天气代码对应的描述"""
        weather_codes = {
            0: "晴朗",
            1: "大部晴朗",
            2: "部分多云",
            3: "阴天",
            45: "雾",
            48: "沉积雾",
            51: "小毛毛雨",
            53: "中毛毛雨",
            55: "大毛毛雨",
            61: "小雨",
            63: "中雨",
            65: "大雨",
            71: "小雪",
            73: "中雪",
            75: "大雪",
            80: "小阵雨",
            95: "雷暴"
        }
        return weather_codes.get(code, "未知")