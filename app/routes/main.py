from flask import render_template, session, redirect, url_for, Blueprint, flash, request, jsonify
from flask_login import login_required, current_user
from ..models import User, db, WaterQuality
from datetime import datetime, timedelta
from sqlalchemy import func

main_bp = Blueprint('main', __name__)

@main_bp.route('/user')
@login_required
def user_dashboard():
    return render_template('dashboard.html', username=current_user.username)

@main_bp.route('/admin')
@login_required
def admin_page():
    if current_user.role != 'admin':
        return "无权限访问", 403
    return render_template('admin.html', username=current_user.username)

@main_bp.route('/')
def home():
    return render_template('index.html')

@main_bp.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', username=current_user.username)

@main_bp.route('/underwater')
@login_required
def underwater():
    return render_template('underwater.html', username=current_user.username)

@main_bp.route('/intelligence')
@login_required
def intelligence():
    return render_template('intelligence.html', username=current_user.username)

@main_bp.route('/weather')
@login_required
def weather():
    return render_template('weather.html', username=current_user.username)

@main_bp.route('/datacenter')
@login_required
def datacenter():
    return render_template('datacenter.html', username=current_user.username)

@main_bp.route('/admin/users')
@login_required
def manage_users_page():
    if current_user.role != 'admin':
        flash('您没有权限访问此页面。', 'warning')
        return redirect(url_for('main.user_dashboard'))
    
    users = User.query.all()
    return render_template('manage_users.html', username=current_user.username, users=users)

@main_bp.route('/add_user', methods=['POST'])
@login_required
def add_user():
    if current_user.role != 'admin':
        flash('操作失败：权限不足。', 'danger')
        return redirect(url_for('main.manage_users_page'))

    username = request.form.get('username')
    password = request.form.get('password')

    if not username or not password:
        flash('用户名和密码不能为空。', 'warning')
        return redirect(url_for('main.manage_users_page'))

    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        flash('用户名已存在，请使用其他名称。', 'warning')
        return redirect(url_for('main.manage_users_page'))

    new_user = User(username=username)
    new_user.set_password(password)
    db.session.add(new_user)
    db.session.commit()
    
    flash(f'用户 {username} 已成功添加！', 'success')
    return redirect(url_for('main.manage_users_page'))

@main_bp.route('/delete_user/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    if current_user.role != 'admin':
        flash('操作失败：权限不足。', 'danger')
        return redirect(url_for('main.manage_users_page'))

    user_to_delete = User.query.get_or_404(user_id)

    if user_to_delete.username == 'admin':
        flash('不能删除主管理员账户！', 'danger')
        return redirect(url_for('main.manage_users_page'))

    if user_to_delete.id == current_user.id:
        flash('不能删除当前登录的账户。', 'danger')
        return redirect(url_for('main.manage_users_page'))

    db.session.delete(user_to_delete)
    db.session.commit()

    flash(f'用户 {user_to_delete.username} 已被删除。', 'success')
    return redirect(url_for('main.manage_users_page'))

@main_bp.route('/api/water_quality_history')
def water_quality_history_api():
    """
    一个API端点，用于根据查询参数返回水质历史数据。
    """
    # 1. 从请求参数中获取查询条件
    data_type = request.args.get('dataType', 'temperature') # 默认为'temperature'
    start_date_str = request.args.get('startDate')
    end_date_str = request.args.get('endDate')

    # 2. 将字符串日期转换为 datetime 对象
    try:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        # 结束日期需要包含当天，所以我们设置为当天的 23:59:59
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d') + timedelta(days=1)
    except (ValueError, TypeError):
        # 如果日期格式错误或为空，则默认查询最近30天的数据
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=30)

    # 3. 根据 data_type 选择要查询的数据库列
    column_map = {
        'temperature': WaterQuality.temperature,
        'ph': WaterQuality.pH,
        'oxygen': WaterQuality.dissolved_oxygen,
        'turbidity': WaterQuality.turbidity,
        'conductivity': WaterQuality.conductivity
    }
    selected_column = column_map.get(data_type, WaterQuality.temperature)

    # 4. 从数据库查询数据 (日平均值)
    query = db.session.query(
        func.date(WaterQuality.monitor_time).label('date'),
        func.avg(selected_column).label('avg_value')
    ).filter(
        WaterQuality.monitor_time.between(start_date, end_date),
        selected_column.isnot(None)
    ).group_by('date').order_by('date')
    
    results = query.all()

    # 5. 格式化图表数据
    labels = [result.date for result in results]
    data_points = [round(result.avg_value, 2) if result.avg_value is not None else 0 for result in results]
    
    # 6. 获取表格的详细数据记录
    table_records_query = WaterQuality.query.filter(
        WaterQuality.monitor_time.between(start_date, end_date)
    ).order_by(WaterQuality.monitor_time.desc()).limit(10)
    
    table_data = [
        {
            'time': record.monitor_time.strftime('%Y-%m-%d %H:%M'),
            'temperature': record.temperature,
            'ph': record.pH,
            'oxygen': record.dissolved_oxygen,
            'turbidity': record.turbidity,
            'conductivity': record.conductivity,
            'status': record.station_status
        }
        for record in table_records_query
    ]

    # 7. 以JSON格式返回所有数据
    return jsonify({
        'labels': labels,
        'data': data_points,
        'tableData': table_data
    })

