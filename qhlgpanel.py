import os
# 需要安装pywebio==1.7.1，高于1.8.0会出问题，暂时搁置，等有空解决
from pywebio import start_server
from pywebio.input import *
from pywebio.output import *
from pywebio.session import info as session_info
import pandas as pd
import numpy as np
import time

def main():
    """行政区划面板生成工具
    """

    put_markdown(''' # 行政区划面板生成工具
    
    本工具用于生成1980-2023年任意连续年份（≥1年）的行政区划名称与代码的长、宽面板，可与任何需要行政区划的数据匹配，可根据需要分层级下载，适用于不同的面板数据。
    
    ## 使用说明
    
    - 在输入区中选择`起始年份`，`终止年份`会自动根据`起始年份`调整。
    - `需要输出的层级`中选择需要下载的层级，可选省级、地级或县级的任意组合，根据科研经验，本工具中的地级包括直辖市。
    - 如果需要匹配上级行政区划代码，则在`是否需要匹配上级区划代码`中选择`是`，如不需要，请选择`否`。注意如果仅选择`省级`，则`是否需要匹配上级区划代码`只能选择`否`。
    - 选择提交。若需要重新选择请选择`重置`或刷新页面。
    - 结果输出后请尽快下载，刷新页面将导致链接失效。统计得到的行政区划数量可与民政部历年统计资料比对。
    - `长面板`一般用于面板数据的匹配，`宽面板`为二维表格，核对查补更为直观。例如：''')

    # img = open('./resources/longwideform.png', 'rb').read()
    # put_image(img)
    put_collapse('查看长、宽面板示例', [
        put_tabs([
            {'title': '长面板（Long Form）示例', 'content': [
                put_table([
                    ['区划代码', '年份', '区划名称'],
                    [110000, 2014, '北京市'],
                    [110000, 2015, '北京市'],
                    [120000, 2014, '天津市'],
                    [120000, 2015, '天津市'],
                    ['……', '……', '……']
                ])
            ]},
            {'title': '宽面板（Wide Form）示例', 'content': [
                put_table([
                    ['区划代码', 2014, 2015],
                    [110000, '北京市', '北京市'],
                    [120000, '天津市', '天津市'],
                    ['……', '……', '……']
                ])
            ]}
        ])
    ])

    put_markdown(''' 
    ## 数据来源
    
    - 原始数据来自于`统计年鉴`公众号
    - 在此基础上对部分错误进行了调整，并将数据更新至2023年
    - [民政部历年行政区划代码](http://www.mca.gov.cn/article/sj/xzqh/1980/)  |  [民政部历年行政区划统计](http://xzqh.mca.gov.cn/statistics/)
    
    ## 源代码
    本程序的源代码：[Gitee](https://gitee.com/czhweb/qhlgpanel/blob/master/qhlgpanel.py)
    
    ''')

    put_collapse('查看Stata预处理命令',[
        put_markdown('''
            ```
            destring *代码 年份, replace
            local varlist "县级区划代码 年份 县级区划名称 县级区划类型 地级区划代码 地级区划名称 地级区划简称 省份代码 省级区划名称 省级区划简称"
            foreach var of local varlist{
                cap label var `var' `var'
            }

            cap rename 县级区划代码 xzqhdm_county
            cap rename 县级区划名称 xzqhmc_county
            cap rename 县级区划类型 xzqhlx_county
            cap rename 地级区划代码 xzqhdm_city
            cap rename 地级区划名称 xzqhmc_city
            cap rename 地级区划简称 xzqhjc_city
            cap rename 省份代码 xzqhdm_prov
            cap rename 省级区划名称 xzqhmc_prov
            cap rename 省级区划简称 xzqhjc_prov
            cap rename 年份 year

            compress
            ```
            ''')
    ])

    put_markdown('''
    ## 输入与结果区
    ''')

    styearlist = list(range(1980, 2024))
    info = input_group("输入相关信息", [
        select('*起始年份*', options= styearlist, name='styear', value = 1980, 
        onchange=lambda c: input_update('endyear', options=list(range(c, 2024)), value = c), required = True),
        select('*终止年份*', options = styearlist, name='endyear', required = True),
        select('*需要输出的层级*', options = ['省级', '地级', '县级'], name = 'cengji', value = ['省级', '地级', '县级'], required = True, multiple = True, onchange = lambda c: input_update('mergeyn', options = '否', value = '否') if c == ['省级'] else input_update('mergeyn', options = ['是', '否'], value = '是')),
        select('*是否需要匹配上级区划代码*', options = ['是', '否'], name = 'mergeyn', value = '是', required = True),
        actions('', [
        {'label': '提交', 'type': 'submit', 'value': 'submit'},
        {'label': '重置', 'type': 'reset', 'color': 'warning'}
        ], name='action', help_text='确认提交后会有一段处理时间，请耐心等待...'),
    ])

    delallexcel()
    styear, endyear, cengji, mergeyn = (info['styear'], info['endyear'], info['cengji'], info['mergeyn'])
    with put_loading(shape='border', color='primary'):
        sttime = time.time()
        put_markdown('> 正在读入原始文件，请稍后...你可以[点击此处](%s)下载原始文件' % excelfilepath)
        excelfile, yearlist = openexcelfile(styear, endyear)
        ckprovnum = pd.DataFrame()
        ckcitynum = pd.DataFrame()
        ckcountynum = pd.DataFrame()
        if '省级' in cengji:
            provcodewide, provcode = provgen(excelfile, yearlist)
            savename_prov_long_excel, content_prov_long_excel = save2es1(provcode, styear, endyear, '省级', mergeyn, '长', 'excel')
            savename_prov_long_stata, content_prov_long_stata = save2es1(provcode, styear, endyear, '省级', mergeyn, '长', 'stata')
            savename_prov_wide_excel, content_prov_wide_excel = save2es1(provcodewide, styear, endyear, '省级', mergeyn, '宽', 'excel')
            ckprovnum = checknum(provcode, '省级')
        if '地级' in cengji:
            citycodewide, citycode = citygen(excelfile, yearlist, mergeyn)
            savename_city_long_excel, content_city_long_excel = save2es1(citycode, styear, endyear, '地级', mergeyn, '长', 'excel')
            savename_city_long_stata, content_city_long_stata = save2es1(citycode, styear, endyear, '地级', mergeyn, '长', 'stata')
            savename_city_wide_excel, content_city_wide_excel = save2es1(citycodewide, styear, endyear, '地级', mergeyn, '宽', 'excel')
            ckcitynum = checknum(citycode, '地级')
        if '县级' in cengji:
            countycodewide, countycode = countygen(excelfile, yearlist, mergeyn)
            savename_county_long_excel, content_county_long_excel = save2es1(countycode, styear, endyear, '县级', mergeyn, '长',
                                                                         'excel')
            savename_county_long_stata, content_county_long_stata = save2es1(countycode, styear, endyear, '县级', mergeyn, '长',
                                                                         'stata')
            savename_county_wide_excel, content_county_wide_excel = save2es1(countycodewide, styear, endyear, '县级', mergeyn,
                                                                         '宽', 'excel')
            ckcountynum = checknum(countycode, '县级')
        put_markdown('> 处理完成')  
        put_table([
            ['输出层级', span('长面板（面板匹配使用）', col=2), '宽面板（统计核对使用）'],
            ['省级', put_file(savename_prov_long_excel + '.xlsx', content_prov_long_excel, 'Excel下载') if '省级' in cengji else '', put_file(savename_prov_long_stata + '.dta', content_prov_long_stata, 'Stata下载') if '省级' in cengji else '', put_file(savename_prov_wide_excel + '.xlsx', content_prov_wide_excel, 'Excel下载') if '省级' in cengji else ''],
            ['地级', put_file(savename_city_long_excel + '.xlsx', content_city_long_excel, 'Excel下载') if '地级' in cengji else '',
             put_file(savename_city_long_stata + '.dta', content_city_long_stata, 'Stata下载') if '地级' in cengji else '',
             put_file(savename_city_wide_excel + '.xlsx', content_city_wide_excel, 'Excel下载') if '地级' in cengji else ''],
            ['县级', put_file(savename_county_long_excel + '.xlsx', content_county_long_excel, 'Excel下载') if '县级' in cengji else '',
             put_file(savename_county_long_stata + '.dta', content_county_long_stata, 'Stata下载') if '县级' in cengji else '',
             put_file(savename_county_wide_excel + '.xlsx', content_county_wide_excel, 'Excel下载') if '县级' in cengji else '']
        ])
        df2table('行政区划数量验证',pd.concat([ckprovnum, ckcitynum, ckcountynum], axis = 1))
        put_markdown('> 处理完成，共用时%.2f秒！' % (time.time()-sttime))
        
