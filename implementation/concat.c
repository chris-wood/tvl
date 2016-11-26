char *
concat(char *x, char*y)
{
    int xLength = strlen(x);
    int yLength = strlen(y);
    char *z = malloc(xLength + yLength + 1);
    memcpy(z, x, xLength);
    memcpy(z + xLength, y, yLength);
    z[xLength + yLength] = 0;
    return z;
}
