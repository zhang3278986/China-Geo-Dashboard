# 🗺️ 多层次地图可视化
(China Geo-Data Interactive Dashboard)

这是一个基于 **Streamlit** 和原生 **ECharts** 引擎打造的极速交互式地理数据可视化工具。专门为需要将多层级地理数据（省级底色、市级气泡、精确散点、胡焕庸线）进行融合展示的研究人员和数据分析师设计。

## ✨ 核心特性

- ⚡ **极速渲染**：彻底抛弃笨重的 Python 封装库，直接注入原生 ECharts JS 引擎，实现 0 毫秒级丝滑交互。
- 🎛️ **全参数可视化配置**：提供网页侧边栏面板，支持实时调节气泡大小、图层颜色、颜色步长和边界线粗细。
- 🧠 **智能地名解析**：内置国家标准行政区划字典，自动纠错并补全“省/市/自治区”后缀，完美匹配 GeoJSON。
- 📥 **一键高质量导出**：支持一键下载 PNG 或无损 SVG 矢量图，满足学术论文排版需求。

## 🚀 快速开始

### 1. 本地运行

确保你的电脑已安装 Python，然后在终端运行以下命令：

```bash
# 克隆仓库
git clone [https://github.com/你的用户名/你的仓库名.git](https://github.com/你的用户名/你的仓库名.git)
cd 你的仓库名

# 安装依赖
pip install -r requirements.txt

# 启动应用
streamlit run app.py
