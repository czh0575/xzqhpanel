from flask import Flask, Blueprint, render_template, request, jsonify
import pymysql, os, xlsxwriter, zipfile
import pandas as pd
from datetime import datetime, timedelta

app = Flask(__name__, static_url_path='/xzqh/static')
bp = Blueprint('main', __name__, url_prefix='/xzqh', static_folder='static')  # 设置全局路由前缀

# 在Flask应用初始化后添加
DOWNLOAD_FOLDER = os.path.join(app.static_folder, 'downloads')
print(DOWNLOAD_FOLDER)

print(DOWNLOAD_FOLDER)
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

# 在应用启动时仅删除临时文件
def clean_temp_files():
    for filename in os.listdir(DOWNLOAD_FOLDER):
        file_path = os.path.join(DOWNLOAD_FOLDER, filename)
        if os.path.isfile(file_path):
            file_modified = datetime.fromtimestamp(os.path.getmtime(file_path))
            if datetime.now() - file_modified > timedelta(days=1):
                os.remove(file_path)

# 在应用启动时调用
clean_temp_files()

# 数据库配置
DB_CONFIG = {
    'host': '111.231.0.202',
    'user': 'macrodatabase',
    'password': '940212',
    'db': 'macrodatabase',
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}

# 构建层级条件
level_mapping = {
    'province': '省级',
    'city': '地级',
    'county': '县级'
}

@bp.route('/')
def index():
    return render_template('index.html')


def level_condition(levels, start_year, end_year):
    """生成根据行政层级和年份范围筛选的SQL查询语句。

    参数:
    levels (list): 需要筛选的行政层级名称列表（如['province', 'city']）。
    start_year (int): 数据起始年份。
    end_year (int): 数据结束年份。

    返回:
    str: 生成的SQL查询语句字符串。
    """
    # 生成年份字段列表
    year_columns = ', '.join([f'Y{year}' for year in range(start_year, end_year+1)])
    # 根据选择的层级导出原始数据
    o_mapped_levels = [level_mapping[level] for level in levels]
    o_level_conditions = ', '.join([f"'{level}'" for level in o_mapped_levels])

    if 'city' in levels:
        o_sql = f"""
            SELECT AreaCode, Level, Catalog, {year_columns}
            FROM adminarea
            WHERE Level IN ({o_level_conditions}) OR Catalog = '直辖市'
        """
    else:
        o_sql = f"""
            SELECT AreaCode, Level, Catalog, {year_columns}
            FROM adminarea
            WHERE Level IN ({o_level_conditions})
        """

    return o_sql


def get_panel(o_sql, start_year, end_year):
    """执行SQL查询并转换为宽面板和长面板数据

    Args:
        o_sql (str): 需要执行的原始SQL查询语句
        start_year (int): 数据时间范围的起始年份
        end_year (int): 数据时间范围的结束年份

    Returns:
        (pd.DataFrame, pd.DataFrame): 
            wide_panel (DataFrame): 过滤后的宽面板数据（保留至少一个年份有值的记录）
            long_panel (DataFrame): 转换后的长面板数据（每个年份单独一行）
    """
    with pymysql.connect(**DB_CONFIG) as conn:
        with conn.cursor() as cursor:
            cursor.execute(o_sql)
            results = cursor.fetchall()

            # 过滤全缺失记录形成宽面板
            filtered_results = [
                record for record in results
                if not all(
                    record.get(f'Y{year}') is None
                    for year in range(start_year, end_year+1)
                )
            ]

            # 转换为长面板格式
            long_panel_results = []
            for record in filtered_results:
                for year in range(start_year, end_year + 1):
                    # 从Y+年份的字段中获取行政区划名称
                    year_field = f'Y{year}'
                    if not record.get(year_field) is None:
                        long_panel_results.append({
                            'AreaCode': record['AreaCode'],
                            'Year': year,
                            'AreaName': record.get(year_field),
                            'Level': record['Level'],
                            'Catalog': record['Catalog']
                        })

            wide_panel = pd.DataFrame(filtered_results)
            long_panel = pd.DataFrame(long_panel_results)
    return wide_panel, long_panel


