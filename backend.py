import os
from importlib.machinery import SourceFileLoader
from types import ModuleType


try:
    # Funciona melhor em ambiente empacotado (PyInstaller).
    import main as _backend
except Exception:
    _module_path = os.path.join(os.path.dirname(__file__), 'main.py')
    if not os.path.isfile(_module_path):
        raise FileNotFoundError(f'Backend nao encontrado: {_module_path}')

    _loader = SourceFileLoader('yt_tools_backend', _module_path)
    _backend = ModuleType(_loader.name)
    _loader.exec_module(_backend)


validar_url = _backend.validar_url
validar_pasta = _backend.validar_pasta
info_video = _backend.info_video
salvar_thumbnail = _backend.salvar_thumbnail
baixar_video = _backend.baixar_video
baixar_audio = _backend.baixar_audio
baixar_playlist_video = _backend.baixar_playlist_video
baixar_playlist_audio = _backend.baixar_playlist_audio
