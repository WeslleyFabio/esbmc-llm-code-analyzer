import os
from fastapi import FastAPI, Form, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from esbmc_runner import run_esbmc
from output_parser import parse_esbmc_output, clean_esbmc_log
from llm_client import get_llm_response
import json
from typing import Optional

load_dotenv()

app = FastAPI()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def wrap_long_lines(log_text, max_length=120):
    wrapped_lines = []
    for line in log_text.splitlines():
        while len(line) > max_length:
            wrapped_lines.append(line[:max_length])
            line = line[max_length:]
        wrapped_lines.append(line)
    return "\n".join(wrapped_lines)


@app.post("/analyze/")
async def analyze_code(
    code: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    properties: Optional[str] = Form("[]")  # <-- novo parâmetro
):
    # Se o usuário enviou um arquivo, lê o conteúdo dele
    if file:
        code_content = (await file.read()).decode("utf-8")
    else:
        code_content = code

    # Salva o código C recebido (do textarea ou do arquivo)
    # Usa BASE_DIR para garantir que user_code seja salvo na raiz do projeto
    user_code_dir = os.path.join(BASE_DIR, "user_code")
    os.makedirs(user_code_dir, exist_ok=True) # Garante que a pasta 'user_code' exista

    user_code_path = os.path.join(user_code_dir, "user_code.c")
    with open(user_code_path, "w", encoding="utf-8") as f:
        f.write(code_content)

    selected_props = json.loads(properties)
    esbmc_output = run_esbmc(user_code_path, selected_props)
    cleaned_log = clean_esbmc_log(esbmc_output)
    cleaned_log = wrap_long_lines(cleaned_log)
    parsed_output = parse_esbmc_output(esbmc_output)
    llm_response = get_llm_response(code_content, parsed_output)


    # Salva o resultado final no disco para o endpoint de download
    # Também usa BASE_DIR para garantir que result.txt seja salvo na raiz do projeto
    output_dir = os.path.join(BASE_DIR, "user_code") # A mesma pasta 'user_code'
    os.makedirs(output_dir, exist_ok=True) # Garante que a pasta exista (redundante, mas seguro)

    output_file = os.path.join(output_dir, "result.txt")
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("==== Log ESBMC ====\n\n")
        f.write(esbmc_output + "\n\n")
        f.write("==== Texto da LLM ====\n\n")
        f.write(llm_response + "\n\n")
        f.write("==== By Rafael, Renan e Weslley ====\n")

    return JSONResponse({
        "esbmc_output": cleaned_log,
        "parsed_output": parsed_output,
        "llm_interpretation": llm_response
    })


@app.post("/download/")
async def download_result():
    # Usa BASE_DIR para o download também, garantindo o caminho correto do arquivo
    download_dir = os.path.join(BASE_DIR, "user_code")
    output_file = os.path.join(download_dir, "result.txt")
    
    if os.path.exists(output_file):
        return FileResponse(path=output_file, filename="resultado_analise.txt", media_type="text/plain")
    else:
        return JSONResponse({"error": "Arquivo de resultado não encontrado."}, status_code=404)

# A montagem dos arquivos estáticos já está correta com BASE_DIR
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")