def genlongdf(level, start_year, end_year):
    """生成指定层级的长格式面板数据DataFrame
    
    参数:
    level (list): 区域层级列表，支持['city']或['province']
    start_year (int): 数据起始年份
    end_year (int): 数据结束年份
    
    返回:
    pandas.DataFrame: 包含重命名后的区域编码、名称和年份列的长格式数据
    """
    sql = level_condition(level, start_year, end_year)
    longpanel = get_panel(sql, start_year, end_year)[1][['AreaCode', 'AreaName', 'Year']]
    if level == ['city']:
        longpanel = longpanel.rename(columns={'AreaCode': 'CityCode', 'AreaName': 'CityName'})
    elif level == ['province']:
        longpanel = longpanel.rename(columns={'AreaCode': 'ProvinceCode', 'AreaName': 'ProvinceName'})
    return longpanel

def export_to_excel(df, sheetname, output_path):
    """将宽表和长表导出为带样式的Excel文件
    
    参数:
    long_df (DataFrame): 长格式数据面板
    output_path (str): 输出的Excel文件路径
    """
    with pd.ExcelWriter(output_path, engine='xlsxwriter') as writer:
        # 定义样式格式
        workbook = writer.book
        header_format = workbook.add_format({
            'bold': True,
            'font_name': '微软雅黑',
            'font_size': 10,
            'border': 1
        })
        normal_format = workbook.add_format({
            'font_name': '微软雅黑',
            'font_size': 10,
            'border': 1
        })

        max_row = df.shape[0]
        max_col = df.shape[1] - 1
        
        df.to_excel(writer, sheet_name= sheetname, index=False)
        sheet = writer.sheets[sheetname]
        # 应用标题行样式
        sheet.conditional_format(0, 0, 0, max_col, {'type': 'no_blanks', 'format': header_format})
        # 应用普通行样式
        sheet.conditional_format(
            1, 0, max_row, max_col,
            {
                'type': 'formula',
                'criteria': '1=1',  # 恒真条件，覆盖所有单元格
                'format': normal_format
            }
        )
        
def export_to_stata(df, output_path):
    """将DataFrame导出为Stata文件（.dta格式）"""
    try:
        # 导出为Stata 15格式（支持长变量名）
        df.to_stata(output_path, version=118, write_index=False)
    except Exception as e:
        raise RuntimeError(f"Stata导出失败：{str(e)}")