@main_bp.route('/api/doubao-chat', methods=['POST'])
@login_required
def doubao_chat():
    """
    智能问答API端点，集成豆包AI并提供数据查询功能
    """
    try:
        data = request.get_json()
        question = data.get('question', '')
        api_key = data.get('api_key', '')
        
        if not question:
            return jsonify({'error': '问题不能为空'}), 400
            
        if not api_key:
            return jsonify({'error': 'API Key不能为空'}), 400
        
        # 分析问题类型并获取相关数据
        context_data = analyze_question_and_get_data(question)
        
        # 构建增强的提示词
        enhanced_prompt = build_enhanced_prompt(question, context_data)
        
        # 调用豆包API（这里需要实际的API调用实现）
        # response = call_doubao_api(enhanced_prompt, api_key)
        
        # 临时模拟响应，实际使用时替换为真实API调用
        response = generate_smart_response(question, context_data)
        
        return jsonify({'response': response})
        
    except Exception as e:
        return jsonify({'error': f'服务异常: {str(e)}'}), 500

@main_bp.route('/api/fish-recognition', methods=['POST'])
def fish_recognition():
    """鱼类识别API"""
    try:
        # 检查是否有上传的文件
        if 'image' not in request.files:
            return jsonify({
                'status': 'error',
                'message': '未找到图片文件'
            }), 400
        
        file = request.files['image']
        if file.filename == '':
            return jsonify({
                'status': 'error',
                'message': '未选择文件'
            }), 400
        
        # 检查文件类型
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
        if not ('.' in file.filename and 
                file.filename.rsplit('.', 1)[1].lower() in allowed_extensions):
            return jsonify({
                'status': 'error',
                'message': '不支持的文件格式'
            }), 400
        
        # 模拟鱼类识别处理
        # 在实际应用中，这里会调用深度学习模型进行图像识别
        import random
        import time
        
        # 模拟处理时间
        time.sleep(1)
        
        # 模拟识别结果
        fish_types = [
            {'name': '鲈鱼', 'confidence': 0.92, 'avg_length': '25-35cm'},
            {'name': '武昌鱼', 'confidence': 0.88, 'avg_length': '20-30cm'},
            {'name': '狗鱼', 'confidence': 0.85, 'avg_length': '30-45cm'},
            {'name': '鲤鱼', 'confidence': 0.90, 'avg_length': '25-40cm'},
            {'name': '草鱼', 'confidence': 0.87, 'avg_length': '35-50cm'}
        ]
        
        selected_fish = random.choice(fish_types)
        predicted_length = round(random.uniform(20, 35), 1)
        health_score = round(random.uniform(80, 100), 1)
        
        result = {
            'fish_type': selected_fish['name'],
            'confidence': selected_fish['confidence'],
            'predicted_length': predicted_length,
            'health_score': health_score,
            'avg_length': selected_fish['avg_length'],
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'recommendations': generate_fish_recommendations(selected_fish['name'], predicted_length, health_score)
        }
        
        return jsonify({
            'status': 'success',
            'data': result
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'识别过程中发生错误: {str(e)}'
        }), 500

