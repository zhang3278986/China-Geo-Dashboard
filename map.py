import streamlit as st
import pandas as pd
import json
import streamlit.components.v1 as components

# ==========================================
# 1. 页面配置与 CSS 样式注入 (自定义侧边栏宽度)
# ==========================================
st.set_page_config(page_title="中国地理数据工作站", layout="wide")

st.markdown(
    """
    <style>
    /* 强制调整侧边栏宽度 */
    section[data-testid="stSidebar"] {
        width: 420px !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.title("⚙️ 可视化配置面板")
    
    # --- 标题与导出设置 ---
    st.subheader("📝 标题设置")
    map_title = st.text_input("地图主标题", value="分省份分城市样本分布图")
    map_subtitle = st.text_input("地图副标题", value="胡焕庸线两侧样本空间分布研究")
    
    st.divider()
    st.subheader("📁 数据导入")
    file_prov = st.file_uploader("1. 省级统计 (名称, 数值)", type=["xlsx"])
    file_city = st.file_uploader("2. 市级气泡 (名称, 数值, 经纬度)", type=["xlsx"])
    file_sample = st.file_uploader("3. 详细样本 (地址, 经纬度)", type=["xlsx"])

    st.divider()
    st.subheader("🛠️ 图层开关")
    lay1, lay2 = st.columns(2)
    with lay1:
        show_prov = st.checkbox("省级着色", value=True)
        show_sample = st.checkbox("样本散点", value=False)
    with lay2:
        show_city = st.checkbox("市级气泡", value=True)
        show_hu = st.checkbox("胡焕庸线", value=True)
    
    st.divider()
    st.subheader("🎨 视觉效果微调")
    # 颜色选择器横向排列
    color_cols = st.columns(3)
    with color_cols[0]:
        bubble_color = st.color_picker("气泡颜色", "#D94E5D")
    with color_cols[1]:
        sample_color = st.color_picker("散点颜色", "#FBD04D")
    with color_cols[2]:
        hu_line_color = st.color_picker("分界线色", "#3E613C")
    
    # 步长节点
    custom_bins_str = st.text_input("省级颜色分段节点", value="0, 50, 150, 300, 500, 850")
    
    # 细节参数调节
    st.write("📐 元素尺寸与细节")
    s1, s2 = st.columns(2)
    with s1:
        bubble_min = st.number_input("气泡最小半径", value=5)
        bubble_scale = st.slider("气泡放大倍率", 5.0, 30.0, 10.0) # 越小气泡越大
        border_width = st.slider("边界线粗细", 0.1, 3.0, 1.0)
    with s2:
        bubble_max = st.number_input("气泡最大半径", value=80)
        label_font_size = st.slider("省名文字大小", 8, 20, 10)
        border_color = st.color_picker("边界线颜色", "#FFFFFF")
        
    show_labels = st.checkbox("显示省份名称", value=False)
    
    st.divider()
    render_mode = st.radio("导出模式 (渲染引擎)", ["PNG (Canvas)", "SVG (矢量图)"], horizontal=True)
    renderer = "canvas" if "PNG" in render_mode else "svg"

# ==========================================
# 2. 数据标准化处理
# ==========================================
STANDARD_PROVINCES = [
    "北京市", "天津市", "河北省", "山西省", "内蒙古自治区", "辽宁省", "吉林省", 
    "黑龙江省", "上海市", "江苏省", "浙江省", "安徽省", "福建省", "江西省", 
    "山东省", "河南省", "湖北省", "湖南省", "广东省", "广西壮族自治区", 
    "海南省", "重庆市", "四川省", "贵州省", "云南省", "西藏自治区", "陕西省", 
    "甘肃省", "青海省", "宁夏回族自治区", "新疆维吾尔自治区", "台湾省", 
    "香港特别行政区", "澳门特别行政区"
]

def get_std_name(name):
    if not isinstance(name, str): return str(name)
    name = name.strip()
    if name in STANDARD_PROVINCES: return name
    for std in STANDARD_PROVINCES:
        clean_std = std.replace("省","").replace("市","").replace("自治区","").replace("维吾尔","").replace("壮族","").replace("回族","").replace("特别行政区","")
        clean_in = name.replace("省","").replace("市","").replace("自治区","").replace("维吾尔","").replace("壮族","").replace("回族","").replace("特别行政区","")
        if clean_in == clean_std or clean_in in std: return std
    return name

p_data, c_data, s_data = [], [], []

if file_prov:
    df_p = pd.read_excel(file_prov)
    for _, row in df_p.iterrows():
        p_data.append({"name": get_std_name(str(row.iloc[0])), "value": int(pd.to_numeric(row.iloc[-1], errors='coerce') or 0)})

if file_city:
    df_c = pd.read_excel(file_city)
    offset = 1 if df_c.shape[1] >= 5 else 0
    for _, row in df_c.iterrows():
        try:
            c_data.append({"name": str(row.iloc[offset]), "value": [float(row.iloc[offset+2]), float(row.iloc[offset+3]), int(row.iloc[offset+1])]})
        except: continue

if file_sample:
    df_s = pd.read_excel(file_sample)
    for _, row in df_s.iterrows():
        try:
            s_data.append({"name": str(row.iloc[0]), "value": [float(row.iloc[1]), float(row.iloc[2])]})
        except: continue

# 动态步长解析
try:
    bins = sorted([int(x.strip()) for x in custom_bins_str.split(',') if x.strip().isdigit()])
    dynamic_pieces = []
    if bins:
        dynamic_pieces.append({"min": bins[-1], "label": f">{bins[-1]}"})
        for i in range(len(bins)-1, 0, -1):
            if bins[i-1] == 0:
                dynamic_pieces.append({"min": 1, "max": bins[i], "label": f"1-{bins[i]}"})
            else:
                dynamic_pieces.append({"min": bins[i-1], "max": bins[i], "label": f"{bins[i-1]}-{bins[i]}"})
    dynamic_pieces.append({"value": 0, "label": "无数据", "color": "#eeeeee"})
except:
    dynamic_pieces = [{"min": 1, "label": "有数据"}]

# ==========================================
# 3. 核心：构建原生 HTML/ECharts 模板
# ==========================================
html_template = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script src="https://cdn.jsdelivr.net/npm/echarts@5.4.3/dist/echarts.min.js"></script>
</head>
<body style="margin: 0; padding: 0; background-color: #ffffff;">
    <div id="main" style="width: 100%; height: 880px;"></div>
    <script>
        var chart = echarts.init(document.getElementById('main'), null, {{ renderer: '{renderer}' }});
        
        fetch('https://geo.datav.aliyun.com/areas_v3/bound/100000_full.json')
            .then(res => res.json())
            .then(geoJson => {{
                echarts.registerMap('china', geoJson);
                
                var option = {{
                    backgroundColor: '#ffffff',
                    title: {{
                        text: '{map_title}',
                        subtext: '{map_subtitle}',
                        left: 'center',
                        top: 20,
                        textStyle: {{ fontSize: 24, fontWeight: 'bold' }}
                    }},
                    toolbox: {{
                        show: true,
                        left: 'right',
                        top: 'center',
                        feature: {{
                            saveAsImage: {{ show: true, type: '{renderer}', name: '地图可视化成果' }}
                        }}
                    }},
                    tooltip: {{ trigger: 'item' }},
                    visualMap: {{
                        type: 'piecewise',
                        left: '5%',
                        bottom: '5%',
                        seriesIndex: 0,
                        inRange: {{ color: ['#ffeda0', '#feb24c', '#f03b20', '#bd0026'] }},
                        pieces: {json.dumps(dynamic_pieces)}
                    }},
                    geo: {{
                        map: 'china',
                        roam: true,
                        label: {{
                            show: {str(show_labels).lower()},
                            color: '#333',
                            fontSize: {label_font_size}
                        }},
                        itemStyle: {{
                            areaColor: '#f4f4f4',
                            borderColor: '{border_color}',
                            borderWidth: {border_width}
                        }}
                    }},
                    series: [
                        // 图层 0: 省级着色
                        {{
                            name: '省级着色',
                            type: 'map',
                            geoIndex: 0,
                            data: {json.dumps(p_data) if show_prov else "[]"},
                            label: {{ show: {str(show_labels).lower()}, fontSize: {label_font_size} }}
                        }},
                        // 图层 1: 市级气泡
                        {{
                            name: '市级气泡',
                            type: 'scatter',
                            coordinateSystem: 'geo',
                            itemStyle: {{ color: '{bubble_color}', opacity: 0.8, borderColor: '#fff', borderWidth: 1 }},
                            symbolSize: function(val) {{
                                return {str(show_city).lower()} ? Math.min({bubble_max}, Math.max({bubble_min}, val[2] / {bubble_scale})) : 0;
                            }},
                            data: {json.dumps(c_data) if show_city else "[]"}
                        }},
                        // 图层 2: 精细样本点
                        {{
                            name: '精确点位',
                            type: 'scatter',
                            coordinateSystem: 'geo',
                            symbolSize: {4 if show_sample else 0},
                            itemStyle: {{ color: '{sample_color}' }},
                            data: {json.dumps(s_data) if show_sample else "[]"}
                        }},
                        // 图层 3: 胡焕庸线
                        {{
                            name: '分界线',
                            type: 'lines',
                            coordinateSystem: 'geo',
                            lineStyle: {{ type: 'dashed', color: '{hu_line_color}', width: 2, opacity: {1 if show_hu else 0} }},
                            data: {json.dumps([{"coords": [[127.52, 50.22], [98.50, 25.01]]}]) if show_hu else "[]"}
                        }},
                        // 图层 4: 端点
                        {{
                            name: '端点',
                            type: 'scatter',
                            coordinateSystem: 'geo',
                            data: {json.dumps([
                                {"name": "黑河", "value": [127.52, 50.22]},
                                {"name": "腾冲", "value": [98.50, 25.01], "label": {"position": "left", "offset": [-10, 0]}}
                            ]) if show_hu else "[]"},
                            symbolSize: {10 if show_hu else 0},
                            itemStyle: {{ color: '{hu_line_color}', borderColor: '#fff', borderWidth: 2 }},
                            label: {{
                                show: true,
                                formatter: '{{b}}',
                                position: 'right',
                                color: '#111',
                                fontWeight: 'bold',
                                fontSize: 14
                            }}
                        }}
                    ]
                }};
                chart.setOption(option);
                window.addEventListener('resize', () => chart.resize());
            }});
    </script>
</body>
</html>
"""

# ==========================================
# 4. 最终渲染
# ==========================================
components.html(html_template, height=900)