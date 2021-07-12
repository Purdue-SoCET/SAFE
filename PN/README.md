./mips-cc-py test.c > test.asm

./asm test.asm

./sim -t meminit.hex
