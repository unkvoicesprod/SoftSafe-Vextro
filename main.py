import os
import re
import sys

import requests
import yt_dlp
from yt_dlp.utils import DownloadError


def sanitizar_nome_arquivo(nome):
    nome = re.sub(r'[\\/*?:"<>|]', '', nome)
    return nome.strip()


def validar_pasta(caminho):
    return bool(caminho) and os.path.isdir(caminho)


def validar_url(url):
    return bool(url) and ('youtube.com' in url or 'youtu.be' in url)


def obter_ffmpeg_location():
    base_dir = getattr(sys, '_MEIPASS', os.path.dirname(__file__))
    ffmpeg_bundled = os.path.join(base_dir, 'ffmpeg.exe')
    if os.path.isfile(ffmpeg_bundled):
        return ffmpeg_bundled

    ffmpeg_local = os.path.join(os.path.dirname(__file__), 'ffmpeg.exe')
    if os.path.isfile(ffmpeg_local):
        return ffmpeg_local

    return None


def aplicar_dependencias_locais(opcoes):
    ffmpeg_location = obter_ffmpeg_location()
    if ffmpeg_location:
        opcoes['ffmpeg_location'] = ffmpeg_location
    return opcoes


def info_video(url):
    try:
        with yt_dlp.YoutubeDL({'quiet': True, 'noplaylist': True}) as ydl:
            info = ydl.extract_info(url, download=False)
        titulo = info.get('title', 'Titulo desconhecido')
        tamanho = info.get('filesize') or info.get('filesize_approx')
        thumbnail = info.get('thumbnail')
        tamanho_str = f"{round(tamanho / (1024 * 1024), 2)} MB" if tamanho else 'Tamanho desconhecido'
        return {'ok': True, 'titulo': titulo, 'tamanho': tamanho_str, 'thumbnail': thumbnail}
    except Exception as exc:
        return {'ok': False, 'erro': str(exc), 'titulo': None, 'tamanho': None, 'thumbnail': None}


def salvar_thumbnail(url_thumb, destino, titulo, log=None):
    if not url_thumb or not destino or not titulo:
        return
    try:
        titulo_limpo = sanitizar_nome_arquivo(titulo)
        nome_arquivo = os.path.join(destino, f"{titulo_limpo}_thumbnail.jpg")
        resposta = requests.get(url_thumb, stream=True, timeout=20)
        if resposta.status_code == 200:
            with open(nome_arquivo, 'wb') as arquivo:
                for chunk in resposta.iter_content(1024):
                    arquivo.write(chunk)
            if log:
                log(f"Thumbnail salva em: {nome_arquivo}")
    except Exception as exc:
        if log:
            log(f"Falha ao salvar thumbnail: {exc}")


def baixar_com_feedback(ydl_opts, url, log=None, progress=None):
    def extrair_percentual(data):
        baixado = data.get('downloaded_bytes')
        total = data.get('total_bytes') or data.get('total_bytes_estimate')

        if isinstance(baixado, (int, float)) and isinstance(total, (int, float)) and total > 0:
            return max(0.0, min(100.0, (float(baixado) / float(total)) * 100.0))

        perc_str = str(data.get('_percent_str', ''))
        match = re.search(r'(\d+(?:\.\d+)?)\s*%', perc_str)
        if match:
            try:
                return max(0.0, min(100.0, float(match.group(1))))
            except ValueError:
                return None
        return None

    def progress_hook(data):
        status = data.get('status')
        if status == 'downloading':
            perc = extrair_percentual(data)

            if progress and perc is not None:
                progress(perc)

            if log:
                speed = data.get('_speed_str', '').strip()
                eta = data.get('_eta_str', '').strip()
                percentual_texto = f"{perc:.1f}%" if perc is not None else data.get('_percent_str', '').strip()
                log(f"Baixando... {percentual_texto} | {speed} | ETA {eta}")
        elif status == 'finished':
            if progress:
                progress(100.0)
            if log:
                log('Download concluido, processando arquivo...')

    ydl_opts['progress_hooks'] = [progress_hook]
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        return True, None
    except DownloadError as exc:
        return False, str(exc)
    except Exception as exc:
        return False, str(exc)


def baixar_video(url, destino, qualidade='best', formato='mp4', log=None, progress=None):
    qualidade_str = f"[height<={qualidade}]" if qualidade != 'best' else ''
    format_selector = (
        f"bestvideo{qualidade_str}+bestaudio[lang^=pt]/"
        f"bestvideo{qualidade_str}+bestaudio[lang=por]/"
        f"bestvideo{qualidade_str}+bestaudio/best"
    )
    if qualidade == 'best':
        format_selector = 'bestvideo+bestaudio[lang^=pt]/bestvideo+bestaudio[lang=por]/best'

    opcoes = {
        'outtmpl': os.path.join(destino, '%(title)s.%(ext)s'),
        'format': format_selector,
        'merge_output_format': formato,
        'noplaylist': True,
        'allow_unscrambled_format': True,
        'extract_flat': False,
        'retries': 5,
    }
    opcoes = aplicar_dependencias_locais(opcoes)
    return baixar_com_feedback(opcoes, url, log, progress)


def baixar_audio(url, destino, formato='mp3', qualidade='0', log=None, progress=None):
    opcoes = {
        'outtmpl': os.path.join(destino, '%(title)s.%(ext)s'),
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': formato,
            'preferredquality': qualidade,
        }],
        'allow_unscrambled_format': True,
        'extract_flat': False,
        'noplaylist': True,
        'retries': 5,
    }
    opcoes = aplicar_dependencias_locais(opcoes)
    return baixar_com_feedback(opcoes, url, log, progress)


def baixar_playlist_video(url, destino, qualidade='best', itens='all', log=None, progress=None):
    if qualidade != 'best':
        format_selector = (
            f"bestvideo[height<={qualidade}]+bestaudio[lang^=pt]/"
            f"bestvideo[height<={qualidade}]+bestaudio[lang=por]/"
            f"bestvideo[height<={qualidade}]+bestaudio/best"
        )
    else:
        format_selector = 'bestvideo+bestaudio[lang^=pt]/bestvideo+bestaudio[lang=por]/best'

    opcoes = {
        'outtmpl': os.path.join(destino, '%(playlist_title)s', '%(title)s.%(ext)s'),
        'format': format_selector,
        'ignoreerrors': True,
        'allow_unscrambled_format': True,
        'extract_flat': False,
        'retries': 5,
    }
    if itens and itens.lower() != 'all':
        opcoes['playlist_items'] = itens
    opcoes = aplicar_dependencias_locais(opcoes)
    return baixar_com_feedback(opcoes, url, log, progress)


def baixar_playlist_audio(url, destino, formato='mp3', qualidade='0', itens='all', log=None, progress=None):
    opcoes = {
        'outtmpl': os.path.join(destino, '%(playlist_title)s', '%(title)s.%(ext)s'),
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': formato,
            'preferredquality': qualidade,
        }],
        'allow_unscrambled_format': True,
        'extract_flat': False,
        'ignoreerrors': True,
        'retries': 5,
    }
    if itens and itens.lower() != 'all':
        opcoes['playlist_items'] = itens
    opcoes = aplicar_dependencias_locais(opcoes)
    return baixar_com_feedback(opcoes, url, log, progress)


def main():
    from gui import main as gui_main

    gui_main()


if __name__ == '__main__':
    main()
