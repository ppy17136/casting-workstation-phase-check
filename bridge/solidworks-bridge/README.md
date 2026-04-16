# SolidWorksBridge

该目录是 `SolidWorks` 薄桥接程序的 `C#/.NET 8` 工程。

当前能力：

- `ping`
- `info`
- `export` 命令行骨架

当前状态：

- 已完成工程骨架与命令协议
- `export` 的真实 COM 导图逻辑尚未实现

## 构建

需要本机安装 `.NET SDK 8.0`。

```powershell
cd E:\zhuzaochuangxin\casting_workstation\bridge\solidworks-bridge
dotnet build
```

## 命令

```powershell
SolidWorksBridge.exe ping
SolidWorksBridge.exe info
SolidWorksBridge.exe export --input demo.sldprt --output out.step --format step
```