def generate_fish_recommendations(fish_type, length, health_score):
    """根据识别结果生成养殖建议"""
    recommendations = []
    
    # 根据鱼类类型给出建议
    if fish_type == '鲈鱼':
        recommendations.append('鲈鱼适宜在水温18-25°C环境中生长')
        recommendations.append('建议投喂高蛋白饲料，促进生长')
    elif fish_type == '武昌鱼':
        recommendations.append('武昌鱼喜欢清洁的水质环境')
        recommendations.append('适当增加溶解氧含量有利于健康')
    elif fish_type == '草鱼':
        recommendations.append('草鱼需要充足的植物性饲料')
        recommendations.append('定期检查水质pH值，保持在7.0-8.5')
    
    # 根据体长给出建议
    if length < 25:
        recommendations.append('鱼体较小，建议增加营养投喂')
    elif length > 35:
        recommendations.append('鱼体发育良好，可考虑适时收获')
    
    # 根据健康评分给出建议
    if health_score < 85:
        recommendations.append('健康状况需要关注，建议检查水质和饲料')
    elif health_score > 95:
        recommendations.append('鱼类健康状况优秀，继续保持当前养殖条件')
    
    return recommendations

def analyze_question_and_get_data(question):
    """
    分析问题并获取相关数据
    """
    context_data = {}
    
    # 获取最新水质数据
    if any(keyword in question for keyword in ['水质', 'pH', '温度', '溶解氧', '浊度', '电导率']):
        latest_water_data = get_latest_water_quality_data()
        context_data['water_quality'] = latest_water_data
        
        # 获取水质趋势数据
        trend_data = get_water_quality_trend()
        context_data['water_trend'] = trend_data
    
    # 获取鱼类相关数据（模拟数据）
    if any(keyword in question for keyword in ['鱼', '鱼类', '养殖', '产量', '生长']):
        fish_data = get_fish_data_simulation()
        context_data['fish_data'] = fish_data
    
    # 获取设备状态数据（模拟数据）
    if any(keyword in question for keyword in ['设备', '传感器', '摄像头', '维护']):
        equipment_data = get_equipment_status_simulation()
        context_data['equipment'] = equipment_data
    
    # 获取环境数据
    if any(keyword in question for keyword in ['环境', '天气', '气温', '湿度']):
        environment_data = get_environment_data_simulation()
        context_data['environment'] = environment_data
    
    return context_data

def get_latest_water_quality_data():
    """
    获取最新的水质数据
    """
    try:
        latest_record = WaterQuality.query.order_by(WaterQuality.monitor_time.desc()).first()
        if latest_record:
            return {
                'monitor_time': latest_record.monitor_time.strftime('%Y-%m-%d %H:%M:%S'),
                'temperature': latest_record.temperature,
                'pH': latest_record.pH,
                'dissolved_oxygen': latest_record.dissolved_oxygen,
                'turbidity': latest_record.turbidity,
                'conductivity': latest_record.conductivity,
                'quality_level': latest_record.quality_level,
                'section_name': latest_record.section_name
            }
    except Exception as e:
        print(f"获取水质数据错误: {e}")
    return None

