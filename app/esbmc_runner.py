import subprocess
import os


def windows_path_to_wsl_path(windows_path):
    """
    Converte um caminho de arquivo Windows (ex: C:\\Users\\...) para o path correspondente no WSL (/mnt/c/Users/...)
    """
    drive, path_rest = os.path.splitdrive(windows_path)
    drive_letter = drive.rstrip(":").lower()
    wsl_path = "/mnt/" + drive_letter + path_rest.replace("\\", "/")
    return wsl_path


def run_esbmc(file_path, options=None):
    """
    Executa o ESBMC no WSL usando o caminho do código C salvo no Windows.
    """
    import subprocess
    import os

    if options is None:
        options = []

    try:
        # Converte o caminho do arquivo C (Windows) para o path WSL
        wsl_input_path = windows_path_to_wsl_path(os.path.abspath(file_path))

        # Caminho absoluto para o esbmc no WSL
        esbmc_path_wsl = "/home/rafael/esbmc/build/src/esbmc/esbmc"

        # Comando final que será executado dentro do WSL
        command = ["wsl", esbmc_path_wsl, wsl_input_path] + options
        # command = ["wsl", esbmc_path_wsl, wsl_input_path]

        print(f"Executando comando: {' '.join(command)}")  # Log para depuração

        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=120  # Tempo máximo de execução
        )

        return result.stdout

    except subprocess.TimeoutExpired:
        return "Erro: Tempo limite de execução excedido ao rodar o ESBMC."

    except Exception as e:
        return f"Erro inesperado ao executar ESBMC via WSL: {str(e)}"
