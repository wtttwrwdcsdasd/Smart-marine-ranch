import os
import pandas as pd
import sqlite3

ROOT_DIR = r'C:\Users\11615\Downloads\data\水质数据\water_quality_by_name'
DB_PATH = 'water_quality_structured.db'
SUPPORTED_EXTS = ['.xlsx', '.xls', '.csv']

# 省份和流域白名单
province_whitelist = [
    '上海市', '云南省', '内蒙古自治区', '北京市', '吉林省', '四川省', '天津市', '宁夏回族自治区', '安徽省', '山东省', '山西省', '广东省', '广西壮族自治区', '新疆维吾尔自治区', '江苏省', '江西省', '河北省', '河南省', '浙江省', '海南省', '湖北省', '湖南省', '甘肃省', '福建省', '西藏自治区', '贵州省', '辽宁省', '重庆市', '陕西省', '青海省', '黑龙江省'
]
basin_whitelist = [
    '长江流域', '滇池流域', '珠江流域', '西南诸河', '松花江流域', '西北诸河', '黄河流域', '海河流域', '淮河流域', '辽河流域', '太湖流域', '巢湖流域', '浙闽片河流'
]

def get_all_data_files(root_dir):
    data_files = []
    for dirpath, _, filenames in os.walk(root_dir):
        for fname in filenames:
            ext = os.path.splitext(fname)[-1].lower()
            if ext in SUPPORTED_EXTS:
                data_files.append(os.path.join(dirpath, fname))
    return data_files

def read_data_file(filepath):
    ext = os.path.splitext(filepath)[-1].lower()
    try:
        if ext in ['.xlsx', '.xls']:
            df = pd.read_excel(filepath)
        elif ext == '.csv':
            # 自动尝试多种编码和分隔符
            for enc in ['utf-8', 'gbk', 'gb2312']:
                try:
                    df = pd.read_csv(filepath, encoding=enc)
                    if df.shape[1] < 2:
                        # 可能是分隔符问题
                        df = pd.read_csv(filepath, encoding=enc, delimiter=';')
                    if df.shape[1] < 2:
                        df = pd.read_csv(filepath, encoding=enc, delimiter='\t')
                    break
                except Exception:
                    continue
        else:
            return None
        # 去除全空行
        df = df.dropna(how='all')
        return df
    except Exception as e:
        print(f"读取文件失败: {filepath}, 错误: {e}")
        return None

def main():
    # 创建数据库
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS water_quality")
    conn.commit()
    # 自动建表，所有字段都为TEXT
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS water_quality (
            id INTEGER PRIMARY KEY AUTOINCREMENT
        )
    """)
    conn.commit()

    files = get_all_data_files(ROOT_DIR)
    print(f"共找到 {len(files)} 个数据文件")
    total_inserted = 0
    skipped_files = 0
    skipped_rows = 0

    for f in files:
        df = read_data_file(f)
        if df is None or df.empty:
            print(f"跳过空文件: {f}")
            skipped_files += 1
            continue

        # 标准化字段名
        df.columns = [str(col).strip() for col in df.columns]

        # 必须有省份和流域字段
        if not ('省份' in df.columns and '流域' in df.columns):
            print(f"跳过无省份/流域字段的文件: {f}")
            skipped_files += 1
            continue

        # 只保留省份和流域在白名单的行
        valid_rows = df[
            df['省份'].isin(province_whitelist) &
            df['流域'].isin(basin_whitelist)
        ]
        skipped = len(df) - len(valid_rows)
        if skipped > 0:
            print(f"文件 {f} 跳过异常行: {skipped}")
            skipped_rows += skipped

        if valid_rows.empty:
            print(f"文件 {f} 没有有效数据行")
            continue

        # 动态添加新字段
        for col in valid_rows.columns:
            try:
                cursor.execute(f"ALTER TABLE water_quality ADD COLUMN '{col}' TEXT")
            except sqlite3.OperationalError:
                pass  # 字段已存在

        # 插入数据
        for _, row in valid_rows.iterrows():
            cols = ','.join([f"'{c}'" for c in row.index])
            placeholders = ','.join(['?'] * len(row))
            sql = f"INSERT INTO water_quality ({cols}) VALUES ({placeholders})"
            cursor.execute(sql, tuple(row.values))
            total_inserted += 1

        conn.commit()

    print(f"导入完成！共插入 {total_inserted} 行，跳过文件 {skipped_files} 个，跳过异常行 {skipped_rows} 行。")
    conn.close()

if __name__ == '__main__':
    main()
    import sqlite3
    conn = sqlite3.connect('water_quality_structured.db')
    cursor = conn.cursor()

    # 不同省份数量
    cursor.execute("SELECT COUNT(DISTINCT 省份) FROM water_quality")
    print("省份数量:", cursor.fetchone()[0])

    # 所有省份
    cursor.execute("SELECT DISTINCT 省份 FROM water_quality")
    print("所有省份:", [row[0] for row in cursor.fetchall()])

    # 不同流域数量
    cursor.execute("SELECT COUNT(DISTINCT 流域) FROM water_quality")
    print("流域数量:", cursor.fetchone()[0])

    # 所有流域
    cursor.execute("SELECT DISTINCT 流域 FROM water_quality")
    print("所有流域:", [row[0] for row in cursor.fetchall()])

    conn.close()