def get_water_quality_trend():
    """
    获取水质趋势数据（最近7天）
    """
    try:
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=7)
        
        trend_data = db.session.query(
            func.date(WaterQuality.monitor_time).label('date'),
            func.avg(WaterQuality.temperature).label('avg_temp'),
            func.avg(WaterQuality.pH).label('avg_ph'),
            func.avg(WaterQuality.dissolved_oxygen).label('avg_oxygen')
        ).filter(
            WaterQuality.monitor_time.between(start_date, end_date)
        ).group_by('date').order_by('date').all()
        
        return [{
            'date': str(record.date),
            'temperature': round(record.avg_temp, 2) if record.avg_temp else None,
            'pH': round(record.avg_ph, 2) if record.avg_ph else None,
            'dissolved_oxygen': round(record.avg_oxygen, 2) if record.avg_oxygen else None
        } for record in trend_data]
    except Exception as e:
        print(f"获取水质趋势数据错误: {e}")
    return []

def get_fish_data_simulation():
    """
    模拟鱼类数据
    """
    return {
        'total_fish_count': 15420,
        'species': [
            {'name': '鲈鱼', 'count': 6800, 'avg_weight': 1.2, 'growth_rate': 0.15},
            {'name': '武昌鱼', 'count': 4320, 'avg_weight': 0.8, 'growth_rate': 0.12},
            {'name': '狗鱼', 'count': 4300, 'avg_weight': 1.5, 'growth_rate': 0.18}
        ],
        'feeding_schedule': '每日3次，上午8点、下午2点、晚上6点',
        'health_status': '良好',
        'estimated_harvest_date': '2024-08-15'
    }

def get_equipment_status_simulation():
    """
    模拟设备状态数据
    """
    return {
        'total_devices': 24,
        'online_devices': 22,
        'offline_devices': 2,
        'devices': [
            {'id': 'UW001', 'type': '水下摄像头', 'status': '正常', 'last_maintenance': '2024-01-15'},
            {'id': 'UW002', 'type': '水下摄像头', 'status': '信号不稳定', 'last_maintenance': '2024-01-10'},
            {'id': 'WQ001', 'type': '水质传感器', 'status': '正常', 'last_maintenance': '2024-01-20'},
            {'id': 'WQ002', 'type': '水质传感器', 'status': '需要校准', 'last_maintenance': '2024-01-05'}
        ]
    }

def get_environment_data_simulation():
    """
    模拟环境数据
    """
    return {
        'air_temperature': 22.5,
        'humidity': 68,
        'wind_speed': 12.3,
        'weather_condition': '多云',
        'water_surface_temperature': 18.2,
        'visibility': 8.5
    }

def build_enhanced_prompt(question, context_data):
    """
    构建增强的提示词
    """
    prompt = f"""你是一个海洋牧场智能助手，请基于以下实时数据回答用户问题：

用户问题：{question}

当前数据：
"""
    
    if 'water_quality' in context_data and context_data['water_quality']:
        water_data = context_data['water_quality']
        prompt += f"""
水质数据（{water_data['monitor_time']}）：
- 温度：{water_data['temperature']}°C
- pH值：{water_data['pH']}
- 溶解氧：{water_data['dissolved_oxygen']}mg/L
- 浊度：{water_data['turbidity']}NTU
- 电导率：{water_data['conductivity']}μS/cm
- 水质等级：{water_data['quality_level']}
- 监测点：{water_data['section_name']}
"""
    
    if 'fish_data' in context_data:
        fish_data = context_data['fish_data']
        prompt += f"""
鱼类养殖数据：
- 总鱼数：{fish_data['total_fish_count']}尾
- 鱼类品种：{', '.join([f"{s['name']}({s['count']}尾)" for s in fish_data['species']])}
- 健康状况：{fish_data['health_status']}
- 预计收获时间：{fish_data['estimated_harvest_date']}
"""
    
    if 'equipment' in context_data:
        equipment_data = context_data['equipment']
        prompt += f"""
设备状态：
- 设备总数：{equipment_data['total_devices']}台
- 在线设备：{equipment_data['online_devices']}台
- 离线设备：{equipment_data['offline_devices']}台
"""
    
    prompt += """

请基于以上数据，用专业但易懂的语言回答用户问题。如果数据显示有异常情况，请提供相应的建议。
"""
    
    return prompt

