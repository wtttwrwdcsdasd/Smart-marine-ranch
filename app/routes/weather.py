from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required
from ..services.weather_service import WeatherService

weather_bp = Blueprint('weather', __name__)

@weather_bp.route('/weather')
@login_required
def weather_dashboard():
    """天气数据展示页面"""
    return render_template('weather.html')

@weather_bp.route('/api/weather/current')
@login_required
def get_current_weather():
    """获取当前天气数据 - 使用固定位置"""
    weather_data = WeatherService.get_current_weather()
    
    if weather_data:
        # 提取当前天气数据
        current = weather_data.get("current", {})
        weather_code = current.get("weather_code")
        
        return jsonify({
            'temperature': current.get("temperature_2m"),
            'humidity': current.get("relative_humidity_2m"),
            'precipitation': current.get("precipitation"),
            'wind_speed': current.get("wind_speed_10m"),
            'wind_direction': current.get("wind_direction_10m"),
            'pressure': current.get("pressure_msl"),
            'surface_pressure': current.get("surface_pressure"),
            'cloud_cover': current.get("cloud_cover"),
            'uv_index': current.get("uv_index"),
            'visibility': current.get("visibility"),
            'is_day': current.get("is_day"),
            'weather_code': weather_code,
            'weather_description': WeatherService.get_weather_code_description(weather_code)
        })
    else:
        return jsonify({'error': '无法获取天气数据'}), 404

@weather_bp.route('/api/weather/forecast')
@login_required
def get_weather_forecast():
    """获取天气预报 - 使用固定位置"""
    days = request.args.get('days', 7, type=int)
    
    forecast_data = WeatherService.get_weather_forecast(days)
    
    if forecast_data:
        # 添加天气描述
        daily = forecast_data.get('daily', {})
        weather_codes = daily.get('weather_code', [])
        weather_descriptions = [WeatherService.get_weather_code_description(code) for code in weather_codes]
        
        # 将天气描述添加到结果中
        result = forecast_data.copy()
        result['daily']['weather_description'] = weather_descriptions
        
        return jsonify(result)
    else:
        return jsonify({'error': '无法获取天气预报'}), 404