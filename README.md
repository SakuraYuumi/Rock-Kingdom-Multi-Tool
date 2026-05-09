# 洛克王国多功能辅助工具

这个项目是洛克王国世界本地辅助工具，包含互动资源地图、跑图导航、孵蛋查询和 PVP 伤害计算等功能。

## 数据源

- 页面：<https://wiki.biligame.com/rocom/大地图>
- 分类索引：<https://wiki.biligame.com/rocom/Data:Mapnew/type/json?action=raw>
- 点位接口：`https://wiki.biligame.com/rocom/Data:Mapnew/type/{markType}/json?action=raw`

## 抓取命令

```powershell
py -3 scripts/fetch_wiki_resources.py
```

默认抓取 Wiki 分类里的：

- `地点`
- `互动事件`
- `宝箱`
- `任务`
- `战斗`
- `精灵分布`
- `采集`
- `收集`

如需抓取全部大地图点位分类：

```powershell
py -3 scripts/fetch_wiki_resources.py --include-all-groups
```

## 输出文件

- `data/wiki_map_categories.json`：Wiki 大地图分类索引
- `data/wiki_resource_points.json`：默认资源点位合集
- `data/wiki_resource_points_by_type.json`：按 `markType` 分组的点位
- `data/wiki_resource_points.csv`：CSV 版点位
- `data/wiki_gathering_points.json`：仅 `采集` 类
- `data/wiki_collection_points.json`：仅 `收集` 类
- `data/wiki_resource_summary.json`：数量汇总

## Wiki 底图

Wiki 大地图使用 Leaflet 瓦片底图，不是一张静态整图。主地上层配置来自：

- `https://wiki.biligame.com/rocom/Widget:Map4/main?action=raw`
- `https://wiki.biligame.com/rocom/Widget:Map4.1/mapc?action=raw`

抓取并拼接主地上层底图：

```powershell
py -3 scripts/fetch_wiki_basemap.py
```

默认输出：

- `assets/wiki_tiles/G/z5/`：原始 Wiki 瓦片
- `assets/maps/wiki_G_z5.png`：拼接后的 Wiki 地上层底图
- `data/wiki_basemap_metadata.json`：底图来源、瓦片范围、坐标换算参数

把资源坐标投影到 Wiki 底图像素：

```powershell
py -3 scripts/project_resources_to_wiki_basemap.py
```

输出：

- `data/wiki_resource_points_pixels.json`
- `dev_artifacts/resource_previews/wiki_G_z5_resources_preview.png`

生成更高清的 z=6 版底图和资源预览：

```powershell
py -3 scripts/fetch_wiki_basemap.py --zoom 6 --scan-min-x -6 --scan-max-x 5 --scan-min-y -6 --scan-max-y 5 --workers 24 --preserve-scan-bounds --metadata-output data/wiki_basemap_metadata_z6.json
py -3 scripts/project_resources_to_wiki_basemap.py --metadata data/wiki_basemap_metadata_z6.json --output data/wiki_resource_points_pixels_z6.json --preview dev_artifacts/resource_previews/wiki_G_z6_resources_preview.png --icon-width 40
```

高清输出：

- `assets/maps/wiki_G_z6.png`：3072x3072 Wiki 地上层底图
- `dev_artifacts/resource_previews/wiki_G_z6_resources_preview.png`：3072x3072 资源标记预览
- `data/wiki_basemap_metadata_z6.json`：z=6 底图坐标换算参数
- `data/wiki_resource_points_pixels_z6.json`：z=6 资源像素坐标

## Wiki 标记图标

下载当前点位数据实际用到的 Wiki 标记图标：

```powershell
py -3 scripts/fetch_wiki_icons.py
```

输出：

- `assets/icons/wiki/`：本地资源标记图
- `data/wiki_resource_icons.json`：`markType` 到图标文件的映射

`project_resources_to_wiki_basemap.py` 会自动读取 `data/wiki_resource_icons.json`，用图标替换预览图里的圆点。默认绘制宽度是 24px，可用 `--icon-width` 调整。

## 本地程序

打开项目根目录里的 `洛克王国多功能辅助工具.pyw` 即可运行本地程序。

也可以用命令启动：

```powershell
py -3 洛克王国多功能辅助工具.pyw
```

程序功能：

- 顶部账号栏可新增、切换、改名账号
- 左侧按资源类型选择显示内容
- 鼠标拖拽移动地图
- 鼠标滚轮按当前位置缩放地图
- 点击资源图标变暗淡，再次点击恢复
- 每个账号独立保存暗淡/已采集状态、路线进度和点位备注
- 顶部工具条提供缩小、放大、100%、适合窗口、恢复全部

程序文件：

- `洛克王国多功能辅助工具.pyw`：双击启动入口
- `app/roco_resource_map_qt.py`：程序主体
- `app/sift_tracker_v2.py`：小地图跟随与导航定位
- `data/wiki_resource_points_pixels_z7.json`：资源像素坐标
- `assets/maps/wiki_G_z7.png`：高清 Wiki 地上层底图
- `assets/maps/wiki_B1_z7.png`、`assets/maps/wiki_B2_z7.png`：地底 B1/B2 底图
- `assets/icons/wiki/`：资源图标
- `data/user_accounts.json`：账号列表与当前账号
- `data/accounts/<账号ID>/`：每个账号自己的采集状态、路线进度和备注

检查资源是否齐全：

```powershell
py -3 app/roco_resource_map_qt.py --check
```

检查程序交互逻辑：

```powershell
py -3 洛克王国多功能辅助工具.pyw --selftest
```

## 开发归档

不是日常运行必需、但对后续校准和回溯有用的文件统一放在 `dev_artifacts/`，目录说明见 `dev_artifacts/README.md`。

## 坐标说明

点位里的 `lat` 和 `lng` 是 Wiki 大地图接口字段名，不是现实地理经纬度。使用 Wiki 底图时，当前 z=5 拼接图的像素换算记录在 `data/wiki_basemap_metadata.json`。