def generate_smart_response(question, context_data):
    """
    基于数据生成智能响应（模拟实现）
    """
    if 'water_quality' in context_data and context_data['water_quality']:
        water_data = context_data['water_quality']
        
        if '水质' in question or 'pH' in question or '温度' in question:
            response = f"""根据最新监测数据（{water_data['monitor_time']}），当前水质状况如下：

📊 **关键指标**：

• 水温：{water_data['temperature']}°C

• pH值：{water_data['pH']}

• 溶解氧：{water_data['dissolved_oxygen']}mg/L

• 浊度：{water_data['turbidity']}NTU

• 水质等级：{water_data['quality_level']}

💡 **分析建议**：

"""
            
            # 基于实际数据给出建议
            if water_data['pH'] and (water_data['pH'] < 6.5 or water_data['pH'] > 8.5):
                response += "• ⚠️ pH值偏离正常范围，建议检查水质调节系统\n\n"
            else:
                response += "• ✅ pH值正常，水质酸碱度适宜\n\n"
                
            if water_data['dissolved_oxygen'] and water_data['dissolved_oxygen'] < 5.0:
                response += "• ⚠️ 溶解氧偏低，建议增加增氧设备运行时间\n\n"
            else:
                response += "• ✅ 溶解氧充足，有利于鱼类生长\n\n"
                
            if water_data['temperature'] and (water_data['temperature'] < 15 or water_data['temperature'] > 25):
                response += "• ⚠️ 水温需要关注，可能影响鱼类活动\n\n"
            else:
                response += "• ✅ 水温适宜，符合养殖要求\n\n"
                
            return response
    
    if 'fish_data' in context_data:
        fish_data = context_data['fish_data']
        
        if any(keyword in question for keyword in ['鱼', '鱼类', '养殖', '产量']):
            return f"""🐟 **当前养殖状况**：

📈 **数量统计**：

• 总鱼数：{fish_data['total_fish_count']:,}尾

• 鲈鱼：{fish_data['species'][0]['count']:,}尾（平均{fish_data['species'][0]['avg_weight']}kg）

• 武昌鱼：{fish_data['species'][1]['count']:,}尾（平均{fish_data['species'][1]['avg_weight']}kg）

• 狗鱼：{fish_data['species'][2]['count']:,}尾（平均{fish_data['species'][2]['avg_weight']}kg）

🎯 **生长情况**：

• 整体健康状况：{fish_data['health_status']}

• 预计收获时间：{fish_data['estimated_harvest_date']}

• 投喂计划：{fish_data['feeding_schedule']}

💡 **管理建议**：

• 继续保持现有投喂频次

• 定期监测鱼类活动状态

• 根据生长情况适时调整饲料配比

"""
    
    if 'equipment' in context_data:
        equipment_data = context_data['equipment']
        
        if any(keyword in question for keyword in ['设备', '维护', '传感器']):
            return f"""🔧 **设备运行状态**：

📊 **总体概况**：

• 设备总数：{equipment_data['total_devices']}台

• 在线设备：{equipment_data['online_devices']}台

• 离线设备：{equipment_data['offline_devices']}台

• 运行率：{(equipment_data['online_devices']/equipment_data['total_devices']*100):.1f}%

⚠️ **需要关注的设备**：

• UW002水下摄像头：信号不稳定，建议检查连接线路

• WQ002水质传感器：需要校准，建议安排技术人员处理

🔧 **维护建议**：

• 定期检查设备连接状态

• 按计划进行设备校准和保养

• 及时更换老化的传感器元件

"""
    
    # 默认响应
    return """感谢您的咨询！作为海洋牧场智能助手，我可以为您提供：

🌊 **水质监测**：实时水质参数分析和建议

🐟 **养殖管理**：鱼类生长状况和饲养指导

🔧 **设备维护**：设备状态监控和维护提醒

📈 **数据分析**：历史趋势分析和预测建议

请告诉我您想了解哪个方面的具体信息，我会基于实时数据为您提供专业的分析和建议。

"""

@main_bp.route('/data_analysis')
@login_required
def data_analysis():
    return render_template('data_analysis.html', username=current_user.username)