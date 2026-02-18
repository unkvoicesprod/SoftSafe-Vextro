# SoftSafe Downloader

Downloader de videos, audios e playlists do YouTube com interface grafica (Tkinter), tema claro/escuro, splash screen e empacotamento para Windows.

## Sobre

O **SoftSafe Downloader** usa `yt-dlp` para baixar conteudo do YouTube e oferece uma interface simples para:

- Baixar **video** (com selecao de qualidade/formato)
- Baixar **audio** (com conversao para MP3/M4A)
- Baixar **playlist de videos**
- Baixar **playlist de audios**
- Salvar thumbnail
- Acompanhar progresso em tempo real

## Funcionalidades

- Interface grafica em Python (`tkinter`)
- Splash screen de inicializacao
- Alternancia de tema `Light/Dark`
- Barra de progresso + log em tempo real
- Botao de logs com opcoes:
  - Abrir arquivo de log
  - Limpar log
- Atalho para pasta de download ao concluir
- Link de apoio no header
- Build `.exe` para Windows com metadados de versao

## Estrutura do projeto

- `main.py`: funcoes principais de download (`yt-dlp`, `requests`)
- `gui.py`: interface principal
- `splash.py`: tela de splash
- `backend.py`: ponte/import do backend para GUI
- `ico.png` / `ico.ico`: icones do app
- `version_info.txt`: metadados de versao para build
- `SoftSafe Downloader.spec`: configuracao PyInstaller

## Requisitos (modo Python)

- Python 3.10+
- `yt-dlp`
- `requests`

Instalacao:

```bash
pip install yt-dlp requests
```

## Executar em desenvolvimento

```bash
python main.py
```

## Build para Windows (.exe)

Exemplo de build com PyInstaller:

```bash
python -m PyInstaller --noconfirm --clean --onefile --windowed \
  --name "SoftSafe Downloader" \
  --icon "ico.ico" \
  --version-file "version_info.txt" \
  --add-data "ico.png;." \
  --add-binary "ffmpeg.exe;." \
  main.py
```

Saida:

- `dist/SoftSafe Downloader.exe`

## Observacoes importantes

- Para conversao de audio (ex.: MP3), o projeto usa **FFmpeg**.
- Neste repositorio, o build foi configurado para incluir `ffmpeg.exe` no executavel.
- Se o icone nao atualizar no Windows Explorer, limpe o cache de icones ou gere com nome novo de arquivo.

## Metadados atuais do executavel

- ProductName: `SoftSafe Downloader`
- FileDescription: `Dev Francisco Armando Chico`
- ProductVersion: `1.1.1`
- FileVersion: `1.1.1`
- CompanyName: `SoftSafe`
- Copyright: `Copyright (c) 2026 SoftSafe`

## Autor

**Francisco Armando Chico**  
Empresa: **SoftSafe**  
Ano: **2026**

## Aviso legal

Este projeto destina-se a uso educacional/pessoal. O usuario e responsavel por respeitar os Termos de Uso das plataformas e direitos autorais aplicaveis.
