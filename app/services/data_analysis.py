import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.graph_objects as go
import plotly.express as px
from plotly.utils import PlotlyJSONEncoder
import json
from datetime import datetime, timedelta
from sqlalchemy import func
from ..models import WaterQuality, WeatherData, db
from scipy import stats
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
import io
import base64

class DataAnalysisService:
    """数据分析服务类"""
    
    def __init__(self):
        self.scaler = StandardScaler()
    
    def get_water_quality_statistics(self, start_date=None, end_date=None, province=None):
        """获取水质数据统计信息"""
        query = WaterQuality.query
        
        if start_date:
            query = query.filter(WaterQuality.monitor_time >= start_date)
        if end_date:
            query = query.filter(WaterQuality.monitor_time <= end_date)
        if province:
            query = query.filter(WaterQuality.province == province)
        
        data = query.all()
        
        if not data:
            return None
        
        # 转换为DataFrame
        df = pd.DataFrame([{
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
            'quality_level': d.quality_level,
            'monitor_time': d.monitor_time,
            'province': d.province
        } for d in data])
        
        # 基础统计
        numeric_columns = ['temperature', 'pH', 'dissolved_oxygen', 'conductivity', 
                          'turbidity', 'permanganate_index', 'ammonia_nitrogen', 
                          'total_phosphorus', 'total_nitrogen', 'chlorophyll_a', 'algae_density']
        
        statistics = {
            'total_records': len(df),
            'date_range': {
                'start': df['monitor_time'].min().isoformat() if not df.empty else None,
                'end': df['monitor_time'].max().isoformat() if not df.empty else None
            },
            'quality_distribution': df['quality_level'].value_counts().to_dict(),
            'province_distribution': df['province'].value_counts().to_dict(),
            'parameter_statistics': {}
        }
        
        # 各参数统计
        for col in numeric_columns:
            if col in df.columns and df[col].notna().any():
                statistics['parameter_statistics'][col] = {
                    'mean': float(df[col].mean()),
                    'median': float(df[col].median()),
                    'std': float(df[col].std()),
                    'min': float(df[col].min()),
                    'max': float(df[col].max()),
                    'count': int(df[col].count())
                }
        
        return statistics
    
    def generate_correlation_analysis(self, start_date=None, end_date=None):
        """生成相关性分析"""
        query = WaterQuality.query
        
        if start_date:
            query = query.filter(WaterQuality.monitor_time >= start_date)
        if end_date:
            query = query.filter(WaterQuality.monitor_time <= end_date)
        
        data = query.all()
        
        if len(data) < 2:
            return None
        
        # 转换为DataFrame
        df = pd.DataFrame([{
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
            'algae_density': d.algae_density
        } for d in data])
        
        # 计算相关性矩阵
        correlation_matrix = df.corr()
        
        # 生成热力图
        fig = px.imshow(correlation_matrix, 
                       text_auto=True, 
                       aspect="auto",
                       title="水质参数相关性分析")
        
        return json.dumps(fig, cls=PlotlyJSONEncoder)
    
    def generate_trend_analysis(self, parameter, start_date=None, end_date=None, province=None):
        """生成趋势分析"""
        query = WaterQuality.query
        
        if start_date:
            query = query.filter(WaterQuality.monitor_time >= start_date)
        if end_date:
            query = query.filter(WaterQuality.monitor_time <= end_date)
        if province:
            query = query.filter(WaterQuality.province == province)
        
        data = query.order_by(WaterQuality.monitor_time).all()
        
        if not data:
            return None
        
        # 提取数据
        dates = [d.monitor_time for d in data]
        values = [getattr(d, parameter) for d in data if getattr(d, parameter) is not None]
        valid_dates = [dates[i] for i, d in enumerate(data) if getattr(d, parameter) is not None]
        
        if len(values) < 2:
            return None
        
        # 创建趋势图
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=valid_dates, y=values, mode='lines+markers', name=parameter))
        
        # 添加趋势线
        if len(values) > 1:
            z = np.polyfit(range(len(values)), values, 1)
            p = np.poly1d(z)
            fig.add_trace(go.Scatter(x=valid_dates, y=p(range(len(values))), 
                                   mode='lines', name='趋势线', line=dict(dash='dash')))
        
        fig.update_layout(title=f'{parameter}趋势分析', xaxis_title='时间', yaxis_title=parameter)
        
        return json.dumps(fig, cls=PlotlyJSONEncoder)
    
    def perform_clustering_analysis(self, n_clusters=3):
        """执行聚类分析"""
        # 获取最近一个月的数据
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        data = WaterQuality.query.filter(
            WaterQuality.monitor_time >= start_date,
            WaterQuality.monitor_time <= end_date
        ).all()
        
        if len(data) < n_clusters:
            return None
        
        # 准备数据
        features = ['temperature', 'pH', 'dissolved_oxygen', 'conductivity', 
                   'turbidity', 'permanganate_index', 'ammonia_nitrogen']
        
        df = pd.DataFrame([{
            feature: getattr(d, feature) for feature in features
        } for d in data])
        
        # 删除包含NaN的行
        df_clean = df.dropna()
        
        if len(df_clean) < n_clusters:
            return None
        
        # 标准化数据
        X_scaled = self.scaler.fit_transform(df_clean)
        
        # K-means聚类
        kmeans = KMeans(n_clusters=n_clusters, random_state=42)
        clusters = kmeans.fit_predict(X_scaled)
        
        # PCA降维用于可视化
        pca = PCA(n_components=2)
        X_pca = pca.fit_transform(X_scaled)
        
        # 创建散点图
        fig = px.scatter(x=X_pca[:, 0], y=X_pca[:, 1], color=clusters,
                        title='水质数据聚类分析（PCA降维）',
                        labels={'x': 'PC1', 'y': 'PC2'})
        
        return {
            'plot': json.dumps(fig, cls=PlotlyJSONEncoder),
            'cluster_centers': kmeans.cluster_centers_.tolist(),
            'explained_variance_ratio': pca.explained_variance_ratio_.tolist()
        }
    
    def generate_quality_report(self, start_date=None, end_date=None):
        """生成水质报告"""
        stats = self.get_water_quality_statistics(start_date, end_date)
        
        if not stats:
            return None
        
        # 水质等级评估
        quality_levels = stats['quality_distribution']
        total_records = stats['total_records']
        
        # 计算优良率
        excellent_count = quality_levels.get('I', 0) + quality_levels.get('II', 0)
        excellent_rate = (excellent_count / total_records * 100) if total_records > 0 else 0
        
        # 参数异常检测
        param_stats = stats['parameter_statistics']
        anomalies = []
        
        # 定义正常范围（示例）
        normal_ranges = {
            'pH': (6.5, 8.5),
            'dissolved_oxygen': (5.0, 15.0),
            'temperature': (0, 35),
            'turbidity': (0, 50)
        }
        
        for param, range_val in normal_ranges.items():
            if param in param_stats:
                mean_val = param_stats[param]['mean']
                if mean_val < range_val[0] or mean_val > range_val[1]:
                    anomalies.append({
                        'parameter': param,
                        'value': mean_val,
                        'normal_range': range_val,
                        'status': 'abnormal'
                    })
        
        report = {
            'summary': {
                'total_records': total_records,
                'date_range': stats['date_range'],
                'excellent_rate': round(excellent_rate, 2),
                'quality_distribution': quality_levels
            },
            'parameter_analysis': param_stats,
            'anomalies': anomalies,
            'recommendations': self._generate_recommendations(anomalies, excellent_rate)
        }
        
        return report
    
    def _generate_recommendations(self, anomalies, excellent_rate):
        """生成建议"""
        recommendations = []
        
        if excellent_rate < 80:
            recommendations.append("水质优良率偏低，建议加强水质监测和治理措施")
        
        for anomaly in anomalies:
            param = anomaly['parameter']
            if param == 'pH':
                recommendations.append("pH值异常，建议检查酸碱平衡，必要时进行pH调节")
            elif param == 'dissolved_oxygen':
                recommendations.append("溶解氧异常，建议检查增氧设备运行状态")
            elif param == 'turbidity':
                recommendations.append("浊度异常，建议检查过滤系统和沉淀处理")
        
        if not recommendations:
            recommendations.append("水质状况良好，继续保持现有管理措施")
        
        return recommendations