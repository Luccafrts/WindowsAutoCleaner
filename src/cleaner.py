import os
import stat
import time
import logging
from pathlib import Path


def is_reparse_point(path: Path) -> bool:
    """Identifica links simbólicos e junctions do Windows."""

    try:
        info = path.lstat()

        return (
            stat.S_ISLNK(info.st_mode)
            or bool(
                getattr(info, "st_file_attributes", 0) & 0x400
            )
        )

    except OSError as error:
        logging.warning(
            "Não foi possível verificar o caminho %s: %s",
            path,
            error
        )
        return True


def clean_temp_directory(
    temp_dir: Path,
    days: int = 0,
    clean: bool = False
) -> dict:
    """Analisa ou limpa arquivos temporários de um usuário."""

    stats = {
        "files_found": 0,
        "total_bytes": 0,
        "files_deleted": 0,
        "files_in_use": 0,
        "access_denied": 0,
        "errors": 0
    }

    if not temp_dir.is_dir():
        logging.warning("Pasta não encontrada: %s", temp_dir)
        return stats

    if is_reparse_point(temp_dir):
        logging.warning(
            "Pasta ignorada por ser link ou junction: %s",
            temp_dir
        )
        return stats

    cutoff = time.time() - (days * 86400)

    def walk_error(error):
        winerror = getattr(error, "winerror", None)

        if winerror == 5:
            stats["access_denied"] += 1
        else:
            stats["errors"] += 1

        logging.warning(
            "Erro ao acessar diretório: %s",
            error
        )

    for root, dirs, files in os.walk(
        temp_dir,
        topdown=True,
        followlinks=False,
        onerror=walk_error
    ):

        root_path = Path(root)

        # Impede a entrada em links e junctions.
        dirs[:] = [
            directory
            for directory in dirs
            if not is_reparse_point(root_path / directory)
        ]

        for filename in files:

            file_path = root_path / filename

            try:
                info = file_path.lstat()

                # Considera somente arquivos regulares.
                if not stat.S_ISREG(info.st_mode):
                    continue

                # Ignora links simbólicos e reparse points.
                if is_reparse_point(file_path):
                    continue

                # Verifica a idade do arquivo.
                if info.st_mtime > cutoff:
                    continue

                stats["files_found"] += 1
                stats["total_bytes"] += info.st_size

                if clean:
                    file_path.unlink()

                    stats["files_deleted"] += 1

                    # Registra individualmente cada exclusão.
                    logging.info(
                        "ARQUIVO EXCLUÍDO: %s | Tamanho: %.2f KB",
                        file_path,
                        info.st_size / 1024
                    )

            except OSError as error:

                winerror = getattr(error, "winerror", None)

                if winerror in (32, 33):
                    stats["files_in_use"] += 1

                elif winerror == 5:
                    stats["access_denied"] += 1

                else:
                    stats["errors"] += 1

                logging.warning(
                    "Não foi possível processar %s: %s",
                    file_path,
                    error
                )

    return stats