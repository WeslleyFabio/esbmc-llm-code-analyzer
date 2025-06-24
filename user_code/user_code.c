#include <stdio.h>

int main() {
    int array[5];
    int i;

    for (i = 0; i <= 5; i++) {  // Erro proposital: acessa índice fora do limite
        array[i] = i * 2;
        printf("array[%d] = %d\n", i, array[i]);
    }

    return 0;
}
