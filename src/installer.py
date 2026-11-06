import ctypes
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from xml.sax.saxutils import escape

APP_NAME = "WindowsAutoCleaner"
TASK_NAME = "WindowsAutoCleaner"

INSTALL_DIR = Path(os.environ.get("ProgramData", r"C:\ProgramData")) / APP_NAME
INSTALLED_EXE = INSTALL_DIR / f"{APP_NAME}.exe"

DEFAULT_DAYS = 0      # só apaga arquivos com mais de X dias
RUN_TIME = "13:00"    # horário da limpeza

# Dias da semana em que a limpeza roda (nomes em inglês, como o Windows exige):
# Monday, Tuesday, Wednesday, Thursday, Friday, Saturday, Sunday
# Lista vazia [] = todos os dias.
SCHEDULE_DAYS = ["Monday"] #exemplo: ["Monday", "Wednesday", "Friday"]

DAY_NAMES_PT = {
    "Sunday": "domingo",
    "Monday": "segunda",
    "Tuesday": "terça", 
    "Wednesday": "quarta",
    "Thursday": "quinta", 
    "Friday": "sexta", 
    "Saturday": "sábado",
}


def is_frozen() -> bool:
    """True quando rodando como .exe gerado pelo PyInstaller."""
    return getattr(sys, "frozen", False)


def is_admin() -> bool:
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def relaunch_as_admin(args: list[str]) -> bool:
    """Reabre o programa pedindo elevação (aparece o aviso do UAC)."""
    if is_frozen():
        params = args
    else:
        params = [str(Path(sys.argv[0]).resolve()), *args]

    result = ctypes.windll.shell32.ShellExecuteW(
        None, "runas", sys.executable, subprocess.list2cmdline(params), None, 1
    )
    return result > 32


def show_message(text: str, ok: bool = True) -> None:
    """Caixa de diálogo, já que ao dar duplo clique o console fecha sozinho."""
    icon = 0x40 if ok else 0x10  # informação / erro
    ctypes.windll.user32.MessageBoxW(0, text, "Windows Auto Cleaner", icon)


def ask_confirm(text: str) -> bool:
    """Caixa Sim/Não. Retorna True se o usuário clicar em Sim."""
    # 0x24 = botões Sim/Não + ícone de pergunta; 6 = resposta "Sim"
    return ctypes.windll.user32.MessageBoxW(0, text, "Windows Auto Cleaner", 0x24) == 6


def _schedule_xml() -> str:
    if not SCHEDULE_DAYS:
        return """<ScheduleByDay>
        <DaysInterval>1</DaysInterval>
      </ScheduleByDay>"""

    days = "".join(f"<{day} />" for day in SCHEDULE_DAYS)
    return f"""<ScheduleByWeek>
        <DaysOfWeek>{days}</DaysOfWeek>
        <WeeksInterval>1</WeeksInterval>
      </ScheduleByWeek>"""


def _schedule_text() -> str:
    if not SCHEDULE_DAYS:
        return f"todos os dias às {RUN_TIME}"

    names = [DAY_NAMES_PT[day] for day in SCHEDULE_DAYS]

    if len(names) == 1:
        if SCHEDULE_DAYS[0] in ("Saturday", "Sunday"):
            return f"todos os {names[0]}s às {RUN_TIME}"

        return f"todas as {names[0]}s às {RUN_TIME}"

    if all(day in ("Saturday", "Sunday") for day in SCHEDULE_DAYS):
        return f"todos os {', '.join(names)}s às {RUN_TIME}"

    return f"todas as {', '.join(names)}s às {RUN_TIME}"


