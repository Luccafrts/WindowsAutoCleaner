import sys

from installer import (
    ask_confirm, is_admin, relaunch_as_admin, show_message, uninstall
)


def main():
    confirmed = "--confirmado" in sys.argv

    if not confirmed and not ask_confirm(
        "Deseja remover o Windows Auto Cleaner?\n\n"
        "Isso desativa a limpeza automática e apaga o programa e os logs "
        "de C:\\ProgramData\\WindowsAutoCleaner."
    ):
        return

    if not is_admin():
        if not relaunch_as_admin(["--confirmado"]):
            show_message("Permissão de administrador negada.", ok=False)
        return

    ok, message = uninstall(remove_files=True)
    show_message(message, ok)


if __name__ == "__main__":
    main()