def delallexcel():
    for file in os.listdir():
        if file.endswith('.xlsx') or file.endswith('.dta'):
            os.remove(file)


def df2table(name, data):
    '''用于dataframe转成可输出的table'''
    # table_datalist = data.columns.tolist()
    # table_header = data.values.tolist()
    # put_table(table_datalist, table_header) #Output table
    # put_scrollable(put_scope('scrollable'),horizon_scroll=True,height=200)
    put_collapse(name, [
        put_html(data.to_html(border=0))
    ], open=True)
    
    # res_table.reset()
    
# def save2es(data, styear, endyear, singlecj, mergeyn, lw):
#     cjtrans = {'省级': 'prov', '地级': 'city', '县级': 'county'}
#     mergetrans = {'是':'withupcode', '否': 'noupcode'}
#     saveexcelname = 'xzqh_%s_%s_%s_%s_%s.xlsx' %(str(styear), str(endyear), cjtrans[singlecj], mergetrans[mergeyn], str(round(time.time() * 1000)))
#     savestataname = 'xzqh_%s_%s_%s_%s_%s.dta' % (
#         str(styear), str(endyear), cjtrans[singlecj], mergetrans[mergeyn], str(round(time.time() * 1000)))
#     data.to_excel(saveexcelname, index = None)
#     data.to_stata(savestataname, write_index=False, version=119)
#     contente = open(saveexcelname, 'rb').read()
#     contents = open(savestataname, 'rb').read()
#     put_row([put_markdown('**%s区划%s面板导出：**' % (singlecj, lw)), put_file(saveexcelname, contente, 'Excel格式下载'), put_file(savestataname, contents, 'Stata格式下载')], size='22% 22% 22%')

