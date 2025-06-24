#include <stdio.h>
#include <stdlib.h>
#include <pthread.h>

int shared_resource = 0;
pthread_mutex_t lock;

void *thread_func(void *arg)
{
    pthread_mutex_lock(&lock);
    shared_resource++;
    pthread_mutex_lock(&lock); // Deadlock proposital
    pthread_mutex_unlock(&lock);
    pthread_mutex_unlock(&lock);
    return NULL;
}

int main()
{
    // ===== Integer Overflow =====
    unsigned char overflow_var = 250;
    overflow_var += 10; // Provoca overflow de inteiro
    printf("Resultado do Overflow: %d\\n", overflow_var);

    // ===== Memory Leak =====
    int *leak = malloc(10 * sizeof(int));
    leak[0] = 42;
    // Intencionalmente não damos free()

    // ===== Array Out of Bounds =====
    int arr[5];
    arr[10] = 123; // Acesso fora dos limites do array

    // ===== Deadlock =====
    pthread_t t1;
    pthread_mutex_init(&lock, NULL);
    pthread_create(&t1, NULL, thread_func, NULL);
    pthread_join(t1, NULL);
    pthread_mutex_destroy(&lock);

    return 0;
}
