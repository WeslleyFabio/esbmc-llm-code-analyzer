def parse_esbmc_output(output):
    result = {}
    if "VERIFICATION FAILED" in output:
        result["status"] = "Falha na verificação"
    elif "VERIFICATION SUCCESSFUL" in output:
        result["status"] = "Verificação bem-sucedida"
    else:
        result["status"] = "Resultado indefinido"

    # Extrair só a primeira linha de erro encontrada
    error_lines = []
    for line in output.splitlines():
        if "Violated property:" in line or "division by zero" in line or "buffer overflow" in line:
            error_lines.append(line.strip())

    result["errors"] = error_lines
    return result


def clean_esbmc_log(log_text):
    """
    Remove linhas de unwinding loop para deixar o log mais legível no frontend.
    """
    filtered_lines = []
    for line in log_text.splitlines():
        if not line.startswith("Unwinding loop"):
            filtered_lines.append(line)
    return "\n".join(filtered_lines)
