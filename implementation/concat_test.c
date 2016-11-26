#include <assert.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>

#include "concat.c"

int main()
{
    {
        char* tmp = concat("Hello, ", "World!");
        assert(strcmp(tmp, "Hello, World!") == 0);
    }
}
