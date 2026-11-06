# Windows Auto Cleaner

Programa para Windows que limpa automaticamente a pasta `Temp` dos usuários, em horários agendados. O usuário só precisa **dar um duplo clique no executável**: ele se instala e se agenda sozinho.

## Como funciona

1. O usuário executa `WindowsAutoCleaner.exe` e aceita o aviso de administrador (UAC).
2. O programa copia a si mesmo para `C:\ProgramData\WindowsAutoCleaner\`.
3. Ele cria uma tarefa no **Agendador de Tarefas** do Windows, rodando como `SYSTEM`.
4. Por padrão, a tarefa roda **as segundas às 13:00** e apaga arquivos temporários com **de 0 dias ou mais**.
5. Se o computador estiver desligado no horário, a limpeza roda assim que ele for ligado.

Depois de instalado, o executável original pode ser apagado. A tarefa usa a cópia em `ProgramData`.

## Instalação e remoção

**Instalar:** dê duplo clique em `WindowsAutoCleaner.exe`. Uma caixa de diálogo confirma a instalação.

**Desinstalar:** dê duplo clique em `Desinstalar_WindowsAutoCleaner.exe`. Ele remove a tarefa agendada e apaga `C:\ProgramData\WindowsAutoCleaner` (programa e logs).

Rodar o instalador de novo não cria tarefas duplicadas: a tarefa `WindowsAutoCleaner` é sobrescrita com a configuração mais recente.

> O executável não é assinado digitalmente, então o Windows SmartScreen ou o antivírus podem exibir um aviso. Se confiar na origem, escolha "Mais informações" > "Executar assim mesmo".

## Uso pela linha de comando

Sem `--clean`, o programa roda em **modo simulação**: apenas informa o que seria apagado.

```bat
:: Simulação, só o usuário atual
python src\main.py

:: Simulação, todos os perfis, arquivos com mais de 7 dias
python src\main.py --all-users --days 7

:: Limpeza real
python src\main.py --clean --days 7
```

| Opção | O que faz |
|---|---|
| `--clean` | Apaga de verdade. Sem ela, é só simulação. |
| `--days N` | Só considera arquivos modificados há mais de N dias (padrão: 0). |
| `--all-users` | Inclui todos os perfis de usuário, não só o atual. |
| `--install` | Instala e agenda a limpeza (pede administrador). |
| `--uninstall` | Remove a tarefa agendada. |

## Configuração do agendamento

No topo de `src/installer.py`:

```python
DEFAULT_DAYS = 0              # idade mínima dos arquivos, em dias
RUN_TIME = "13:00"            # horário da limpeza
SCHEDULE_DAYS = ["Monday"]    # dias da semana; [] = todos os dias
```

Os dias devem estar em inglês (`Monday`, `Tuesday`, `Wednesday`, `Thursday`, `Friday`, `Saturday`, `Sunday`). Depois de alterar, gere o executável de novo e reinstale.

## Gerando o executável

Requisitos: Windows e Python 3.10 ou superior (desenvolvido e testado com Python 3.14 no Windows 11).

```bat
build.bat
```

Isso gera, em `dist\`:

- `WindowsAutoCleaner.exe` (instalador e programa de limpeza)
- `Desinstalar_WindowsAutoCleaner.exe` (desinstalador)

O `build.bat` usa o [PyInstaller](https://pyinstaller.org). O programa só depende da biblioteca padrão do Python.

## Segurança

Como o programa apaga arquivos, ele foi escrito de forma conservadora:

- **Modo simulação por padrão.** Nada é apagado sem `--clean`.
- **Só apaga arquivos regulares** com data de modificação mais antiga que o limite de dias.
- **Ignora links simbólicos e junctions** (reparse points), tanto de arquivos quanto de pastas, e não entra neles. Isso evita apagar conteúdo fora do `Temp` por engano.
- **Arquivos em uso são pulados**, sem forçar a exclusão.
- **Limpa apenas** `AppData\Local\Temp` de cada perfil de usuário. Perfis de sistema e perfis padrão (`Default`, `Public` etc.) são ignorados.
- **Registro completo:** cada arquivo excluído é gravado em `C:\ProgramData\WindowsAutoCleaner\Logs\cleanup.log`, com um resumo no final de cada execução.

A tarefa agendada roda como `SYSTEM` com privilégios elevados, para conseguir limpar o `Temp` de todos os usuários. Por isso, teste sempre em modo simulação antes de instalar em máquinas importantes.

## Limitações

- Apenas Windows.
- Limpa só `AppData\Local\Temp` dos perfis. Não limpa `C:\Windows\Temp` nem caches de navegador.
- Remove arquivos, mas não remove pastas vazias.
- O executável não é assinado digitalmente.

## Estrutura do projeto

```
WindowsAutoCleaner/
├── build.bat              # gera os executáveis com PyInstaller
└── src/
    ├── main.py            # ponto de entrada e linha de comando
    ├── cleaner.py         # lógica de limpeza de uma pasta Temp
    ├── profiles.py        # lista os perfis de usuário (registro do Windows)
    ├── installer.py       # instalação e tarefa agendada
    ├── desinstalar.py     # ponto de entrada do desinstalador
    └── diagnostico.py     # mostra links/junctions nos perfis (não apaga nada)
```
