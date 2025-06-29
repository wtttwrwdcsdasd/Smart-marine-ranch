from flask import Blueprint, jsonify, request
import sqlite3
import os

data_bp = Blueprint('data', __name__)

DB_PATH = os.path.join('instance', 'water_quality_structured.db')

@data_bp.route('/api/water_quality_data')
def get_water_quality_data():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # 获取筛选参数
    province = request.args.get('province')
    basin = request.args.get('basin')
    page = int(request.args.get('page', 1))
    page_size = int(request.args.get('page_size', 100))
    offset = (page - 1) * page_size

    # 构建查询
    base_query = "SELECT * FROM water_quality"
    filters = []
    params = []

    if province:
        filters.append("省份 = ?")
        params.append(province)
    if basin:
        filters.append("流域 = ?")
        params.append(basin)
    if filters:
        base_query += " WHERE " + " AND ".join(filters)

    # 查询总数
    count_query = base_query.replace("SELECT *", "SELECT COUNT(*) as total")
    cursor.execute(count_query, params)
    total = cursor.fetchone()["total"]

    # 查询数据
    base_query += " LIMIT ? OFFSET ?"
    params.extend([page_size, offset])

    try:
        cursor.execute(base_query, params)
        rows = cursor.fetchall()
        result = [dict(row) for row in rows]
        response = {
            "data": result,
            "total": total,
            "page": page,
            "page_size": page_size
        }
        return jsonify(response)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()
        
@data_bp.route('/api/provinces')
def get_provinces():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT 省份 FROM water_quality")
    provinces = [row[0] for row in cursor.fetchall()]
    conn.close()
    return jsonify(provinces)

@data_bp.route('/api/basins')
def get_basins():
    province = request.args.get('province')
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    if province:
        cursor.execute("SELECT DISTINCT 流域 FROM water_quality WHERE 省份 = ?", (province,))
    else:
        cursor.execute("SELECT DISTINCT 流域 FROM water_quality")
    basins = [row[0] for row in cursor.fetchall()]
    conn.close()
    return jsonify(basins)