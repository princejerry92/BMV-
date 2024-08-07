# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['run_app.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('templates', 'templates'),
        ('static', 'static'),
        ('metricschart.py', '.'),
        ('telmsg.py', '.'),
        ('emitterGUI.py', '.'),
    ],
    hiddenimports=[
        'engineio.async_drivers.threading',
        'engineio.async_drivers.gevent',
        'flask_socketio',
        'socketio',
        'gevent.monkey',
        'gunicorn',
        'gunicorn.glogging',
        'gunicorn.workers.ggevent',
        'MetaTrader5',
        'gevent',
        'gevent.queue',
        'psutil',
        'engineio', 
        'engineio.async_threading', 
        'engineio.async_sockets', 
        'engineio.packet', 
        'engineio.payload', 
        'engineio.socket', 
        'engineio.namespace', 
        'engineio.async_namespace', 
        'engineio.client', 
        'engineio.server', 
        'engineio.exceptions', 
        'engineio.payload.Payload', 
        'engineio.packet.Packet',
        'engineio.async_drivers.eventlet', 
        'eventlet.hubs.epolls', 
        'eventlet.hubs.kqueue', 
        'eventlet.hubs.selects', 
        'dns', 
        'dns.asyncbackend', 
        'dns.asyncquery', 
        'dns.asyncresolver', 
        'dns.e164', 
        'dns.namedict', 
        'dns.tsigkeyring', 
        'dns.versioned'
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
    name='BMVemitter',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=r'C:\BMV Emitter\venv\businessman.ico',
    onefile=True  # This is the key change for one-file mode
)