@bp.route('/generate', methods=['POST'])
def generate_panel():
    try:
        data = request.json
        start_year = int(data['startYear'])
        end_year = int(data['endYear'])
        levels = data['levels']
        include_parent = data['includeParent']

        mapenzh = {
            'AreaCode':'区划代码', 
            'Level': '区划层级', 
            'Catalog': '区划类型', 
            'Year': '年份', 
            'AreaName': '区划名称', 
            'CityCode':'地级代码', 
            'CityName': '地级名称', 
            'ProvinceCode': '省级代码', 
            'ProvinceName': '省级名称'
            }

        # 生成表单数据sql
        o_sql = level_condition(levels, start_year, end_year)
        # 根据命令生成面板数据
        widepanel, longpanel = get_panel(o_sql, start_year, end_year)
        widepanel['AreaCode'] = widepanel['AreaCode'].astype(int)
        output_widepanel = widepanel.rename(columns = mapenzh)
        if include_parent:
            if 'county' in levels:
                # 匹配城市代码
                zxscode = ['110000', '120000', '310000', '500000']
                longpanel['CityCode'] = longpanel['AreaCode'].apply(lambda x:str(x)[:4] + '00' if not (str(x)[:2] + '0000') in zxscode else str(x)[:2] + '0000')
                city_longpanel = genlongdf(['city'], start_year, end_year)
                merged_city = pd.merge(longpanel, city_longpanel, on=['CityCode', 'Year'], how='left')
                merged_city['CityCode'] = merged_city['CityCode'].astype(int)
                # 匹配省份代码
                merged_city['ProvinceCode'] = merged_city['AreaCode'].str[:2] + '0000'
                province_longpanel = genlongdf(['province'], start_year, end_year)
                merged_province = pd.merge(merged_city, province_longpanel, on=['ProvinceCode', 'Year'],how='left')
                merged_province['ProvinceCode'] = merged_province['ProvinceCode'].astype(int)
                merged_province['AreaCode'] = merged_province['AreaCode'].astype(int)
                output_longpanel = merged_province.rename(columns = mapenzh)
            elif 'city' in levels:
                # 匹配省份代码
                longpanel['ProvinceCode'] = longpanel['AreaCode'].str[:2] + '0000'
                province_longpanel = genlongdf(['province'], start_year, end_year)
                merged_province = pd.merge(longpanel, province_longpanel, on=['ProvinceCode', 'Year'],how='left')
                merged_province['ProvinceCode'] = merged_province['ProvinceCode'].astype(int)
                merged_province['AreaCode'] = merged_province['AreaCode'].astype(int)
                output_longpanel = merged_province.rename(columns = mapenzh)
        else:
            output_longpanel = longpanel.rename(columns = mapenzh)

        # 生成文件名（带时间戳防重复）
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        wide_filename_excel = f"{timestamp}_widepanel_{start_year}_{end_year}.xlsx"
        long_filename_excel = f"{timestamp}_longpanel_{start_year}_{end_year}.xlsx"
        wide_filename_stata = f"{timestamp}_widepanel_{start_year}_{end_year}.dta"
        long_filename_stata = f"{timestamp}_longpanel_{start_year}_{end_year}.dta"
        zip_filename = f"{timestamp}_panel_data_{start_year}_{end_year}.zip"


        # 生成并保存Excel和Stata文件
        try:
            # 宽面板（Excel和Stata）
            wide_path_excel = os.path.join(DOWNLOAD_FOLDER, wide_filename_excel)
            export_to_excel(output_widepanel, 'WidePanel', wide_path_excel)
            wide_path_stata = os.path.join(DOWNLOAD_FOLDER, wide_filename_stata)
            export_to_stata(output_widepanel, wide_path_stata)

            # 长面板（Excel和Stata）
            long_path_excel = os.path.join(DOWNLOAD_FOLDER, long_filename_excel)
            export_to_excel(output_longpanel, 'LongPanel', long_path_excel)
            long_path_stata = os.path.join(DOWNLOAD_FOLDER, long_filename_stata)
            export_to_stata(output_longpanel, long_path_stata)


            # 创建ZIP文件路径
            zip_path = os.path.join(DOWNLOAD_FOLDER, zip_filename)
            # 将文件打包为ZIP
            with zipfile.ZipFile(zip_path, 'w') as zipf:
                zipf.write(wide_path_excel, os.path.basename(wide_path_excel))
                zipf.write(wide_path_stata, os.path.basename(wide_path_stata))
                zipf.write(long_path_excel, os.path.basename(long_path_excel))
                zipf.write(long_path_stata, os.path.basename(long_path_stata))

            os.remove(wide_path_excel)
            os.remove(wide_path_stata)
            os.remove(long_path_excel)
            os.remove(long_path_stata)

        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': f'文件生成失败：{str(e)}'
            }), 500


        return jsonify({
            'status': 'success',
            'meta': {
                'downloads': {
                    'zip_file': f'/xzqh/static/downloads/{zip_filename}'
                },
                'startYear': start_year,
                'endYear': end_year,
                'levels': levels,
                "includeParent": include_parent
            }
        })

    except ValueError:
        return jsonify({'status': 'error', 'message': '无效的年份格式'}), 400
    except pymysql.MySQLError as e:
        return jsonify({'status': 'error', 'message': f'数据库错误：{str(e)}'}), 500
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'服务器错误：{str(e)}'}), 500


if __name__ == '__main__':
    app.register_blueprint(bp)
    app.run(host = '0.0.0.0', debug=False, port = 8716)