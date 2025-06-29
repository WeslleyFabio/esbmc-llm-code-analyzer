#include <stdio.h>
#include <stdlib.h>

int main() {
    // 1. Null pointer exception
    int *ptr = NULL;
    *ptr = 42;  // Erro: tentativa de acessar ponteiro nulo

    // 2. Buffer overflow
    char buffer[10];
    for (int i = 0; i <= 10; i++) {  // i vai de 0 até 10 (11 posições)
        buffer[i] = 'A';  // Erro: buffer tem apenas 10 posições (0 a 9)
    }

    // 3. Array out of bounds
    int arr[5] = {1, 2, 3, 4, 5};
    int index = 6;
    int value = arr[index];  // Erro: índice fora dos limites do array

    printf("Valor acessado: %d\n", value);
    return 0;
}
