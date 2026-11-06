import argparse
import logging
import sys
from pathlib import Path

from profiles import get_user_profiles
from cleaner import clean_temp_directory
from installer import (
    DEFAULT_DAYS, install, uninstall, is_admin,
    is_frozen, relaunch_as_admin, show_message
)


LOG_DIR = Path(r"C:\ProgramData\WindowsAutoCleaner\Logs")
LOG_FILE = LOG_DIR / "cleanup.log"


def configurar_logs():
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(LOG_FILE, encoding="utf-8"),
            logging.StreamHandler()
        ],
        force=True
    )


def main():
    parser = argparse.ArgumentParser(
        description="Windows Auto Cleaner"
    )

    parser.add_argument(
        "--clean",
        action="store_true",
        help="Executa a exclusão dos arquivos temporários."
    )

    parser.add_argument(
        "--days",
        type=int,
        default=0,
        help="Idade mínima dos arquivos em dias (padrão: 0)."
    )

    parser.add_argument(
        "--all-users",
        action="store_true",
        help="Limpa o Temp de todos os perfis (usado pela tarefa agendada)."
    )

    parser.add_argument(
        "--install",
        action="store_true",
        help="Instala e agenda a limpeza automática (pede administrador)."
    )

    parser.add_argument(
        "--uninstall",
        action="store_true",
        help="Remove a limpeza automática agendada."
    )

    args = parser.parse_args()

    if args.days < 0:
        parser.error("O número de dias não pode ser negativo.")

    # Duplo clique no .exe (sem argumentos) = instalar.
    if args.install or args.uninstall or (is_frozen() and len(sys.argv) == 1):
        if not is_admin():
            forwarded = sys.argv[1:] or ["--install"]
            if not relaunch_as_admin(forwarded):
                show_message("Permissão de administrador negada.", ok=False)
            return

        if args.uninstall:
            ok, message = uninstall()
        else:
            ok, message = install(days=args.days or DEFAULT_DAYS)

        show_message(message, ok)
        return

    configurar_logs()

    profiles = get_user_profiles()

    # Sem --all-users, limita a limpeza ao usuário atual.
    if not args.all_users:
        current_user = Path.home()

        profiles = [
            profile for profile in profiles
            if profile.resolve() == current_user.resolve()
        ]

    mode = "LIMPEZA REAL" if args.clean else "SIMULAÇÃO"

    print("\nWINDOWS AUTO CLEANER")
    print("=" * 45)
    print(f"MODO: {mode}")
    print(f"Idade mínima dos arquivos: {args.days} dias")
    print("=" * 45)

    logging.info("=" * 50)
    logging.info("Iniciando Windows Auto Cleaner")
    logging.info("Modo: %s", mode)
    logging.info("Idade mínima: %s dias", args.days)

    total_files = 0
    total_bytes = 0
    total_deleted = 0
    total_in_use = 0
    total_denied = 0
    total_errors = 0

    for profile in profiles:
        temp_dir = profile / "AppData" / "Local" / "Temp"

        print(f"\nPerfil: {profile}")
        logging.info("Analisando perfil: %s", profile)

        if not temp_dir.is_dir():
            print("  Pasta Temp não encontrada. Ignorando.")
            logging.info("Pasta Temp não encontrada: %s", temp_dir)
            continue

        stats = clean_temp_directory(
            temp_dir=temp_dir,
            days=args.days,
            clean=args.clean
        )

        total_files += stats["files_found"]
        total_bytes += stats["total_bytes"]
        total_deleted += stats["files_deleted"]
        total_in_use += stats["files_in_use"]
        total_denied += stats["access_denied"]
        total_errors += stats["errors"]

        space_mb = stats["total_bytes"] / (1024 ** 2)

        print(f"  Arquivos encontrados: {stats['files_found']}")
        print(f"  Espaço analisado: {space_mb:.2f} MB")

        if args.clean:
            print(f"  Arquivos excluídos: {stats['files_deleted']}")

        logging.info(
            "Perfil: %s | Encontrados: %s | Espaço: %.2f MB | Excluídos: %s",
            profile,
            stats["files_found"],
            space_mb,
            stats["files_deleted"]
        )

    total_mb = total_bytes / (1024 ** 2)

    print("\n" + "=" * 45)
    print("RESUMO GERAL")
    print("=" * 45)
    print(f"Arquivos encontrados: {total_files}")
    print(f"Espaço analisado: {total_mb:.2f} MB")

    if args.clean:
        print(f"Arquivos excluídos: {total_deleted}")

    print(f"Arquivos em uso: {total_in_use}")
    print(f"Acessos negados: {total_denied}")
    print(f"Outros erros: {total_errors}")
    print("=" * 50)

    logging.info("RESUMO FINAL")
    logging.info("Arquivos encontrados: %s", total_files)
    logging.info("Espaço analisado: %.2f MB", total_mb)
    logging.info("Arquivos excluídos: %s", total_deleted)
    logging.info("Arquivos em uso: %s", total_in_use)
    logging.info("Acessos negados: %s", total_denied)
    logging.info("Outros erros: %s", total_errors)
    logging.info("Execução finalizada.")
    print("=" * 50)


if __name__ == "__main__":
    main()