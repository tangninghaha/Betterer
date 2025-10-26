# Betterer - 基于 Flask Datta Able 的题目管理系统

一款专为学生设计的高效题目组织与管理工具，基于开源项目[Flask Datta Able](https://app-generator.dev/product/datta-able/flask/)构建，支持题目分类、难度标记、Markdown格式记录及个人笔记管理，帮助学生系统化梳理学习内容。

本项目大部分代码由 AI 编写。


## 项目简介

本系统基于 Bootstrap 5 框架和 Flask 后端，提供简洁直观的界面，专注于题目管理的核心需求：
- 支持录入题目描述、难度分级、设置标签、树状分类
- 内置 Markdown 编辑器，支持数学公式渲染
- 可添加个人注释、解法思路，形成个性化学习档案
- 响应式设计，适配桌面与移动设备


## 核心功能

| 功能                | 说明                                  |
|---------------------|---------------------------------------|
| 题目管理            | 新增、编辑、删除题目    |
| 分类体系            | 按标签（如"数组"、"动态规划"）和难度（1-5级）分类，支持树状分类 |
| Markdown支持        | 题目内容、解法均支持Markdown格式，含代码高亮、数学公式 |
| 个人笔记            | 针对每个题目添加私有注释，记录学习心得 |
| 文字提取            | 上传图片并识别图片文字 |

## 计划中的功能

见 [愿望清单](./todo.md)

## 快速开始

### 环境要求

- Python（推荐开发者版本号 3.13.7）
- 使用 Windows 开发，不确保其它系统兼容性


### 本地安装（手动）
1. 克隆仓库

   ```bash
   git clone https://github.com/tangninghaha/Betterer.git
   cd Betterer
   ```

2. 安装依赖

   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

3. 运行程序

   ```bash
   python .\\run.py
   ```

## 许可证说明

本项目基于[MIT许可证](LICENSE.md)构建，原始代码版权归 AppSeed 所有。使用时需遵守以下条款：

- 允许用于个人学习、教育项目或商业产品
- 允许修改、扩展代码，但**不得移除源代码中的版权声明**（如文件头部的`Copyright (c) 2019 - present AppSeed.us`）
- 禁止将本项目的UI元素、模板单独出售，或用于创建可售卖的HTML/CSS模板、CMS主题
- 分发衍生作品时，需包含原始许可证文件


## 致谢

- 基于[Flask Datta Able](https://app-generator.dev/product/datta-able/flask/)开源框架开发
- 设计依赖[Datta Able Dashboard](https://app-generator.dev/docs/templates/bootstrap/datta-able.html)（Bootstrap 5）