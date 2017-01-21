int
add(int a, int b)
{
    return a + b;
}

void add(int a, int b, int *c)
{
    *c = a + b;
}

int inc(int x)
{
    return x + 1;
}

void incp(int *x)
{
    *x++;
}
