"""Script de diagnóstico: mostra se o Temp de cada perfil é link/junction.

"""
import stat

from profiles import get_user_profiles


def main():
    for profile in get_user_profiles():
        print(f"\nPERFIL: {profile}")

        paths = [
            profile,
            profile / "AppData",
            profile / "AppData" / "Local",
            profile / "AppData" / "Local" / "Temp",
        ]

        for path in paths:
            try:
                info = path.lstat()
                attributes = getattr(info, "st_file_attributes", 0)

                print(f"\nCaminho: {path}")
                print(f"Existe: {path.exists()}")
                print(f"Link simbólico: {stat.S_ISLNK(info.st_mode)}")
                print(f"Reparse point: {bool(attributes & 0x400)}")
                print(f"Atributos: {hex(attributes)}")

            except OSError as error:
                print(f"Erro: {error}")


if __name__ == "__main__":
    main()
