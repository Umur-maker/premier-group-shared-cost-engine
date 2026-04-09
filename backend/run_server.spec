# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec for Premier Cost Engine backend

import os

block_cipher = None
backend_root = os.path.dirname(SPECPATH) if 'SPECPATH' not in dir() else '.'

a = Analysis(
    ['run_server.py'],
    pathex=[os.path.dirname(backend_root)],
    binaries=[],
    datas=[
        ('core/logo.png', 'backend/core'),
        ('data-seed/companies.json', 'backend/data-seed'),
        ('data-seed/settings.json', 'backend/data-seed'),
    ],
    hiddenimports=[
        'uvicorn',
        'uvicorn.logging',
        'uvicorn.loops',
        'uvicorn.loops.auto',
        'uvicorn.protocols',
        'uvicorn.protocols.http',
        'uvicorn.protocols.http.auto',
        'uvicorn.protocols.websockets',
        'uvicorn.protocols.websockets.auto',
        'uvicorn.lifespan',
        'uvicorn.lifespan.on',
        'uvicorn.lifespan.off',
        'backend',
        'backend.main',
        'backend.api',
        'backend.api.companies',
        'backend.api.settings',
        'backend.api.calculate',
        'backend.api.history',
        'backend.api.payments',
        'backend.core',
        'backend.core.config',
        'backend.core.engine',
        'backend.core.data_manager',
        'backend.core.history',
        'backend.core.payments',
        'backend.core.translations',
        'backend.core.excel_export',
        'backend.core.statement_export',
        'backend.core.statement_pdf',
        'backend.core.agreement_pdf',
        'backend.core.safe_filename',
        'reportlab',
        'reportlab.lib',
        'reportlab.lib.pagesizes',
        'reportlab.lib.units',
        'reportlab.lib.colors',
        'reportlab.lib.utils',
        'reportlab.lib.enums',
        'reportlab.lib.styles',
        'reportlab.platypus',
        'reportlab.pdfbase',
        'reportlab.pdfbase._fontdata',
        'reportlab.graphics',
        'openpyxl',
        'openpyxl.styles',
        'openpyxl.utils',
        'pydantic',
        'starlette',
        'starlette.background',
        'anyio',
        'anyio._backends',
        'anyio._backends._asyncio',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='run_server',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    icon=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='run_server',
)
