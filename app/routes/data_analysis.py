from flask import Blueprint, request, jsonify, send_file, flash, redirect, url_for
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import pandas as pd
import os
import io
from datetime import datetime
from ..models import WaterQuality, db
from ..services.data_analysis import DataAnalysisService

analysis_bp = Blueprint('analysis', __name__)
data_service = DataAnalysisService()

# 配置上传
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls'}

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@analysis_bp.route('/api/data/statistics')
@login_required
def get_statistics():
    """获取数据统计信息"""
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    province = request.args.get('province')
    
    try:
        if start_date:
            start_date = datetime.fromisoformat(start_date)
        if end_date:
            end_date = datetime.fromisoformat(end_date)
        
        stats = data_service.get_water_quality_statistics(start_date, end_date, province)
        
        if stats:
            return jsonify({'success': True, 'data': stats})
        else:
            return jsonify({'success': False, 'message': '没有找到数据'})
    
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@analysis_bp.route('/api/data/correlation')
@login_required
def get_correlation():
    """获取相关性分析"""
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    try:
        if start_date:
            start_date = datetime.fromisoformat(start_date)
        if end_date:
            end_date = datetime.fromisoformat(end_date)
        
        correlation_plot = data_service.generate_correlation_analysis(start_date, end_date)
        
        if correlation_plot:
            return jsonify({'success': True, 'plot': correlation_plot})
        else:
            return jsonify({'success': False, 'message': '数据不足，无法生成相关性分析'})
    
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@analysis_bp.route('/api/data/trend')
@login_required
def get_trend():
    """获取趋势分析"""
    parameter = request.args.get('parameter', 'pH')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    province = request.args.get('province')
    
    try:
        if start_date:
            start_date = datetime.fromisoformat(start_date)
        if end_date:
            end_date = datetime.fromisoformat(end_date)
        
        trend_plot = data_service.generate_trend_analysis(parameter, start_date, end_date, province)
        
        if trend_plot:
            return jsonify({'success': True, 'plot': trend_plot})
        else:
            return jsonify({'success': False, 'message': '数据不足，无法生成趋势分析'})
    
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@analysis_bp.route('/api/data/clustering')
@login_required
def get_clustering():
    """获取聚类分析"""
    n_clusters = int(request.args.get('n_clusters', 3))
    
    try:
        result = data_service.perform_clustering_analysis(n_clusters)
        
        if result:
            return jsonify({'success': True, 'data': result})
        else:
            return jsonify({'success': False, 'message': '数据不足，无法进行聚类分析'})
    
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@analysis_bp.route('/api/data/report')
@login_required
def get_report():
    """获取水质报告"""
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    try:
        if start_date:
            start_date = datetime.fromisoformat(start_date)
        if end_date:
            end_date = datetime.fromisoformat(end_date)
        
        report = data_service.generate_quality_report(start_date, end_date)
        
        if report:
            return jsonify({'success': True, 'data': report})
        else:
            return jsonify({'success': False, 'message': '没有找到数据'})
    
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@analysis_bp.route('/api/data/upload', methods=['POST'])
@login_required
def upload_data():
    """上传数据文件"""
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': '没有选择文件'})
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'message': '没有选择文件'})
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        
        try:
            # 读取文件
            if filename.endswith('.csv'):
                df = pd.read_csv(filepath, encoding='utf-8')
            else:
                df = pd.read_excel(filepath)
            
            # 数据验证和处理
            required_columns = ['monitor_time', 'province', 'section_name']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                os.remove(filepath)
                return jsonify({
                    'success': False, 
                    'message': f'缺少必要列: {", ".join(missing_columns)}'
                })
            
            # 数据导入
            success_count = 0
            error_count = 0
            
            for _, row in df.iterrows():
                try:
                    # 解析时间
                    monitor_time = pd.to_datetime(row['monitor_time'])
                    
                    water_quality = WaterQuality(
                        province=row.get('province'),
                        basin=row.get('basin'),
                        section_name=row.get('section_name'),
                        monitor_time=monitor_time,
                        quality_level=row.get('quality_level'),
                        temperature=row.get('temperature'),
                        pH=row.get('pH'),
                        dissolved_oxygen=row.get('dissolved_oxygen'),
                        conductivity=row.get('conductivity'),
                        turbidity=row.get('turbidity'),
                        permanganate_index=row.get('permanganate_index'),
                        ammonia_nitrogen=row.get('ammonia_nitrogen'),
                        total_phosphorus=row.get('total_phosphorus'),
                        total_nitrogen=row.get('total_nitrogen'),
                        chlorophyll_a=row.get('chlorophyll_a'),
                        algae_density=row.get('algae_density'),
                        station_status=row.get('station_status')
                    )
                    
                    db.session.add(water_quality)
                    success_count += 1
                    
                except Exception as e:
                    error_count += 1
                    continue
            
            db.session.commit()
            os.remove(filepath)  # 删除临时文件
            
            return jsonify({
                'success': True,
                'message': f'数据上传成功！成功导入 {success_count} 条记录，失败 {error_count} 条',
                'success_count': success_count,
                'error_count': error_count
            })
            
        except Exception as e:
            if os.path.exists(filepath):
                os.remove(filepath)
            return jsonify({'success': False, 'message': f'文件处理失败: {str(e)}'})
    
    return jsonify({'success': False, 'message': '不支持的文件格式'})

@analysis_bp.route('/api/data/export')
@login_required
def export_data():
    """导出数据"""
    format_type = request.args.get('format', 'csv')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    province = request.args.get('province')
    
    try:
        # 构建查询
        query = WaterQuality.query
        
        if start_date:
            start_date = datetime.fromisoformat(start_date)
            query = query.filter(WaterQuality.monitor_time >= start_date)
        if end_date:
            end_date = datetime.fromisoformat(end_date)
            query = query.filter(WaterQuality.monitor_time <= end_date)
        if province:
            query = query.filter(WaterQuality.province == province)
        
        data = query.all()
        
        if not data:
            return jsonify({'success': False, 'message': '没有找到数据'})
        
        # 转换为DataFrame
        df = pd.DataFrame([{
            'id': d.id,
            'province': d.province,
            'basin': d.basin,
            'section_name': d.section_name,
            'monitor_time': d.monitor_time,
            'quality_level': d.quality_level,
            'temperature': d.temperature,
            'pH': d.pH,
            'dissolved_oxygen': d.dissolved_oxygen,
            'conductivity': d.conductivity,
            'turbidity': d.turbidity,
            'permanganate_index': d.permanganate_index,
            'ammonia_nitrogen': d.ammonia_nitrogen,
            'total_phosphorus': d.total_phosphorus,
            'total_nitrogen': d.total_nitrogen,
            'chlorophyll_a': d.chlorophyll_a,
            'algae_density': d.algae_density,
            'station_status': d.station_status
        } for d in data])
        
        # 生成文件
        output = io.BytesIO()
        
        if format_type == 'csv':
            df.to_csv(output, index=False, encoding='utf-8-sig')
            output.seek(0)
            return send_file(
                output,
                mimetype='text/csv',
                as_attachment=True,
                download_name=f'water_quality_data_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
            )
        
        elif format_type == 'excel':
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='水质数据', index=False)
            output.seek(0)
            return send_file(
                output,
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                as_attachment=True,
                download_name=f'water_quality_data_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
            )
        
        else:
            return jsonify({'success': False, 'message': '不支持的导出格式'})
    
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500