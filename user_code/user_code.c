#include <stdio.h>
#include <stdlib.h>
#include <pthread.h>

int shared_resource = 0;
pthread_mutex_t lock;

void* cause_deadlock(void* arg) {
    pthread_mutex_lock(&lock);
    shared_resource++;
    pthread_mutex_lock(&lock);  // Deadlock proposital
    pthread_mutex_unlock(&lock);
    pthread_mutex_unlock(&lock);
    return NULL;
}

int main() {
    // ====== Integer Overflow ======
    unsigned char overflow_var = 250;
    overflow_var += 10;  // Overflow proposital

    // ====== NaN Example ======
    double zero = 0.0;
    double nan_result = 0.0 / zero;  // Gera NaN

    // ====== Array Out of Bounds ======
    int array[5];
    array[10] = 123;  // Array bounds violation proposital

    // ====== Deadlock ======
    pthread_t t1;
    pthread_mutex_init(&lock, NULL);
    pthread_create(&t1, NULL, cause_deadlock, NULL);
    pthread_join(t1, NULL);
    pthread_mutex_destroy(&lock);

    return 0;
}
