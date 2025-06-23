import requests

code = """#include <stdio.h>

int main() {
    int a = 10;
    int b = 0;
    int c = a / b;  // Erro: divisão por zero
    printf("Resultado: %d", c);
    return 0;
}
"""

response = requests.post("http://127.0.0.1:8000/analyze/", data={"code": code})
print(response.json())