@app.get("/", response_class=HTMLResponse)
async def frontend():
    html_content = """
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Secure C Analyzer</title>
        <link rel="stylesheet" href="/static/style.css">
    </head>
    <body>
        <header class="header">
            <div class="header-container">
                <div class="header-left">
                    <div class="logo">
                        <div class="logo-icon">🛡️</div>
                        <div class="logo-text">
                            <h1>Secure C Analyzer</h1>
                            <p>Análise de Segurança com ESBMC e LLM</p>
                        </div>
                    </div>
                </div>
                <div class="header-right">
                    <div class="header-badge">
                        <span>💻</span>
                        <span>Código C</span>
                    </div>
                    <div class="header-badge">
                        <span>⚡</span>
                        <span>Análise Rápida</span>
                    </div>
                </div>
            </div>
        </header>

        <div class="main-container">
            <div class="content-grid">
                <div class="main-content">
                    <div class="card">
                        <div class="card-header">
                            <h2>Código C para Análise</h2>
                            <p>Cole seu código C ou faça upload de um arquivo</p>
                        </div>
                        <div class="card-content">
                            <div class="file-upload-section">
                                <div class="file-upload-header">
                                    <label class="file-upload-label">Upload de Arquivo</label>
                                    <button id="clearFileBtn" class="clear-file-btn" style="display: none;">✕</button>
                                </div>
                                <div id="fileUploadArea" class="file-upload-area">
                                    <input type="file" id="fileInput" accept=".c" class="file-input">
                                    <div class="file-upload-content">
                                        <div class="upload-icon">📁</div>
                                        <p>Clique para selecionar um arquivo .c</p>
                                        <p class="upload-subtitle">Ou arraste e solte aqui</p>
                                    </div>
                                </div>
                                <div id="fileInfo" class="file-info" style="display: none;">
                                    <span class="file-icon">📄</span>
                                    <span id="fileName" class="file-name"></span>
                                    <span id="fileSize" class="file-size"></span>
                                </div>
                            </div>

                            <textarea 
                                id="codeInput" 
                                placeholder="Cole aqui seu código C..."
                                class="code-textarea"
                            ></textarea>
                            
                            <div class="analyze-section">
                                <button id="analyzeBtn" class="analyze-btn">
                                    <span id="analyzeIcon">▶️</span>
                                    <span id="analyzeText">Analisar Código</span>
                                </button>
                            </div>
                        </div>
                    </div>

                    <div id="resultsSection" class="card" style="display: none;">
                        <div class="card-header">
                            <div class="results-header">
                                <div class="results-title">
                                    <span class="success-icon">✅</span>
                                    <h3>Resultado da Análise</h3>
                                </div>
                                <div class="results-actions">
                                    <button id="toggleLogBtn" class="action-btn">
                                        <span id="logIcon">👁️</span>
                                        <span id="logTextBtn">📝 Ver Log ESBMC</span>
                                    </button>
                                    <button id="downloadBtn" class="action-btn">
                                        <span>📥</span>
                                        <span>⬇️ Baixar Resultado</span>
                                    </button>
                                </div>
                            </div>
                        </div>
                        <div class="card-content">
                            <div class="results-content">
                                <div class="analysis-result">
                                    <pre id="analysisText" class="analysis-text"></pre>
                                    <span id="typingCursor" class="typing-cursor">|</span>
                                </div>
                                <div id="logSection" class="log-section" style="display: none;">
                                    <pre id="esbmcLogContent" class="log-text">Log ESBMC não disponível</pre>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div id="loadingSection" class="card" style="display: none;">
                        <div class="card-content">
                            <div class="loading-content">
                                <div class="spinner"></div>
                                <div class="loading-text">
                                    <h3>Analisando código...</h3>
                                    <p>Executando verificações de segurança com ESBMC</p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="sidebar">
                    <div class="card properties-card">
                        <div class="card-header">
                            <div class="properties-header">
                                <div class="properties-title">
                                    <span>⚙️</span>
                                    <h3>Propriedades de Verificação</h3>
                                </div>
                                <button id="togglePropertiesBtn" class="toggle-btn">−</button>
                            </div>
                            <p>Selecione as verificações que deseja executar</p>
                        </div>
                        <div id="propertiesContent" class="card-content">
                            <button id="selectAllBtn" class="select-all-btn">
                                <span id="selectAllIcon">☐</span>
                                <span id="selectAllText">Selecionar Tudo</span>
                            </button>
                            
                            <div class="properties-list">
                                <div class="property-item">
                                    <input type="checkbox" id="multi-property" name="properties" value="--multi-property">
                                    <label for="multi-property">
                                        <div class="property-label">Multi Property</div>
                                        <div class="property-description">Verifica múltiplas propriedades</div>
                                    </label>
                                </div>
                                <div class="property-item">
                                    <input type="checkbox" id="compact-trace" name="properties" value="--compact-trace">
                                    <label for="compact-trace">
                                        <div class="property-label">Compact Trace</div>
                                        <div class="property-description">Traz todos os contraexemplos do --multi-property</div>
                                    </label>
                                </div>
                                <div class="property-item">
                                    <input type="checkbox" id="no-standard-checks" name="properties" value="--no-standard-checks">
                                    <label for="no-standard-checks">
                                        <div class="property-label">No Standard Checks</div>
                                        <div class="property-description">Desabilita verificações padrão</div>
                                    </label>
                                </div>
                                <div class="property-item">
                                    <input type="checkbox" id="no-assertions" name="properties" value="--no-assertions">
                                    <label for="no-assertions">
                                        <div class="property-label">No Assertions</div>
                                        <div class="property-description">Ignora asserções</div>
                                    </label>
                                </div>
                                <div class="property-item">
                                    <input type="checkbox" id="no-bounds-check" name="properties" value="--no-bounds-check">
                                    <label for="no-bounds-check">
                                        <div class="property-label">No Bounds Check</div>
                                        <div class="property-description">Desabilita verificação de limites</div>
                                    </label>
                                </div>
                                <div class="property-item">
                                    <input type="checkbox" id="no-div-by-zero-check" name="properties" value="--no-div-by-zero-check">
                                    <label for="no-div-by-zero-check">
                                        <div class="property-label">No Division by Zero</div>
                                        <div class="property-description">Ignora divisão por zero</div>
                                    </label>
                                </div>
                                <div class="property-item">
                                    <input type="checkbox" id="no-pointer-check" name="properties" value="--no-pointer-check">
                                    <label for="no-pointer-check">
                                        <div class="property-label">No Pointer Check</div>
                                        <div class="property-description">Desabilita verificação de ponteiros</div>
                                    </label>
                                </div>
                                <div class="property-item">
                                    <input type="checkbox" id="memory-leak-check" name="properties" value="--memory-leak-check">
                                    <label for="memory-leak-check">
                                        <div class="property-label">Memory Leak Check</div>
                                        <div class="property-description">Verifica vazamentos de memória</div>
                                    </label>
                                </div>
                                <div class="property-item">
                                    <input type="checkbox" id="no-align-check" name="properties" value="--no-align-check">
                                    <label for="no-align-check">
                                        <div class="property-label">No Alignment Check</div>
                                        <div class="property-description">Ignora alinhamento de memória</div>
                                    </label>
                                </div>
                                <div class="property-item">
                                    <input type="checkbox" id="overflow-check" name="properties" value="--overflow-check">
                                    <label for="overflow-check">
                                        <div class="property-label">Overflow Check</div>
                                        <div class="property-description">Verifica overflow de inteiros</div>
                                    </label>
                                </div>
                                <div class="property-item">
                                    <input type="checkbox" id="nan-check" name="properties" value="--nan-check">
                                    <label for="nan-check">
                                        <div class="property-label">NaN Check</div>
                                        <div class="property-description">Verifica valores NaN</div>
                                    </label>
                                </div>
                                <div class="property-item">
                                    <input type="checkbox" id="deadlock-check" name="properties" value="--deadlock-check">
                                    <label for="deadlock-check">
                                        <div class="property-label">Deadlock Check</div>
                                        <div class="property-description">Detecta deadlocks</div>
                                    </label>
                                </div>
                                <div class="property-item">
                                    <input type="checkbox" id="data-races-check" name="properties" value="--data-races-check">
                                    <label for="data-races-check">
                                        <div class="property-label">Data Races Check</div>
                                        <div class="property-description">Verifica condições de corrida</div>
                                    </label>
                                </div>
                            </div>
                            
                            <div class="properties-counter">
                                <span id="propertiesCount">0 de 12 selecionadas</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

    <script>
        const analyzeBtn = document.getElementById('analyzeBtn');
        const codeInput = document.getElementById('codeInput');
        const fileInput = document.getElementById('fileInput');
        const logSection = document.getElementById('logSection');
        const esbmcLogContent = document.getElementById('esbmcLogContent'); // Renamed from logText for clarity within the log section
        const analysisText = document.getElementById('analysisText');
        const typingCursor = document.getElementById('typingCursor');
        const resultsSection = document.getElementById('resultsSection');
        const loadingSection = document.getElementById('loadingSection');

        // New elements for file handling
        const fileInfo = document.getElementById('fileInfo');
        const fileNameSpan = document.getElementById('fileName');
        const fileSizeSpan = document.getElementById('fileSize');
        const clearFileBtn = document.getElementById('clearFileBtn');

        analyzeBtn.addEventListener('click', analyzeCode);

        // Event listener for file input change
        fileInput.addEventListener('change', () => {
            const file = fileInput.files[0];
            if (file) {
                fileNameSpan.textContent = file.name;
                fileSizeSpan.textContent = `(${formatBytes(file.size)})`;
                fileInfo.style.display = 'flex'; // Use flex to display filename and size inline
                clearFileBtn.style.display = 'inline-block';
                codeInput.value = ''; // Clear code input when a file is selected
            } else {
                fileNameSpan.textContent = '';
                fileSizeSpan.textContent = '';
                fileInfo.style.display = 'none';
                clearFileBtn.style.display = 'none';
            }
        });

        // Event listener for clear file button
        clearFileBtn.addEventListener('click', () => {
            fileInput.value = ''; // Clear the selected file
            fileNameSpan.textContent = '';
            fileSizeSpan.textContent = '';
            fileInfo.style.display = 'none';
            clearFileBtn.style.display = 'none';
        });

        // Helper function to format file size
        function formatBytes(bytes, decimals = 2) {
            if (bytes === 0) return '0 Bytes';
            const k = 1024;
            const dm = decimals < 0 ? 0 : decimals;
            const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
            const i = Math.floor(Math.log(bytes) / Math.log(k));
            return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
        }

        async function analyzeCode() {
            analysisText.textContent = '';
            esbmcLogContent.textContent = ''; // Use esbmcLogContent here
            resultsSection.style.display = 'none';
            loadingSection.style.display = 'block';

            const formData = new FormData();

            const file = fileInput.files[0];
            if (file) {
                formData.append('file', file);
            } else {
                const code = codeInput.value;
                formData.append('code', code);
            }

            const checkboxes = document.querySelectorAll('input[name="properties"]:checked');
            const properties = Array.from(checkboxes).map(cb => cb.value);
            formData.append('properties', JSON.stringify(properties));
            try {
                const res = await fetch('/analyze/', {
                    method: 'POST',
                    body: formData
                });
                const data = await res.json();
                showResults(data.llm_interpretation, data.esbmc_output);

            } catch (error) {
                analysisText.textContent = '❌ Erro ao analisar: ' + error;
                typingCursor.style.display = 'none';
            } finally {
                loadingSection.style.display = 'none';
            }
        }

        function showResults(text, esbmcLog) {
            resultsSection.style.display = 'block';
            typingCursor.style.display = 'inline';
            let i = 0;

            function typeChar() {
                if (i < text.length) {
                    analysisText.textContent += text.charAt(i);
                    i++;
                    setTimeout(typeChar, 20);
                } else {
                    typingCursor.style.display = 'none';
                }
            }

            typeChar();
            esbmcLogContent.textContent = esbmcLog; // Use esbmcLogContent here
        }

        // Mostrar/ocultar log ESBMC
        const toggleLogBtn = document.getElementById('toggleLogBtn');
        toggleLogBtn.addEventListener('click', () => {
            logSection.style.display = (logSection.style.display === 'none' || logSection.style.display === '') ? 'block' : 'none';
        });
        // Baixar resultado
        const downloadBtn = document.getElementById('downloadBtn');
        downloadBtn.addEventListener('click', async () => {
            try {
                const response = await fetch('/download/', { method: 'POST' });
                if (!response.ok) throw new Error('Erro ao baixar resultado.');
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = 'resultado_analise.txt';
                document.body.appendChild(a);
                a.click();
                a.remove();
                window.URL.revokeObjectURL(url);
            } catch (error) {
                alert('❌ Erro no download: ' + error);
            }
        });
        // Botão Selecionar Tudo
        const selectAllBtn = document.getElementById('selectAllBtn');
        const selectAllIcon = document.getElementById('selectAllIcon');
        const selectAllText = document.getElementById('selectAllText');
        const propertiesCount = document.getElementById('propertiesCount');
        const propertyCheckboxes = document.querySelectorAll('input[name="properties"]');

        selectAllBtn.addEventListener('click', () => {
            const allChecked = Array.from(propertyCheckboxes).every(cb => cb.checked);
            propertyCheckboxes.forEach(cb => cb.checked = !allChecked);
            updatePropertiesCount();
        });
        propertyCheckboxes.forEach(cb => cb.addEventListener('change', updatePropertiesCount));

        function updatePropertiesCount() {
            const total = propertyCheckboxes.length;
            const checked = Array.from(propertyCheckboxes).filter(cb => cb.checked).length;
            propertiesCount.textContent = `${checked} de ${total} selecionadas`;
            if (checked === total) {
                selectAllIcon.textContent = '☑️';
                selectAllText.textContent = 'Desmarcar Tudo';
            } else {
                selectAllIcon.textContent = '☐';
                selectAllText.textContent = 'Selecionar Tudo';
            }
        }

        // Expandir/recolher painel de propriedades
        const togglePropertiesBtn = document.getElementById('togglePropertiesBtn');
        const propertiesContent = document.getElementById('propertiesContent');

        togglePropertiesBtn.addEventListener('click', () => {
            const isVisible = propertiesContent.style.display !== 'none';
            propertiesContent.style.display = isVisible ? 'none' : 'block';
            togglePropertiesBtn.textContent = isVisible ? '+' : '−';
        });
        // Inicialização
        updatePropertiesCount();
    </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)