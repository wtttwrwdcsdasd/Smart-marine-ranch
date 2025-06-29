import os
import json
import re
from datetime import datetime
from bs4 import BeautifulSoup
sas
from app import create_app, db
# 确保所有需要用到的模型都被导入
from app.models import User, RanchLocation, WaterQuality

# --- 数据清洗辅助函数 ---
def clean_html_and_get_float(html_string):
    """从包含HTML的字符串中提取浮点数，处理'--'等无效值"""
    if not isinstance(html_string, str) or html_string in ('--', '*', ''):
        return None
    try:
        # 优先使用正则表达式从HTML标签中提取内容，效率更高
        match = re.search(r'>([\d.-]+)<', html_string)
        if match:
            return float(match.group(1))
        # 如果正则匹配失败（例如字符串本身就是数字），则直接尝试转换
        return float(html_string)
    except (ValueError, TypeError):
        return None

def parse_monitoring_time(time_str, year_str):
    """将 'MM-DD HH:MM' 格式的字符串和年份结合，转换为datetime对象"""
    if not time_str or not year_str:
        return None
    try:
        full_datetime_str = f"{year_str}-{time_str}"
        return datetime.strptime(full_datetime_str, '%Y-%m-%d %H:%M')
    except ValueError:
        # 如果格式不匹配，返回None，避免程序中断
        return None

# --- 主程序 ---
app = create_app()

with app.app_context():
    print("初始化数据库表...")
    db.create_all()

    # 2. 初始化用户和位置数据
    if not User.query.filter_by(username='admin').first():
        print("检测到用户数据未初始化，正在创建默认用户和位置...")
        
        # 创建管理员账户
        admin = User(username='admin', role='admin')
        admin.set_password('admin123')
        db.session.add(admin)
        
        # 创建普通用户账户
        user = User(username='user', role='user')
        user.set_password('user123')
        db.session.add(user)
        
        # 添加示例牧场位置
        if not RanchLocation.query.first():
            locations = [
                RanchLocation(name='青岛海洋牧场', latitude=36.0671, longitude=120.3826, description='山东青岛近海海洋牧场'),
                RanchLocation(name='舟山海洋牧场', latitude=30.0444, longitude=122.1997, description='浙江舟山群岛海洋牧场'),
                RanchLocation(name='北部湾海洋牧场', latitude=21.4735, longitude=109.1192, description='广西北部湾海洋牧场')
            ]
            db.session.add_all(locations)
        
        db.session.commit()
        print("用户和位置数据初始化完成。")
    else:
        print("用户数据已存在。")

    # 3. 初始化水质数据
    if not WaterQuality.query.first():
        base_dir = os.path.join('water_data', '水质数据')
        if not os.path.exists(base_dir):
            print(f"水质数据目录不存在: {base_dir}，无法导入。")
        else:
            all_records_to_add = []
            for month_folder in os.listdir(base_dir):
                month_path = os.path.join(base_dir, month_folder)
                if not os.path.isdir(month_path) or not month_folder.startswith('202'):
                    continue
                
                year_str = month_folder[:4]
                for fname in os.listdir(month_path):
                    if not fname.endswith('.json'):
                        continue
                    
                    fpath = os.path.join(month_path, fname)
                    print(f"  - 正在处理: {fpath}")
                    with open(fpath, 'r', encoding='utf-8') as f:
                        try:
                            data = json.load(f)
                            tbody = data.get('tbody', [])
                            for row in tbody:
                                if not row or len(row) < 17: continue
                                monitor_time_obj = parse_monitoring_time(row[3], year_str)
                                if not monitor_time_obj: continue

                                record = WaterQuality(
                                    province=row[0], basin=row[1],
                                    section_name=BeautifulSoup(row[2], 'html.parser').get_text(strip=True) if row[2] else None,
                                    monitor_time=monitor_time_obj, quality_level=row[4] if row[4] else None,
                                    temperature=clean_html_and_get_float(row[5]), pH=clean_html_and_get_float(row[6]),
                                    dissolved_oxygen=clean_html_and_get_float(row[7]), conductivity=clean_html_and_get_float(row[8]),
                                    turbidity=clean_html_and_get_float(row[9]), permanganate_index=clean_html_and_get_float(row[10]),
                                    ammonia_nitrogen=clean_html_and_get_float(row[11]), total_phosphorus=clean_html_and_get_float(row[12]),
                                    total_nitrogen=clean_html_and_get_float(row[13]), chlorophyll_a=clean_html_and_get_float(row[14]),
                                    algae_density=clean_html_and_get_float(row[15]), station_status=row[16] if row[16] else None
                                )
                                all_records_to_add.append(record)
                        except Exception as e:
                            print(f"    ! 处理文件 {fname} 时发生错误: {e}")
            
            if all_records_to_add:
                print(f"准备将 {len(all_records_to_add)} 条数据存入数据库...")
                db.session.bulk_save_objects(all_records_to_add)
                db.session.commit()
                print("水质数据导入成功！")
            else:
                print("没有找到可导入的水质数据。")
    else:
        print("水质数据已存在，跳过导入。")

    print("\n所有数据库初始化任务完成")