def _build_task_xml(command: str, arguments: str) -> str:
    start = datetime.now().strftime(f"%Y-%m-%dT{RUN_TIME}:00")

    return f"""<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo>
    <Description>Limpeza periódica das pastas Temp (Windows Auto Cleaner).</Description>
  </RegistrationInfo>
  <Triggers>
    <CalendarTrigger>
      <StartBoundary>{start}</StartBoundary>
      <Enabled>true</Enabled>
      {_schedule_xml()}
    </CalendarTrigger>
  </Triggers>
  <Principals>
    <Principal id="Author">
      <UserId>S-1-5-18</UserId>
      <RunLevel>HighestAvailable</RunLevel>
    </Principal>
  </Principals>
  <Settings>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <StartWhenAvailable>true</StartWhenAvailable>
    <ExecutionTimeLimit>PT1H</ExecutionTimeLimit>
    <Enabled>true</Enabled>
  </Settings>
  <Actions Context="Author">
    <Exec>
      <Command>{escape(command)}</Command>
      <Arguments>{escape(arguments)}</Arguments>
    </Exec>
  </Actions>
</Task>
"""


def install(days: int = DEFAULT_DAYS) -> tuple[bool, str]:
    """Copia o executável e cria a tarefa agendada (roda como SYSTEM)."""
    try:
        INSTALL_DIR.mkdir(parents=True, exist_ok=True)

        run_args = f"--clean --all-users --days {days}"

        if is_frozen():
            source = Path(sys.executable)
            if source.resolve() != INSTALLED_EXE.resolve():
                shutil.copy2(source, INSTALLED_EXE)
            command = str(INSTALLED_EXE)
            arguments = run_args
        else:
            # Modo desenvolvimento: a tarefa chama o python + main.py.
            command = sys.executable
            main_py = Path(__file__).with_name("main.py").resolve()
            arguments = f'"{main_py}" {run_args}'

        xml_file = Path(tempfile.gettempdir()) / f"{TASK_NAME}.xml"
        xml_file.write_text(_build_task_xml(command, arguments), encoding="utf-16")

        try:
            result = subprocess.run(
                ["schtasks", "/Create", "/TN", TASK_NAME,
                 "/XML", str(xml_file), "/F"],
                capture_output=True, text=True
            )
        finally:
            xml_file.unlink(missing_ok=True)

        if result.returncode != 0:
            return False, f"Falha ao criar a tarefa agendada:\n{result.stderr or result.stdout}"

        return True, (
            "Instalação concluída!\n\n"
            f"A limpeza vai rodar {_schedule_text()} e apagar arquivos "
            f"temporários com mais de {days} dias.\n"
            f"Se o PC estiver desligado nesse horário, ela roda assim que ligar.\n\n"
            f"Logs: C:\\ProgramData\\{APP_NAME}\\Logs"
        )

    except Exception as error:
        return False, f"Erro durante a instalação:\n{error}"


def _task_exists() -> bool:
    result = subprocess.run(
        ["schtasks", "/Query", "/TN", TASK_NAME],
        capture_output=True, text=True
    )
    return result.returncode == 0


def uninstall(remove_files: bool = False) -> tuple[bool, str]:
    """Remove a tarefa agendada e, opcionalmente, a pasta em ProgramData."""
    lines = []

    if _task_exists():
        result = subprocess.run(
            ["schtasks", "/Delete", "/TN", TASK_NAME, "/F"],
            capture_output=True, text=True
        )

        if result.returncode != 0:
            return False, f"Não foi possível remover a tarefa:\n{result.stderr or result.stdout}"

        lines.append("Tarefa agendada removida.")
    else:
        lines.append("A tarefa agendada não foi encontrada (já estava removida).")

    if remove_files and INSTALL_DIR.exists():
        shutil.rmtree(INSTALL_DIR, ignore_errors=True)

        if INSTALL_DIR.exists():
            lines.append(
                f"Não foi possível apagar tudo em {INSTALL_DIR} "
                "(algum arquivo em uso?). Apague a pasta manualmente."
            )
        else:
            lines.append("Executável e logs removidos.")

    lines.append("\nA limpeza automática foi desativada.")
    return True, "\n".join(lines)