def save2es1(data, styear, endyear, singlecj, mergeyn, lw, filetype):
    cjtrans = {'省级': 'prov', '地级': 'city', '县级': 'county'}
    mergetrans = {'是':'withupcode', '否': 'noupcode'}
    lwtrans = {'长': 'long', '宽': 'wide'}
    savename = 'xzqh_%s_%s_%s_%s_%s_%s' %(cjtrans[singlecj], str(styear), str(endyear), mergetrans[mergeyn], lwtrans[lw], str(round(time.time() * 1000)))
    if filetype == 'excel':
        data.to_excel(savename + '.xlsx', index=None)
        content = open(savename + '.xlsx', 'rb').read()
    elif filetype == 'stata':
        data.to_stata(savename + '.dta', write_index=False, version=119)
        content = open(savename + '.dta', 'rb').read()
    return savename, content

def provgen(excelfile, yearlist):
    provcode = excelfile.copy()
    provcode.columns = ['省级区划代码'] + yearlist
    provcode = provcode[~pd.isna(provcode['省级区划代码'])]
    provcode = provcode[provcode['省级区划代码'].apply(lambda x:(str(int(x))[-4:]=='0000'))]
    provcode = provcode.dropna(subset =  yearlist, how = 'all')
    provcode = provcode[provcode['省级区划代码'] <= 660000]
    provcodewide = provcode.copy()
    provcode = provcode.melt(id_vars=['省级区划代码'], value_name='省级区划名称' , var_name='年份').dropna(subset = ['省级区划名称'])
    provcode['省级区划代码'] = provcode['省级区划代码'].apply(lambda x:str(int(x)))
    provcode = provcode.reset_index(drop = True)
    provcode['省级区划简称'] = ''
    for i in range(len(provcode)):
        if provcode['省级区划名称'][i][-1:] == '省':
            provcode['省级区划简称'][i] = provcode['省级区划名称'][i][:-1]
        if provcode['省级区划名称'][i][-3:] == '自治区':
            if provcode['省级区划名称'][i] == '内蒙古自治区':
                provcode['省级区划简称'][i] = '内蒙古'
            else:
                provcode['省级区划简称'][i] = provcode['省级区划名称'][i][:2]
        if provcode['省级区划名称'][i][-1:] == '市':
            provcode['省级区划简称'][i] = provcode['省级区划名称'][i][:-1]
        if provcode['省级区划名称'][i][-2:] == '地区':
            provcode['省级区划简称'][i] = provcode['省级区划名称'][i][:-2]
    return provcodewide, provcode

