# flask_app.spec
import sys
from pathlib import Path

block_cipher = None

# 项目根目录
root_path = Path(__name__).parent

def get_all_routes_modules():
    # 项目根目录（假设 .spec 文件在项目根目录）
    root = Path(__name__).parent
    # apps 目录路径
    apps_dir = root / "apps"
    # 存储所有 routes 模块的列表
    routes_modules = []

    # 遍历 apps 目录下的所有子目录
    for subdir in apps_dir.iterdir():
        if subdir.is_dir():  # 只处理目录
            # 检查是否存在 routes.py
            routes_file = subdir / "routes.py"
            if routes_file.exists():
                # 生成模块名（如 apps.authentication.routes）
                module_name = f"apps.{subdir.name}.routes"
                routes_modules.append(module_name)
    return routes_modules

# 调用函数获取所有 routes 模块
all_routes = get_all_routes_modules()

a = Analysis(
    ['run.py'],  # 入口文件
    pathex=[str(root_path)],
    binaries=[],
    datas=[
        # 包含静态文件和模板（源路径: 打包后路径）
        (str(root_path / "templates"), "templates"),
        (str(root_path / "static"), "static"),
        (str(root_path / "docs"), "docs"),
    ],
    hiddenimports=[
        # 显式声明Flask相关隐式依赖
        "flask_migrate",
        "flask_sqlalchemy",
        "flask_login",
        "markdown.extensions.extra",
        "markdown.extensions.codehilite",
        "markdown.extensions.mdx_math",
        "celery.fixups",
        "celery.fixups.flask",
        "celery.fixups.django",
        *all_routes,
        # 根据项目实际依赖补充
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="Betterer",  # EXE文件名
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,  # 压缩EXE
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # 显示控制台（调试用，发布时可改为False）
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon="static\\assets\\images\\favicon.ico",
)