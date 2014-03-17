#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <gsl/gsl_matrix.h>

gsl_matrix *new_matrix(int x, int y)
{
    int i, j;
    gsl_matrix *matrix = gsl_matrix_alloc(x, y);
    for(i = 0; i < x; ++i) {
        for(j = 0; j < y; ++j) {
            gsl_matrix_set(matrix, i, j, (i * x + j + 1));
        }
    }
    return matrix;
}

void matrix_show(FILE *fs, gsl_matrix *matrix)
{
    int i, j;
    double val;
    for (i = 0; i < matrix->size1; ++i) {
        for(j = 0; j < matrix->size2; ++j) {
            val = gsl_matrix_get(matrix, i, j);
            fprintf(fs, "%.1f\t", val);
        }
        fprintf(fs, "\n");
    }
}

double traverse_matrix1(gsl_matrix *matrix) {
    int i, j;
    double sum = 0;
    int x = matrix->size1;
    int y = matrix->size2;
    for(j = 0; j < y; ++j) {
        for(i = 0; i < x; ++i) {
            sum += gsl_matrix_get(matrix, i, j);
        }
    }
    return sum;
}

double traverse_matrix2(gsl_matrix *matrix) {
    int i, j;
    double sum = 0.0;
    double val = 0.0;
    int sz = matrix->size1;
    if (matrix->size1 != matrix->size2)
        return 0.0f;
    //printf("size = %d\n", sz);
    for(i = 0; i < sz; ++i) {
        for(j = 0;j <= i;++j) {
            //printf("%d %d\n", j, i-j);
            val = gsl_matrix_get(matrix, j, i-j);
            //printf("%.0f\n", val);
            sum += val;
        }
    }
    // bottom half
    for(i = 1; i < sz; ++ i) { // line
        //i,3
        for (j = 0; i + j < sz; ++j) {//
            //printf("%d %d\n", i + j, sz - 1 - j);
            val = gsl_matrix_get(matrix, i+j, sz - 1 -j);
            //printf("%.0f\n", val);
            sum += val;
        }
    }
    return sum;
}

int main(int argc, char *argv[])
{
    int x = 256, y =256;
    if(argc > 2) {
        x = atoi(argv[1]);
        y = atoi(argv[2]);
    }
    if (x <= 0 || y <= 0) {
        x = 100;
        y = 100;
    }
    
    gsl_matrix *mat1 = new_matrix(x, y);
    gsl_matrix *mat2 = gsl_matrix_alloc(x, y);
    gsl_matrix_set_all(mat2, 3.0);
    //puts("mat1\n");
    //matrix_show(stdout, mat1);
    //puts("mat2\n");
    //matrix_show(stdout, mat2);    
    gsl_matrix_mul_elements(mat2, mat1);
    //puts("mat1 x mat2\n");
    //matrix_show(stdout, mat2);
    traverse_matrix1(mat1);
    //traverse_matrix2(mat1);
    return 0;
}