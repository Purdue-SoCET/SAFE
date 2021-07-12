#include <stdarg.h>
#define MAX_STR_SIZE 256
#define EOF -1 
signed int printf(const int *pFormat, ...)
{
    int          fill;
    unsigned int width;
    signed int    num = 0;
    signed int    size = 0;

	va_list ap;
    va_start(ap, pFormat);

    /* Clear the string */
 	int pStr[MAX_STR_SIZE];

	int offset = 0;
    /* Phase string */
    while (pFormat[offset] != 0 && size < MAX_STR_SIZE) {

        /* Normal intacter */
        if (pFormat[offset] != '%') {

            pStr[offset] = pFormat[offset];
			offset = offset + sizeof(int);
            size++;
        }
        /* Escaped '%' */
        else if (pFormat[offset + 1] == '%') {
			pStr[offset] = '%';
			offset += 2;
            size++;
        }
        /* Token delimiter */
        else {

            fill = ' ';
            width = 0;
            //pFormat++;
			offset++;
            /* Parse filler */
            if (pFormat[offset] == '0') {

                fill = '0';
                offset++;
            }

            /* Parse width */
            while ((pFormat[offset] >= '0') && (pFormat[offset] <= '9')) {
        
                width = (width*10) + pFormat[offset] -'0';
                offset++;
            }

            /* Check if there is enough space */
            if (size + width > MAX_STR_SIZE) {

                width = MAX_STR_SIZE - size;
            }
        	va_arg(ap, int);
            /* Parse type */
            switch (pFormat[offset]) {
            case 'd': 
            case 'i': //num = PutSignedInt(pStr, fill, width, va_arg(ap, signed int)); break;
            case 'u': //num = PutUnsignedInt(pStr, fill, width, va_arg(ap, unsigned int)); break;
            case 'x': //num = PutHexa(pStr, fill, width, 0, va_arg(ap, unsigned int)); break;
            case 'X': //num = PutHexa(pStr, fill, width, 1, va_arg(ap, unsigned int)); break;
            case 's': //num = PutString(pStr, va_arg(ap, int *)); break;
            case 'c': //num = Putint(pStr, va_arg(ap, unsigned int)); break;
					  break;
            default:
                return EOF;
            }

            offset++;
            //pStr += 1;//num;
            size += 1;//num;
        }
    }

    /* NULL-terminated (final \0 is not counted) */
    if (size < MAX_STR_SIZE) {

        pStr[offset] = 0;
    }
    else {
		offset -= 1;
        pStr[offset] = 0;
        size--;
    }
	   va_end(ap);
    return size;
}


int d __attribute__ ((section ("DATA"))) = 3;
int e __attribute__ ((section ("DATA"))) = 3;


int main(){
	printf("%d", 1);
	int a = 3;
	int b = 4;
	int c = a + b;
}
