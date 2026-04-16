# GitHub 上传前检查清单

## 1. 先确认要公开什么

- 公开的是**软件原型与展示材料**
- 不公开学校平台账号信息、个人隐私信息和非必要大体积安装包
- 不把本仓库表述成已经完成全部项目成果

## 2. 提交前建议保留的内容

- `app/`：软件主代码
- `scripts/`：演示数据、截图、展示资产生成脚本
- `README.md`：图文首页说明
- `pyproject.toml`：运行入口与依赖说明
- `artifacts/demo_case.json`
- `artifacts/demo_workflow_summary.json`
- `artifacts/demo_workflow_summary.md`
- `artifacts/walkthrough/`
- `artifacts/showcase/`

## 3. 提交前建议不要公开的内容

- `release/`：打包产物体积较大，且不利于仓库简洁
- `dist/`：构建产物
- 本地数据库文件
- 用户本机生成的 `generated_docs/` 与 `generated_exports/` 临时结果
- 仅供本地使用的安装包、便携版和压缩包

## 4. 文案口径要保持一致

- 软件名称统一为：`砂型铸造工艺图—工艺卡—仿真校核辅助工作站`
- 项目主线统一为：`砂型铸造工艺图与工艺卡的一体化建模及仿真辅助优化`
- 演示案例统一为：`圆盖铝合金件一体化阶段演示`

## 5. 上传前最后自查

- README 首页截图是否为最新版本
- README 中的图片路径是否可正常显示
- `.gitignore` 是否已生效
- 是否误包含个人目录、绝对路径截图或敏感文件
- 演示索引文件是否仍指向圆盖案例

## 6. 推荐上传顺序

1. 先上传代码与 README
2. 再上传 `artifacts/showcase/` 与 `artifacts/walkthrough/`
3. 最后补充阶段成果说明或发布说明
