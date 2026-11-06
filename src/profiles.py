import os
import winreg
from pathlib import Path


def get_user_profiles() -> list[Path]:
    profiles = []

    registry_path = (
        r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\ProfileList"
    )

    system_sids = {
        "S-1-5-18",
        "S-1-5-19",
        "S-1-5-20"
    }

    excluded_profiles = {
        "default",
        "default user",
        "public",
        "all users",
        "defaultuser0",
        "wdagutilityaccount",
        "defaultapppool"
    }

    windows_dir = Path(
        os.environ.get("SystemRoot", r"C:\Windows")
    )

    with winreg.OpenKey(
        winreg.HKEY_LOCAL_MACHINE,
        registry_path
    ) as registry:

        index = 0

        while True:
            try:
                sid = winreg.EnumKey(registry, index)
            except OSError:
                break

            index += 1

            if (
                sid in system_sids
                or sid.endswith("_Classes")
                or sid.endswith(".bak")
            ):
                continue

            try:
                with winreg.OpenKey(registry, sid) as profile_key:
                    profile_path, _ = winreg.QueryValueEx(
                        profile_key,
                        "ProfileImagePath"
                    )

            except OSError:
                continue

            if not isinstance(profile_path, str):
                continue

            profile_path = os.path.expandvars(profile_path)
            profile = Path(profile_path)

            if not profile.is_absolute():
                continue

            if profile.name.casefold() in excluded_profiles:
                continue

            # Não incluir perfis localizados dentro do Windows.
            try:
                profile.relative_to(windows_dir)
                continue
            except ValueError:
                pass

            if not profile.is_dir():
                continue

            if profile.parent == profile:
                continue

            # Evita adicionar o mesmo perfil mais de uma vez.
            if any(
                existing.casefold() == str(profile).casefold()
                for existing in profiles
            ):
                continue

            profiles.append(str(profile))

    return [Path(profile) for profile in profiles]