def citygen(excelfile, yearlist, mergeyn):
    citycode = excelfile.copy()
    citycode.columns = ['地级区划代码'] + yearlist
    citycode = citycode[~pd.isna(citycode['地级区划代码'])]
    # 直辖市算城市
    zxscode = ['110000', '120000', '310000', '500000']
    citycode = citycode[citycode['地级区划代码'].apply(lambda x:(str(int(x))[-2:]=='00' and str(int(x))[-4:]!='0000') or (str(int(x)) in zxscode))]
    citycode = citycode.dropna(subset =  yearlist, how = 'all')
    citycode = citycode[citycode['地级区划代码'] <= 660000]
    citycodewide = citycode.copy()
    citycode = citycode.melt(id_vars=['地级区划代码'], value_name='地级区划名称' , var_name='年份').dropna(subset = ['地级区划名称'])
    citycode['地级区划代码'] = citycode['地级区划代码'].apply(lambda x:str(int(x)))
    citycode = citycode.reset_index(drop = True)
    citycode['地级区划简称'] = ''
    for i in range(len(citycode)):
        if citycode['地级区划名称'][i][-1:] == '市':
            citycode['地级区划简称'][i] = citycode['地级区划名称'][i][:-1]
        if citycode['地级区划名称'][i][-3:] == '自治州':
            citycode['地级区划简称'][i] = citycode['地级区划名称'][i][:-3]
        if citycode['地级区划名称'][i][-1:] == '盟':
            citycode['地级区划简称'][i] = citycode['地级区划名称'][i][:-1]
        if citycode['地级区划名称'][i][-2:] == '地区':
            citycode['地级区划简称'][i] = citycode['地级区划名称'][i][:-2]
    if mergeyn == '是':
        # 匹配省份代码
        cityprovcode = citycode.copy()
        provcode = provgen(excelfile, yearlist)[1]
        cityprovcode['省份代码'] = cityprovcode['地级区划代码'].apply(lambda x:str(int(x))[:2] + '0000')
        cityprovcode = pd.merge(cityprovcode, provcode, left_on = ['省份代码', '年份'], right_on = ['省级区划代码','年份']).drop(['省级区划代码'], axis = 1)
        return citycodewide, cityprovcode
    else:
        return citycodewide, citycode

def countygen(excelfile, yearlist, mergeyn):
    countycode = excelfile.copy()
    countycode.columns = ['县级区划代码'] + yearlist
    countycode = countycode[~pd.isna(countycode['县级区划代码'])]
    countycode = countycode[countycode['县级区划代码'].apply(lambda x:str(int(x))[-2:]!='00')]
    countycode = countycode.dropna(subset =  yearlist, how = 'all')
    countycodewide = countycode.copy()
    countycode = countycode.melt(id_vars=['县级区划代码'], value_name='县级区划名称' , var_name='年份').dropna(subset = ['县级区划名称'])
    countycode['县级区划代码'] = countycode['县级区划代码'].apply(lambda x:str(int(x)))
    countycode = countycode.reset_index(drop = True)
    # 区县名称容易重复,不放简称
    # 区分不同类型
    countycode['县级区划类型'] = ''
    linqu = ['神农架林区']
    for i in range(len(countycode)):
        if countycode['县级区划名称'][i][-1:] == '区':
            if countycode['县级区划名称'][i] in linqu:
                countycode['县级区划类型'][i] = '林区'
            elif countycode['县级区划名称'][i][-2:] == '特区':
                countycode['县级区划类型'][i] = '特区'
            else:
                countycode['县级区划类型'][i] = '市辖区'
        if countycode['县级区划名称'][i][-1:] == '市':
            countycode['县级区划类型'][i] = '县级市'
        if countycode['县级区划名称'][i][-1:] == '县':
            if countycode['县级区划名称'][i][-3:] == '自治县':
                countycode['县级区划类型'][i] = '自治县'
            else:
                countycode['县级区划类型'][i] = '县'
        if countycode['县级区划名称'][i][-1:] == '旗':
            if countycode['县级区划名称'][i][-3:] == '自治旗':
                countycode['县级区划类型'][i] = '自治旗'
            else:
                countycode['县级区划类型'][i] = '旗'    
    if mergeyn == '是':
        # 匹配地级代码
        countycityprovcode = countycode.copy()
        zxscode = ['110000', '120000', '310000', '500000']
        countycityprovcode['地级区划代码'] = countycityprovcode['县级区划代码'].apply(lambda x:str(int(x))[:4] + '00' if not (str(int(x))[:2] + '0000') in zxscode else str(int(x))[:2] + '0000')
        citycode = citygen(excelfile, yearlist, '否')[1]
        # 有可能是直辖县,所以一定要用left,否则会遗漏
        countycityprovcode = pd.merge(countycityprovcode, citycode, on = ['地级区划代码', '年份'], how = 'left')
        countycityprovcode['地级区划代码'][pd.isnull(countycityprovcode['地级区划名称'])] = np.nan
        countycityprovcode['省份代码'] = countycityprovcode['县级区划代码'].apply(lambda x:str(int(x))[:2] + '0000')
        provcode = provgen(excelfile, yearlist)[1]
        countycityprovcode = pd.merge(countycityprovcode, provcode, left_on = ['省份代码', '年份'], right_on = ['省级区划代码','年份']).drop(['省级区划代码'], axis = 1)
        return countycodewide, countycityprovcode
    else:
        return countycodewide, countycode

def checknum(data, singlecj):
    '''验证省级、地级、县级个数'''
    item = '%s区划数量' % singlecj
    cknum = pd.DataFrame(data.groupby(['年份']).size(),columns= [item])
    return cknum


def checkcitynum(citycode):
    '''验证地级个数'''
    citycode['省份代码'] = citycode['地级区划代码'].apply(lambda x:str(int(x))[:2])
    ckcitynum = pd.DataFrame(citycode.groupby(['年份']).size(),columns= ['地级区划数量'])
    return ckcitynum



def openexcelfile(styear, endyear):
    yearlist = [''.join(str(x)) for x in range(styear, endyear+1)]
    excelfile = pd.read_excel(excelfilepath, usecols= ['行政区划代码'] + yearlist)
    return excelfile, yearlist


if __name__ == '__main__':
    excelfilepath = './resources/县级行政区划1980-2023.xlsx'
    start_server(main, debug=True, port=9015)