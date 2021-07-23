/******************************************************************************
 * 32 bit mips simulator
 * mulicore capable, the second core starts at address 0x0200
 * all mips 32bit instructions are encoded in here
 * even the ones we don't use, although they may not be tested
 * thuroughly.
 *
 * -Eric Villasenor email evillase@gmail.com
 *
 * Added SLLV and SRLV instructions
 * -Shubham Rastogi email shubhamrastogi3111995@gmail.com
 ******************************************************************************
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <malloc.h>
#include <assert.h>
#include <sys/socket.h>
#include <netinet/in.h> 
#include <unistd.h>
#include <sys/file.h>

/* check to see if we have inline */
#if !defined __GNUC__
#define inline /**/
#endif

#if !defined CHAR_BIT
#define CHAR_BIT 8
#endif

#define TRUE        1
#define FALSE       0
#define ERROR       -1

/* maximum file extension length */
#define MAX_EXT_LENGTH    4

/* types of memory supported */
#define MEMTYPE_RAM_FILE  1
#define MEMTYPE_INTELHEX  2

/* program verison */
int version_major = 0;
int version_minor = 3;

/* define new types */
typedef unsigned char u_int8;
typedef signed char int8;
typedef unsigned short int u_int16;
typedef signed short int int16;
typedef unsigned int u_int32;
typedef signed int int32;
typedef unsigned long long u_int64;
typedef signed long long int64;

/* overflow flag */
int oflag;

/* cache coherence for ll/sc */
int ccrmw[2/* number of processors */];

/*-----------------------------------------------------------------------------
 * Error handler
 *-----------------------------------------------------------------------------
 */
void errorHandler(char *msg)
{
  fprintf(stderr, "An error occured:\n");
  fprintf(stderr, "%s\n", msg);
  fprintf(stderr, "program terminating\n\n");
  exit(1);
}

/*-----------------------------------------------------------------------------
 * 32 bit operations
 *-----------------------------------------------------------------------------
 */
/* gets selected bit field from instruction */
static u_int32 field (u_int32 i, int32 o, int32 w)
{
  return ((i & (((1 << w) - 1) << o)) >> o);
}

/* get selected bit o from word i */
static u_int32 getBit (u_int32 i, int32 o)
{
  return ((i & (1 << o)) >> o);
}

/* set selected bit o in word i */
static void setBit (u_int32 *i, int32 o)
{
  (*i) |= 1 << o;
}

/* set a range of bits in word i starting at o and
 * ending sz bits later,
 * starts from lsb and masks to msb */
static void setRange (u_int32 *i, int32 o, int32 sz)
{
  u_int32 mask = (1 << sz) -1;
  (*i) |= mask << o;
}

/* clear selected bit o from word i */
static void clrBit (u_int32 *i, int32 o)
{
  (*i) &= ~(1 << o);
}

/* clear range of bits in word i starting at o
 * and ending sz bits later */
static void clrRange (u_int32 *i, int32 o, int32 sz)
{
  u_int32 mask = (1 << sz) -1;
  (*i) &= ~(mask << o);
}

/* mask bit o in word i and or
 * with bit sequence v shifted o bits */
static void mkBit (u_int32 *i, int32 o, int32 v)
{
  *i = ((*i) & ~(1 << o)) | (v << o);
}

/* sign extent the sz'th bit in word i */
static void signExtend (int32 *i, int32 sz)
{
  if (getBit (*i, sz-1) == 1)
  {
    setRange ((u_int32 *)i, sz, 32-sz);
  }
  else
  {
    clrRange ((u_int32 *)i, sz, 32-sz);
  }
}

/* this may need to change */
/* this is a rotate */
/* this is not used */
inline u_int32 rotateRight (u_int32 val, int32 sa)
{
  u_int32 tmp = val;

  sa = sa % 32;

  val = val >> sa;
  tmp = tmp << (32-sa);
  val = val | tmp;
  return val;
}

/*-----------------------------------------------------------------------------
 * machine state declaration
 *-----------------------------------------------------------------------------
 */
#define WORD_SIZE           4             /* word size of processors */
#define NUM_REGS            32            /* number of gp registers */
#define REG_SPECIAL         200           /* special register offset */
#define NUM_INSTRUCTIONS    2048          /* max num insns to track */
//SAFE CH MEMSIZE how much
//Ask whether instrcache is same as data cache in terms of associativtiy and size
#define MEMSPACE_SIZE       0x00010000    /* this is 65536 */
#define PROCONE_BASE_ADDR   0x00000000    /* start pc for proc 0 */
#define PROCTWO_BASE_ADDR   0x00000200    /* start pc for proc 1 */
/*
SAFE
we could replace memory of sim -t -c with L2 cache of CH
it just looks for the addr and whether it is a read or write request
*/

/* cache simulator parameters, both cores must have same cache sizes */
#define HIT_ADDR            0x3100        /* where the hit count is to be written
 /*                                            MUST MATCH hitcounter.vhd address */
//valid, tag, data
//#define ICACHE_SIZE         64            /* size in bytes of I$ */
#define ICACHE_SIZE		65536 //Modified for SAFE CH L1 cache
#define ICACHE_ASSOC        1             /* I$ associativity */
//#define ICACHE_BLOCKSIZE    1             /* I$ block size in words */
#define ICACHE_BLOCKSIZE   16	//SAFE CH 16 words per block		 
#define ICACHE_NUMSETS      ICACHE_SIZE/WORD_SIZE/ICACHE_ASSOC/ICACHE_BLOCKSIZE
//valid, tag, data, dirty
//#define DCACHE_SIZE         128           /* size in bytes of D$ */
#define DCACHE_SIZE		65536 //Modified for SAFE CH L1 cache
//#define DCACHE_ASSOC        2             /* D$ associativity */
#define DCACHE_ASSOC        1             /* SAFE CH associativity */
//#define DCACHE_BLOCKSIZE    2             /* D$ block size in words */
#define DCACHE_BLOCKSIZE   16	//SAFE CH 16 words per block		 
#define DCACHE_NUMSETS      DCACHE_SIZE/WORD_SIZE/DCACHE_ASSOC/DCACHE_BLOCKSIZE
//SAFE CH has profiling params like hits, misses, hitrate, missrate
#define ICACHE    0
#define DCACHE    1

//SAFE CH has 1024 * 2^6 bytes = 64*1024 bytes
/* flag so we can include cache simulation */
int caches = 0;

/* input file and output file format */
int memtype = MEMTYPE_INTELHEX;
/* flag so we can execute program with two cores */
int multicore = 0;
/* shared memory */
//this needs SAFE change so that L2 is memory
//make this point to L2 cache in python
u_int8 *mainmem[MEMSPACE_SIZE];

/* our machine definition */
typedef struct
{
  /* registers */
  u_int32 GPR[NUM_REGS];  /* general purpose */
  u_int32 PR[NUM_REGS]; /* processor/special */
  u_int32 PC_reg;   /* program counter */
  u_int32 RMW_reg;  /* processor read modify write state for ll/sc */

  /* caches */
  /* setup as cache[index][way]*/
  /* note: caches don't really do anything at this point except keep track of hit rate
     but they can be fully operational. This only maintains tags, valid, and lru */
  u_int32 icache[ICACHE_NUMSETS][ICACHE_ASSOC];
  u_int32 i_lru[ICACHE_NUMSETS][ICACHE_ASSOC];
  u_int32 i_v[ICACHE_NUMSETS][ICACHE_ASSOC];
  u_int32 dcache[DCACHE_NUMSETS][DCACHE_ASSOC];
  u_int32 d_lru[DCACHE_NUMSETS][DCACHE_ASSOC];
  u_int32 d_v[DCACHE_NUMSETS][DCACHE_ASSOC];

  /* cache stats */
  int32 num_mem_access; /* used more to verify correct operation */
  int32 num_ihit;        /* used to find hit rate */
  int32 num_dhit;        /* used to find hit rate */

  /* name of processor */
  char name[10];

  /* instruction count statistics */
  int32 IC[NUM_INSTRUCTIONS];

  /* exceptions */
  int32 exceptions;
  /* instructions exeecuted */
  unsigned long instructions;
  /* flag to output trace */
  int16 trace;
  /* has this core halted(needed for multicore) */
  int16 halted;
} Machine;

/* cache function prototypes */
u_int32 getTag(u_int32, int);
u_int32 getIndex(u_int32, int);
void cacheAccess(Machine *, u_int32, int);


/* register numbers */
#define ZERO    (0)
#define AT      (1)
#define V0      (2)
#define V1      (3)
#define A0      (4)
#define A1      (5)
#define A2      (6)
#define A3      (7)
#define T0      (8)
#define T1      (9)
#define T2      (10)
#define T3      (11)
#define T4      (12)
#define T5      (13)
#define T6      (14)
#define T7      (15)
#define S0      (16)
#define S1      (17)
#define S2      (18)
#define S3      (19)
#define S4      (20)
#define S5      (21)
#define S6      (22)
#define S7      (23)
#define T8      (24)
#define T9      (25)
#define K0      (26)
#define K1      (27)
#define GP      (28)
#define SP      (29)
#define FP      (30)
#define RA      (31)

/* program counter */
#define PC      (NUM_REGS + 100)
/* read modify write state register */
#define RMW     (NUM_REGS + 101)

/* special registers
 * not really used but
 * some are kept track of.
 * *NOTE* these are not specific
 * to mips, they just happen to be,
 * if you need mips specific you must
 * implement them */
#define EPC     (REG_SPECIAL + 1)
#define EHBR    (REG_SPECIAL + 2)
#define CAUSE   (REG_SPECIAL + 3)
#define STATUS  (REG_SPECIAL + 4)
#define PTBR    (REG_SPECIAL + 5)

/* mips exceptions */
#define EXC_INT             0
#define EXC_ADEL            4
#define EXC_ADES            5
#define EXC_IBE             6
#define EXC_DBE             7
#define EXC_SYS             8
#define EXC_BP              9
#define EXC_RI              10
#define EXC_CPU             11
#define EXC_OV              12
#define EXC_TR              13

/* exceptions */
#define EXC_RESET           1
//#define EXC_UNALIGNED_PC    2
//#define EXC_UNALIGNED_LW    3
//#define EXC_UNALIGNED_SW    4
#define EXC_UNIMP_INSTR     666

/* privilage violation */
//#define EXC_PRIV_VIOLATE    6
//#define EXC_TLB_MISS        7
//#define EXC_ACCESS_VIOLATE  8
//#define EXC_READ_FAULT      9
//#define EXC_WRITE_FAULT     10
//#define EXC_EXECUTE_FAULT   11
//#define EXC_SYSCALL         12
//#define EXC_EXTERNAL        13

/* get exception names */
const char *excName (int32 exc)
{
  switch (exc)
  {
    case EXC_INT:
      return "Interrupt";
    case EXC_ADEL:
      return "Load from illegal address";
    case EXC_ADES:
      return "Store to illegal address";
    case EXC_IBE:
      return "Bus error on insn fetch";
    case EXC_DBE:
      return "Bus error on data reference";
    case EXC_SYS:
      return "syscall insn executed";
    case EXC_BP:
      return "break insn executed";
    case EXC_RI:
      return "Reserved insn";
    case EXC_CPU:
      return "Coprocessor missing";
    case EXC_OV:
      return "Arithmetic overflow";
    default:
      return "Unknown";
  }
}

/* get special reg name */
/* again not really used but i left
 * it in for giggles */
const char *pRegName (int32 rd)
{
  switch (rd)
  {
    case EPC:
      return "EPC";
    case EHBR:
      return "EHBR";
    case CAUSE:
      return "CAUSE";
    case STATUS:
      return "STATUS";
    case PTBR:
      return "PTBR";
    default:
      return "REG??";
  }
}

/* all the mips instructions
 * we have.
 * because some instructions use
 * funct and and have an op of zero
 * if the op was zero i logically ored
 * it with the funct shifted 4 bits
 * thus SRL is 0x020 and so on. */

/* for the new branch instructions,
 * op is always 1, and rt changes,
 * so I shifted rt by 4 and added op
 * -Shubham Rastogi */
const char *opName (int32 op)
{
  switch (op)
  {
    case 0x000:
      return "SLL";
    case 0x001:
      return "BLTZ";
    case 0x011:
      return "BGEZ";
    case 0x020:
      return "SRL";
    case 0x040:
      return "SLLV";
    case 0x060:
      return "SRLV";
    case 0x080:
      return "JR";
    case 0x200:
      return "ADD";
    case 0x210:
      return "ADDU";
    case 0x220:
      return "SUB";
    case 0x230:
      return "SUBU";
    case 0x240:
      return "AND";
    case 0x250:
      return "OR";
    case 0x260:
      return "XOR";
    case 0x270:
      return "NOR";
    case 0x2a0:
      return "SLT";
    case 0x2b0:
      return "SLTU";
    case 0x002:
      return "J";
    case 0x003:
      return "JAL";
    case 0x004:
      return "BEQ";
    case 0x005:
      return "BNE";
    case 0x006:
      return "BLEZ";
    case 0x007:
      return "BGTZ";
    case 0x008:
      return "ADDI";
    case 0x009:
      return "ADDIU";
    case 0x00a:
      return "SLTI";
    case 0x00b:
      return "SLTIU";
    case 0x00c:
      return "ANDI";
    case 0x00d:
      return "ORI";
    case 0x00e:
      return "XORI";
    case 0x00f:
      return "LUI";
    case 0x023:
      return "LW";
    case 0x024:
      return "LBU";
    case 0x025:
      return "LHU";
    case 0x028:
      return "SB";
    case 0x029:
      return "SH";
    case 0x02b:
      return "SW";
    /* same opcode used for TSL and LL */
    case 0x030:
      //return "TSL";
      return "LL";
    /* only used with LL, if using TSL comment out or add flag */
    case 0x038:
      return "SC";
    case 0x03f:
      return "HALT";
    case 0x101:
      return "BLTZAL";
    case 0x111:
      return "BGEZAL";
    default:
      return "????";
  }
}

/*-----------------------------------------------------------------------------
 * machine operations
 *-----------------------------------------------------------------------------
 */
/* create a machine and give it a name
 * like fido... */
Machine * machineCreate(char *name)
{
  /* get zero initialized memory for our processor */
  Machine *m = calloc(1, sizeof (Machine));
  /* set exceptions */
  m->PR[CAUSE - REG_SPECIAL] = EXC_RESET;
  /* set name */
  strcpy(m->name, name);
  /* return machine */
  return m;
}

/* check if the memory address is valid */
u_int8 isMemoryValid (u_int32 addr)
{
  int i = 0;
  int tmp = 0;

  /* check bytes */
  for (i = 0; i < WORD_SIZE; i++)
  {
    /* check to see if we fall off the memory cliff
     * and if the space is valid*/
    if ((addr + i) >= (MEMSPACE_SIZE) || mainmem[addr + i] == NULL)
    {
      tmp++;
    }
  }

  /* these 4 bytes are invalid */
  if (tmp == WORD_SIZE)
  {
    return FALSE;
  }

  /* memory at address is ok */
  return TRUE;
}
/* get a byte from an address location */
u_int8 getByte (u_int32 addr)
{
  /* make sure we didn't lose memory */
  assert (mainmem != NULL);
  /* make sure we didn't fall off memory cliff */
  if (addr >= MEMSPACE_SIZE)
  {
    errorHandler ("The program has exceeded the allowable address space in getByte.\n");
  }
  /* get byte */
  if (mainmem[addr] == NULL)
  {
    return 0;
  }
  FILE * send_L1_to_mem;
  send_L1_to_mem = fopen("send_L1_to_mem","w");
  while(!flock(send_L1_to_mem, LOCK_EX));
  fprintf(send_L1_to_mem, "addr: %d", addr);
  while(!flock(send_L1_to_mem, LOCK_UN));
  fclose(send_L1_to_mem);
  FILE * recv_mem_to_L1;
  recv_mem_to_L1 = fopen("recv_mem_to_L1", "r");
  while(!flock(recv_mem_to_L1, LOCK_EX));
  int val1;
  fscanf(recv_mem_to_L1, "val: %d", &val1);
  while(!flock(recv_mem_to_L1, LOCK_UN));
  fclose(recv_mem_to_L1);
  return val1; 
  /* return byte */
}

/* get a word from memory */
u_int32 getWord (u_int32 addr)
{
  u_int8 word[WORD_SIZE];
  int i;

  assert (mainmem != NULL);
  /* check address */
  if (addr % WORD_SIZE)
  {
    printf ("Unaligned access of address %08X\n", addr);
    /* align if broken */
    addr &= 0xfffffffc;
  }
  /* get bytes in word */
  for (i = 0; i < WORD_SIZE; i++)
  {
    word[i] = getByte(addr + i);
  }
  for (int i = 0; i < MEMSPACE_SIZE; i++){
	if (mainmem[i] != NULL)
  	{
		if (i % 4 == 0) printf("\n");
  		printf("%04x ",*mainmem[i]);
	}
	else{
	    //printf("NULL");
	}
  }
  //printf("\n");
  /* pack bytes bigendian and return */
  return ((word[0] << 24) | (word[1] << 16) | (word[2] << 8) | word[3]);
}

/* set a byte of memory to a value */
void setByte (u_int32 addr, u_int8 val)
{
  assert (mainmem != NULL);
  /* check memory cliff again */
  if (addr >= (MEMSPACE_SIZE))
  {
    /* this will exit the program */
    errorHandler ("Address space out of range.\n");
  }

  /* make some space */
  if (mainmem[addr] == NULL)
  {
    /* get 0 inititalized virtual memory */
    mainmem[addr] = calloc(1, sizeof (u_int8));
    /* check for out of virtual memory */
    if (mainmem[addr] == NULL)
    {      
      /* oh well */
      errorHandler("Failed to allocate virtual memory in setByte\n");
    }
  }
  /* set the value in memory */
  *(mainmem[addr]) = val;
  FILE * send_L1_to_mem;
  send_L1_to_mem = fopen("sw_ask_L1_to_mem", "w");
  while(!flock(send_L1_to_mem,LOCK_EX));
  fprintf(send_L1_to_mem, "addr: %d val: %d", addr, val);
  while(!flock(send_L1_to_mem,LOCK_UN));
  fclose(send_L1_to_mem);
}

/* set a word of memory to a value */
/*
void setWord (Machine *m, u_int32 addr, u_int32 val)
{
  int i;

  assert (m != NULL);

  assert (mainmem != NULL);


  if (addr % WORD_SIZE)
  {
    printf ("Unaligned access of address %08X\n", addr);
   
    addr &= 0xfffffffc;
  }
  //FILE * fp_w = fopen("value_r","wb");
  //FILE * fl_w = fopen("lock_r","wb");
 
  u_int8 * b_val;
  //fscanf(fp_w,"%d",1);
  //fp_w.close();
  for (i = WORD_SIZE-1; i >= 0; i--)
  {

	*b_val = ((val >> (i*8)) & 0x000000ff);
    //fwrite(b_val, sizeof(u_int8), addr + (WORD_SIZE-1-i), fp_w);
	setByte(addr + (WORD_SIZE-1-i), ((val >> (i*8)) & 0x000000ff));
  }
  //FILE * fl_w = fopen("lock_r","wb");
  //fscanf(fl_w,"%d",1);
  //fl_w.close();
  //fp_w.close();

  if (m->trace)
  {
    printf ("\t[%08X] <-- %08X\n", addr, val);
  }
}
*/
/* set a word of memory to a value */
void setWord (Machine *m, u_int32 addr, u_int32 val)
{
  int i;
  /* check machine */
  assert (m != NULL);
  /* check main mem */
  assert (mainmem != NULL);

  /* check addr */
  if (addr % WORD_SIZE)
  {
    printf ("Unaligned access of address %08X\n", addr);
    /* align addr if broken */
    addr &= 0xfffffffc;
  }

  /* set memory value */
  for (i = WORD_SIZE-1; i >= 0; i--)
  {
    /* byte by byte */
    /* remember big endian
     * thus the index manipulation.
     * the byte and shift amount are inversly related */
    setByte(addr + (WORD_SIZE-1-i), ((val >> (i*8)) & 0x000000ff));
  }
  /* if we are tracing print out what
   * we did */
  if (m->trace)
  {
    printf ("\t[%08X] <-- %08X\n", addr, val);
  }
  for (int i = 0; i < MEMSPACE_SIZE; i++){
	if (mainmem[i] != NULL)
  	{
		if (i % 4 == 0) printf("\n");
  		printf("%04x ",*mainmem[i]);
	}
	else{
	    //printf("NULL ");
	}
  }
  //printf("\n");
}

/* get a register value from a machine */
u_int32 getReg (Machine *m, unsigned int num)
{
  /* make sure registers are relevant */
  assert (   num < NUM_REGS
          || num == PC
          || num == RMW
          || (num >= REG_SPECIAL && num <= REG_SPECIAL + NUM_REGS));
  /* and we have a machine */
  assert (m != NULL);
  /* reg 0 test */
  assert (m->GPR[ZERO] == 0);

  /* get the register */
  if (num == ZERO)
  {
    return 0;
  }
  /* get general purpose registers */
  if (num < NUM_REGS)
  {
    return m->GPR[num];
  }
  /* get program counter */
  else if (num == PC)
  {
    return m->PC_reg;
  }
  /* get rmw state */
  else if (num == RMW)
  {
    return m->RMW_reg;
  }
  /* get special regs */
  else if (num >= REG_SPECIAL && num <= REG_SPECIAL + NUM_REGS)
  {
    return m->PR[num - REG_SPECIAL];
  }
  /* its bad if we get here. i mean it, really */
  return 0;
}

/* set a register to a value */
void setReg (Machine *m, unsigned int num, u_int32 val)
{
  /* make sure registers are relevant */
  assert (   num < NUM_REGS
          || num == PC
          || num == RMW
          || (num >= REG_SPECIAL && num <= REG_SPECIAL + NUM_REGS));
  /* and we have a machine */
  assert (m != NULL);

  /* user wants to see whats going on */
  if (m->trace)
  {
    /* print reg */
    if (num == PC)
    {
      printf ("\tPC <-- %08X\n", val);
    }
    else if (num == RMW)
    {
      printf ("\tRMW <-- %08X\n", val);
    }
    else if (num < NUM_REGS)
    {
      printf ("\tR%d <-- %08X\n", num, val);
    }
    else if (num >= REG_SPECIAL && num < REG_SPECIAL + NUM_REGS)
    {
      printf ("\t%s <-- %08X\n", pRegName (num), val);
    }
    else
    {
      printf ("\ttrying to set unknown register\n");
    }
  }

  /* maintain zero register */
  if (num == ZERO)
  {
    return;
  }

  /* set registers */
  if (num == PC)
  {
    m->PC_reg = val;
  }
  else if (num == RMW)
  {
    m->RMW_reg = val;
  }
  else if (num < NUM_REGS)
  {
    m->GPR[num] = val;
  }
  else if (num >= REG_SPECIAL && num < REG_SPECIAL + NUM_REGS)
  {
    m->PR[num - REG_SPECIAL] = val;
  }

}

/* load a program into main memory */
u_int32 mainmemLoadProgram (Machine *m, const char *filename)
{
  u_int32 lines = 0;    /* lines/words loaded */
  u_int32 addr = 0;   /* address counter */
  u_int32 val = 0;    /* data loaded */
  int i, j;     /* counter vars */
  char fileext[MAX_EXT_LENGTH]; /* what file type to use */
  char* hexext = "hex";   /* default */
  char* ramext = "ram";   /* legacy */
  char dummy[100];    /* place holder for junk */
  FILE *fp = NULL;    /* file we are loading */

  /* check for machine */
  assert (m != NULL);

  /* open file */
  fp = fopen (filename, "r");
  /* check file */
  if (!fp)
  {
    fprintf (stderr, "Failed to load %s\n", filename);
    /* zero is error return for this function */
    return 0;
  }
  /* check file extension for ram hex mif */
  for (j= 0, i = 0; j < strlen(filename)-1; j++)
  {
    /* found start of extension */
    if (filename[j] == '.')
    {
      /* jump past the period */
      j++;
      break;
    }
  }
  /* check file extension length */
  if (strlen(filename) - j >= MAX_EXT_LENGTH)
  {
    fprintf(stderr, "Bad extention on file: %s\n\n", filename+j);
    return 0;
  }
  /* check extension don't check mif */
  strcpy(fileext, filename+j);
  if (!strcmp(fileext, hexext))
  {
    memtype = MEMTYPE_INTELHEX;
  }
  else if (!strcmp(fileext, ramext))
  {
    memtype = MEMTYPE_RAM_FILE;
  }
  else
  {
    fprintf(stderr, "Unrecognized file extension: %s\n", fileext);
    return 0;
  }

  /* load program ram file*/
  while ((memtype == MEMTYPE_RAM_FILE) && fscanf (fp, "%8X %[/] %8X%[^\n]\n", &addr, dummy, &val, dummy) >= 3)
  {
    /* count lines */
    lines++;
    /* set word in memory */
    setWord (m, addr, val);
  }

  /* load program hex file*/
  while ((memtype == MEMTYPE_INTELHEX) && fscanf (fp, "%[:]%02X%04X%02X%08X%[^\n]\n", dummy, &i, &addr, &j, &val, dummy) >= 5)
  {
    /* this is the last line of file, not data */
    if (j == 1)
    {
      break;
    }
    /* count lines */
    lines++;
    /* set word in memory */
    /* because asm divided by WORD SIZE
     * we need to multiply the address
     * by WORD SIZE so we can get
     * back to the right address */
    /* asm did this because the internal
     * fpga memory is allocated in such
     * a way that it would be wasteful
     * if we did not divide */
    setWord (m, addr*i/* multiply to get origional address */, val);
  }

  /* close file */
  fclose (fp);
  /* say done */
  printf ("%u words loaded from %s\n", lines, filename);

  /* return number of words loaded */
  return lines;
}

/* dump stats and memory to file */
void machineDump (Machine *m1, Machine *m2)
{
  int i = 0;    /* counter */
  int j, checksum = 0;  /* check sum */
  u_int32 addr = 0; /* address value */
  u_int32 val = 0;  /* data value */
  FILE *fp = NULL;  /* output file */
  char bytes[17];   /* 1 extra for null terminator */
  char byte[3];   /* 1 extra for null terminator */

  /* make sure we have a machine */
  assert (m1 != NULL);

  /* say done */
  printf ("Done simulating...\n\n");

  printf ("Instruction Breakdown:\n\n");

  /* are we printing out two cores */
  if (m2 != NULL && multicore)
  {
    printf ("\t\t%s\n", m1->name);
  }
  /* instruciton statistics for proc 0 */
  for (i = 0; i < NUM_INSTRUCTIONS; i++)
  {
    /* only print operations that have been run and their percentages */
    if (m1->IC[i] != 0)
    {
      printf ("\t %4s: %4d (%.2f%%)\n", opName (i), m1->IC[i],
          ((float)(m1->IC[i])*100) / ((float)m1->instructions));
    }
  }
  /* more stats for proc 0 */
  printf ("\t TOTAL: %4lu\n", m1->instructions);
  printf ("\n");
  printf ("\tPC: %08X\n", getReg (m1, PC));
  printf ("\n");


  if(caches)
  {
    printf("ICache:\n");
    printf("\t Accesses:\t%d\n",(int)m1->instructions);
    printf("\t Hits:\t\t%d\n",m1->num_ihit);
    printf("\t Hit Rate:\t%d%%\n",(100*m1->num_ihit)/((int)m1->instructions));
    printf("DCache:\n");
    printf("\t Accesses:\t%d\n",m1->num_mem_access);
    printf("\t Hits:\t\t%d\n",m1->num_dhit);
    if (m1->num_mem_access) {
      printf("\t Hit Rate:\t%d%%\n",(100*m1->num_dhit)/m1->num_mem_access);
    }
    else {
      printf("\t Hit Rate:\t0%%\n");
    }
    printf("\n");
  }

  /* only print processor regs if handling exceptions */
  if (m1->PR[CAUSE - REG_SPECIAL] != EXC_RESET)
  {
    printf ("Exceptions Encountered: %d\n", m1->exceptions);
    printf ("Processor Registers\n");
    /*for (i = 0; i < NUM_REGS; i += 4)*/
    for (i = EPC; i <= PTBR; i += 1)
    {
      printf ("%7s: %04X ", pRegName (i), getReg (m1, i - REG_SPECIAL));
      if (0 == (i-REG_SPECIAL) % 4) printf("\n");
      /*
      printf ("%7s: %04X %7s: %04X %7s: %04X %7s: %04X\n",
          pRegName (i), getReg (m1, i - REG_SPECIAL),
          pRegName (i+1), getReg (m1, i + 1 - REG_SPECIAL),
          pRegName (i+2), getReg (m1, i + 2 - REG_SPECIAL),
          pRegName (i+3), getReg (m1, i + 3 - REG_SPECIAL));
          */
    }
    printf ("\n");
  }

  /* now general registers for proc 0 */
  printf ("General Purpose Registers:\n");
  for (i = 0; i < NUM_REGS; i += 4)
  {
    printf ("\tR%2d: %08X\tR%2d: %08X\tR%2d: %08X\tR%2d: %08X\n",
        i, getReg (m1, i),
        i+1, getReg (m1, i+1),
        i+2, getReg (m1, i+2),
        i+3, getReg (m1, i+3));
  }
  /* now print state of proc 1 */
  if (m2 != NULL && multicore)
  {
    /* print name of processor */
    printf ("\n\n\t\t%s\n", m2->name);
    /* print instruction break down */
    for (i = 0; i < NUM_INSTRUCTIONS; i++)
    {
      /* only print operations that have been run and their percentages */
      if (m2->IC[i] != 0)
      {
        printf ("\t %4s: %4d (%.2f%%)\n", opName (i), m2->IC[i],
            ((float)(m2->IC[i])*100) / ((float)m2->instructions));
      }
    }
    printf ("\t TOTAL: %4lu\n", m2->instructions);
    printf ("\n");
    printf ("\tPC: %08X\n", getReg (m2, PC));
    printf ("\n");
    /* only print processor regs if handling exceptions */
    if (m2->PR[CAUSE - REG_SPECIAL] != EXC_RESET)
    {
      printf ("Exceptions Encountered: %d\n", m2->exceptions);
      printf ("Processor Registers\n");
      /*for (i = 0; i < NUM_REGS; i += 4)*/
      for (i = EPC; i <= PTBR; i += 1)
      {
        printf ("%7s: %04X ", pRegName (i), getReg (m1, i - REG_SPECIAL));
        if (0 == (i-REG_SPECIAL) % 4) printf("\n");
        /*
        printf ("%7s: %04X %7s: %04X %7s: %04X %7s: %04X\n",
            pRegName (i), getReg (m2, i + REG_SPECIAL),
            pRegName (i+1), getReg (m2, i + 1 + REG_SPECIAL),
            pRegName (i+2), getReg (m2, i + 2 + REG_SPECIAL),
            pRegName (i+3), getReg (m2, i + 3 + REG_SPECIAL));
            */
      }
      printf ("\n");
    }
    /* now general registers */
    printf ("General Purpose Registers:\n");
    for (i = 0; i < NUM_REGS; i += 4)
    {
      printf ("\tR%2d: %08X\tR%2d: %08X\tR%2d: %08X\tR%2d: %08X\n",
          i, getReg (m2, i),
          i+1, getReg (m2, i+1),
          i+2, getReg (m2, i+2),
          i+3, getReg (m2, i+3));
    }
  }

  /* open output file */
  if (memtype == MEMTYPE_INTELHEX)
  {
    fp = fopen("memsim.hex", "w");
  }
  else
  {
    fp = fopen("memsim.ram", "w");
  }

  /* write values of memory addresses */
  for (addr = 0; addr < MEMSPACE_SIZE; addr += WORD_SIZE)
  {
    if (!isMemoryValid (addr))
    {
      continue;
    }

    val = getWord (addr);
    /* fix to have tb_cpu
     * and sim output same file
     * have tb_cpu keep track of memory addresses
     * touched and remove this if/continue
     */
    if (val == 0)
    {
      continue;
    }

    /* compute checksum */
    sprintf(bytes, "%02X%04X%02X%08X", 4, ((addr/WORD_SIZE)& (MEMSPACE_SIZE-1)), 0, val);
    for (checksum = 0, j = 0, i = 0; i <strlen(bytes)-1; i++)
    {
      byte[0] = bytes[i++];
      byte[1] = bytes[i];
      byte[2] = '\0';
      sscanf (byte, "%2X", &j);
      /* add fields 2-5 together in 2digit invervals */
      checksum += j;
    }
    /* two ways to do this
     * subtract sum from 0x100
     * or invert and add 1
     */
    /* keep only lsb */
    checksum &= 0xff;
    /* invert the result */
    checksum = ~checksum;
    /* add 1 to get check sum */
    checksum += 1;
    /* again lsb is what we want */
    checksum &= 0xff;
    if (memtype == MEMTYPE_INTELHEX)
    {
      /* print intel hex format to file */
      fprintf (fp, ":%02X%04X%02X%08X%02X\n", WORD_SIZE, ((addr/WORD_SIZE)&(MEMSPACE_SIZE-1)), 0, val, checksum);
    }
    else
    {
      /* print .ram format to file */
      fprintf (fp, "%08X %08X\n", addr, val);
    }
  }
  /* print footer for intel hex */
  if (memtype == MEMTYPE_INTELHEX)
  {
    fprintf (fp, ":00000001FF\n");
  }
  /* close output */
  fclose (fp);
}

/*-----------------------------------------------------------------------------
 * executing operations
 *-----------------------------------------------------------------------------
 */

/* this is unused, and i can't think of a use for it */
/* besides putting crap back in the buffer */
void magic (Machine *m, u_int32 op, u_int32 val)
{
  if (op == 0)
  {
    putchar (val);
  }
  else if (op == 1)
  {
    setReg (m, val, getchar());
  }
}

/* set exceptions */
void exception (Machine *m, int type)
{
  if (m->trace)
  {
    printf ("\t[Exception %s]\n", excName(type));
    setReg (m, CAUSE, type);
    setReg (m, EPC, getReg (m, PC));
    setReg (m, PC, getReg (m, EHBR));
    m->exceptions++;
  }
  m->halted = TRUE;
}

/* execute the program */
u_int32 execute (Machine *m1, Machine *m2)
{
  /* current machine being executed */
  Machine *m = NULL;
  u_int32 instr;
  /* decoded instruction parts for */
  /* rtype */
  u_int32 op;
  u_int32 rs;
  u_int32 rt;
  u_int32 rd;
  u_int32 shamt;
  u_int32 funct;
  /* itype */
  u_int32 imm;
  /* jtype */
  u_int32 addr;
  /* offset */
  int32 offset;
  /* temporary vars */
  int32 t_os;
  int32 t_rs;
  int32 t_rt;
  /* halt */
  int halting = FALSE;
  /* split execution time between
   * processors */
  u_int32 timeshare = 0;

  /* loop and execute instructions */
  while (!halting)
  {
    /* program counter and next program counter
     * addresses */
    u_int32 pc;
    u_int32 npc;
    /* temps */
    u_int32 t_addr;
    u_int32 t_npc;

    /* setup processors */
    if (multicore)
    {
      /* need to switch cores when done */
      if (m && m->halted)
      {
        /* reset time so we hit next if block */
        timeshare = 0;
      }
      /* or when time is up do a switch */
      if (timeshare == 0)
      {
        /* get new timeshare */
        timeshare = (rand() & 0x03);
        /* switch processors */
        if (m == m1)
        {
          m = m2; /* switch to m2 */
          if (m2->halted)
          {
            m = m1; /* m2 halted switch back to m1 */
          }
        }
        else if (m == m2)
        {
          m = m1; /* switch to m1 */
          if (m1->halted)
          {
            m = m2; /* m1 halted switch back to m2 */
          }
        }
      }
      /* error checking */
      if (m1->halted && m2->halted)
      {
        /* yea this is bad, gremlins in the machines... */
        fprintf (stderr, "Both machines halted and we are still executing\n");
      }

      /* first time in loop */
      if (m == NULL)
      {
        m = m1; /* start on m1 arbitrary choice */
      }
    }
    else
    {
      m = m1; /* no multicore */
    }

    /* fetch */
    pc = getReg (m, PC);
    /* make sure we don't go over our address space */
    /* wraps memory around to 0 when it reaches the cliff */
    npc = ((pc+WORD_SIZE) >= (MEMSPACE_SIZE) ?
        ((pc+WORD_SIZE) == (MEMSPACE_SIZE) ? 0 :
        ((pc+WORD_SIZE)&(MEMSPACE_SIZE-1))) : (pc+WORD_SIZE));

    /* let user know what processor and
     * what is happening */
    if (m->trace)
    {
      printf ("\n%08X(%s): ", pc, m->name);
    }
    /* undecoded instruction */
    instr = getWord (pc);

    /* reset decoded instruction */
    op = rs = rt = rd = shamt = funct = 0;
    imm = addr = 0;

    /* decode insntruction */
    op = field (instr, 26, 6);
    rs = field (instr, 21, 5);
    rt = field (instr, 16, 5);
    rd = field (instr, 11, 5);
    shamt = field (instr, 6, 5);
    funct = field (instr, 0, 6);
    imm = field (instr, 0, 16);
    addr = field (instr, 0, 26);

    /* sign extended immediate */
    offset = (int32)imm;
    signExtend (&offset, 16);

    /* instruction statistic counters */
    if (op == 0)
    {
      m->IC[funct<<4]++; /* remember what we do for rtypes */
    }
    else if (op == 1) /* For branch types we shift rt by 4 and add op (which is 1) */
    {
      m->IC[(rt<<4)+op]++;
    }
    else
    {
      m->IC[op]++;
    }
    /* count one more instruction executed */
    m->instructions++;

    /* reset overflow flag */
    oflag = FALSE;

    /* Do an icache access */
    cacheAccess(m,pc,ICACHE);

    /* execute */
    switch (op)
    {
      case 0x0: /* r-type */
        switch (funct)
        {
          case 0x00: /* sll */
            if (m->trace)
            {
              printf ("%08X SLL R%d, R%d, %d\n", instr, rd, rs, shamt);
            }
            setReg (m, PC, npc);
            setReg (m, rd, getReg (m, rs) << shamt);
            break;
          case 0x02: /* srl */
            if (m->trace)
            {
              printf ("%08X SRL R%d, R%d, %d\n", instr, rd, rs, shamt);
            }
            setReg (m, PC, npc);
            setReg (m, rd, getReg (m, rs) >> shamt);
            break;
          case 0x04: /* sllv */
            if(m->trace)
            {
              printf ("%08X SLLV R%d, R%d, R%d\n", instr, rd, rs, rt);
            }
            setReg (m, PC, npc);
            setReg (m, rd, getReg (m, rt) << field (getReg (m, rs), 0, 5));
            break;
          case 0x06: /* srlv */
            if(m->trace)
            {
              printf("%08X SRLV R%d, R%d, R%d\n", instr, rd, rs, rt);
            }  
            setReg (m, PC, npc);
            setReg (m, rd, getReg (m, rt) >> field (getReg (m, rs), 0, 5));
            break;
          case 0x08: /* jr */
            t_addr = getReg (m, rs);

            if (m->trace)
            {
              printf ("%08X JR R%d\n", instr, rs);
            }

            if (t_addr % WORD_SIZE)
            {
              exception (m, EXC_ADEL);
            }
            else
            {
              setReg (m, PC, t_addr);
            }
            break;
          case 0x20: /* add */
            t_rs = (int32)getReg (m, rs);
            t_rt = (int32)getReg (m, rt);

            /* check for overflow */
            if (((t_rs ^ t_rt) | (((t_rs ^ (~(t_rs ^ t_rt)
                          & (1 << (sizeof(int32)*CHAR_BIT-1)))) + t_rt) ^ t_rt))
                >= 0)
            {
              oflag = 1;
            }

            if (m->trace)
            {
              printf ("%08X ADD R%d, R%d, R%d\n", instr, rd, rs, rt);
            }
            if (oflag)
            {
              exception (m, EXC_OV);
            }
            else
            {
              setReg (m, PC, npc);
              setReg (m, rd, t_rs + t_rt);
            }
            break;
          case 0x21: /* addu */
            t_rs = (int32)getReg (m, rs);
            t_rt = (int32)getReg (m, rt);

            /* check for overflow */
            if (((t_rs ^ t_rt) | (((t_rs ^ (~(t_rs ^ t_rt)
                          & (1 << (sizeof(int32)*CHAR_BIT-1)))) + t_rt) ^ t_rt))
                >= 0)
            {
              oflag = 1;
            }
            /* if there is overflow no problem just set flag and
             * continue */

            if (m->trace)
            {
              printf ("%08X ADDU R%d, R%d, R%d\n", instr, rd, rs, rt);
            }
            setReg (m, PC, npc);
            setReg (m, rd, t_rs + t_rt);
            break;
          case 0x22: /* sub */
            t_rs = (int32)getReg (m, rs);
            t_rt = (int32)getReg (m, rt);

            /* check for overflow */
          //  if (((t_rs ^ t_rt) | (((t_rs ^ (~(t_rs ^ t_rt)
          //                & (1 << (sizeof(int32)*CHAR_BIT-1)))) - t_rt) ^ t_rt))
          //      < 0)
		  if (((t_rs < 0) && (t_rt >= 0) && ((t_rs - t_rt) >= 0)) || 
			   ((t_rs >= 0) && (t_rt < 0) && ((t_rs - t_rt) < 0)))  // Neg - Pos results in Pos (overflow) or Pos - Neg results in Neg (overflow)	// ALU Port B select mux.
            {
              oflag = 1;
            }

            if (m->trace)
            {
              printf ("%08X SUB R%d, R%d, R%d\n", instr, rd, rs, rt);
            }
            if (oflag)
            {
              exception (m, EXC_OV);
            }
            else
            {
              setReg (m, PC, npc);
              setReg (m, rd, t_rs - t_rt);
            }
            break;
          case 0x23: /* subu */
            t_rs = (int32)getReg (m, rs);
            t_rt = (int32)getReg (m, rt);

            /* check for overflow */
            if (((t_rs ^ t_rt) | (((t_rs ^ (~(t_rs ^ t_rt)
                          & (1 << (sizeof(int32)*CHAR_BIT-1)))) - t_rt) ^ t_rt))
                < 0)
            {
              oflag = 1;
            }
            /* if there is overflow no problem just set flag and
             * continue */

            if (m->trace)
            {
              printf ("%08X SUBU R%d, R%d, R%d\n", instr, rd, rs, rt);
            }
            setReg (m, PC, npc);
            setReg (m, rd, t_rs - t_rt);
            break;
          case 0x24: /* and */
            if (m->trace)
            {
              printf ("%08X AND R%d, R%d, R%d\n", instr, rd, rs, rt);
            }
            setReg (m, PC, npc);
            setReg (m, rd, getReg (m, rs) & getReg (m, rt));
            break;
          case 0x25: /* or */
            if (m->trace)
            {
              printf ("%08X OR R%d, R%d, R%d\n", instr, rd, rs, rt);
            }
            setReg (m, PC, npc);
            setReg (m, rd, getReg (m, rs) | getReg (m, rt));
            break;
          case 0x26: /* xor */
            if (m->trace)
            {
              printf ("%08X XOR R%d, R%d, R%d\n", instr, rd, rs, rt);
            }
            setReg (m, PC, npc);
            setReg (m, rd, getReg (m, rs) ^ getReg (m, rt));
            break;
          case 0x27: /* nor */
            if (m->trace)
            {
              printf ("%08X NOR R%d, R%d, R%d\n", instr, rd, rs, rt);
            }
            setReg (m, PC, npc);
            setReg (m, rd, ~(getReg (m, rs) | getReg (m, rt)));
            break;
          case 0x2a: /* slt */
            t_rs = (int32)getReg (m, rs);
            t_rt = (int32)getReg (m, rt);

            if (m->trace)
            {
              printf ("%08X SLT R%d, R%d, R%d\n", instr, rd, rs, rt);
            }
            setReg (m, PC, npc);
            /* signed compare */
            setReg (m, rd, (t_rs < t_rt) ? 1 : 0);
            break;
          case 0x2b: /* sltu */
            if (m->trace)
            {
              printf ("%08X SLTU R%d, R%d, R%d\n", instr, rd, rs, rt);
            }
            setReg (m, PC, npc);
            /* unsigned compare */
            setReg (m, rd, ((u_int32)getReg (m, rs) < (u_int32)getReg (m, rt)) ? 1 : 0);
            break;
          default:
            exception (m, EXC_UNIMP_INSTR);
            printf ("Illegal rtype instruction: %08X.\n", instr);
            return 0;
            break;
        }
        break;
      case 0x1: /* b type */
        switch (rt)
        {
          case 0x00: /* bltz */
            t_addr = npc + (offset << 2);
            if(m->trace)
            {
              printf ("%08X BLTZ R%d, R0, %d\n", instr, rs, t_addr);
            }
            /* new to wrap address maybe FIXME */
            t_addr = ((t_addr) >= (MEMSPACE_SIZE) ?
              ((t_addr) == (MEMSPACE_SIZE) ? 0 :
              ((t_addr)&(MEMSPACE_SIZE-1))) : (t_addr));
            /* set pc */
            if ((int) getReg (m, rs) < 0)
            {
              setReg (m, PC, t_addr);
            }
            else
            {
              setReg (m, PC, npc);
            }
            break;
          case 0x01: /* bgez */
            t_addr = npc + (offset << 2);
            if(m->trace)
            {
              printf ("%08X BGEZ R%d, R0, %d\n", instr, rs, t_addr);
            }
            /* new to wrap address maybe FIXME */
            t_addr = ((t_addr) >= (MEMSPACE_SIZE) ?
              ((t_addr) == (MEMSPACE_SIZE) ? 0 :
              ((t_addr)&(MEMSPACE_SIZE-1))) : (t_addr));
            /* set pc */
            if ((int) getReg (m, rs) >= 0)
            {
              setReg (m, PC, t_addr);
            }
            else
            {
              setReg (m, PC, npc);
            }
            break;
          case 0x10: /* bltzal */
            t_addr = npc + (offset << 2);
            if(m->trace)
            {
              printf ("%08X BLTZAL R%d, R0, %d\n", instr, rs, t_addr);
            }
            /* new to wrap address maybe FIXME */
            t_addr = ((t_addr) >= (MEMSPACE_SIZE) ?
              ((t_addr) == (MEMSPACE_SIZE) ? 0 :
              ((t_addr)&(MEMSPACE_SIZE-1))) : (t_addr));
            /* set pc */
            if ((int) getReg (m, rs) < 0)
            {
              setReg (m, PC, t_addr);
              setReg (m, RA, npc);
            }
            else
            {
              setReg (m, PC, npc);
            }
            break;
          case 0x11: /* bgezal */
            t_addr = npc + (offset << 2);
            if(m->trace)
            {
              printf ("%08X BGEZAL R%d, R0, %d\n", instr, rs, t_addr);
            }
            /* new to wrap address maybe FIXME */
            t_addr = ((t_addr) >= (MEMSPACE_SIZE) ?
              ((t_addr) == (MEMSPACE_SIZE) ? 0 :
              ((t_addr)&(MEMSPACE_SIZE-1))) : (t_addr));
            /* set pc */
            if ((int) getReg (m, rs) >= 0)
            {
              setReg (m, PC, t_addr);
              setReg (m, RA, npc);
            }
            else
            {
              setReg (m, PC, npc);
            }
            break;

        }
        break;
      case 0x2: /* j jtype */
        t_npc = field (npc, 28, 4) << 28;
        t_addr = (t_npc | (addr << 2));

        if (m->trace)
        {
          printf ("%08X J %08X\n", instr, t_addr);
        }
        /* new to wrap address maybe FIXME */
        t_addr = ((t_addr) >= (MEMSPACE_SIZE) ?
            ((t_addr) == (MEMSPACE_SIZE) ? 0 :
            ((t_addr)&(MEMSPACE_SIZE-1))) : (t_addr));
        /* set pc to npc */
        setReg (m, PC, t_addr);
        break;
      case 0x3: /* jal jtype */
        t_npc = field (npc, 29, 3) << 28;
        t_addr = (t_npc | (addr << 2));

        if (m->trace)
        {
          printf ("%08X JAL %08X\n", instr, t_addr);
        }
        /* new to wrap address maybe FIXME */
        t_addr = ((t_addr) >= (MEMSPACE_SIZE) ?
            ((t_addr) == (MEMSPACE_SIZE) ? 0 :
            ((t_addr)&(MEMSPACE_SIZE-1))) : (t_addr));
        /* set pc to jump address */
        setReg (m, PC, t_addr);
        /* set return address to npc */
        setReg (m, RA, npc);
        break;
      case 0x4: /* beq itype */
        t_addr = npc + (offset << 2);

        if (m->trace)
        {
          printf ("%08X BEQ R%d, R%d, %d\n", instr, rs, rt, t_addr);
          //printf ("%08X BEQ R%d, R%d, %d\n", instr, rt, rs, t_addr);
        }
        /* new to wrap address maybe FIXME */
        t_addr = ((t_addr) >= (MEMSPACE_SIZE) ?
            ((t_addr) == (MEMSPACE_SIZE) ? 0 :
            ((t_addr)&(MEMSPACE_SIZE-1))) : (t_addr));
        /* set pc */
        if (getReg (m, rs) == getReg (m, rt))
        {
          setReg (m, PC, t_addr);
        }
        else
        {
          setReg (m, PC, npc);
        }
        break;
      case 0x5: /* bne itype */
        t_addr = npc + (offset << 2);

        if (m->trace)
        {
          //printf ("%08X BNE R%d, R%d, %d\n", instr, rs, rt, t_addr);
          printf ("%08X BNE R%d, R%d, %d\n", instr, rs, rt, t_addr);
        }
        /* new to wrap address maybe FIXME */
        t_addr = ((t_addr) >= (MEMSPACE_SIZE) ?
            ((t_addr) == (MEMSPACE_SIZE) ? 0 :
            ((t_addr)&(MEMSPACE_SIZE-1))) : (t_addr));
        /* set pc */
        if (getReg (m, rs) != getReg (m, rt))
        {
          setReg (m, PC, t_addr);
        }
        else
        {
          setReg (m, PC, npc);
        }
        break;
      case 0x6: /* blez itype */
        t_addr = npc + (offset << 2);

        if(m->trace)
        {
          printf ("%08X BLEZ R%d, %d\n", instr, rs, t_addr);
        }
        /* new to wrap address maybe FIXME */
        t_addr = ((t_addr) >= (MEMSPACE_SIZE) ?
            ((t_addr) == (MEMSPACE_SIZE) ? 0 :
            ((t_addr)&(MEMSPACE_SIZE-1))) : (t_addr));
        /* set pc */
        if((int) getReg (m, rs) <= 0)
        {
          setReg (m, PC, t_addr);
        }
        else
        {
          setReg(m, PC, npc);
        }
        break;
        case 0x7: /* bgtz itype */
        t_addr = npc + (offset << 2);

        if(m->trace)
        {
          printf ("%08X BGTZ R%d, %d\n", instr, rs, t_addr);
        }
        /* new to wrap address maybe FIXME */
        t_addr = ((t_addr) >= (MEMSPACE_SIZE) ?
            ((t_addr) == (MEMSPACE_SIZE) ? 0 :
            ((t_addr)&(MEMSPACE_SIZE-1))) : (t_addr));
        /* set pc */
        if((int) getReg (m, rs) > 0)
        {
          setReg (m, PC, t_addr);
        }
        else
        {
          setReg(m, PC, npc);
        }
        break;
      case 0x8: /* addi itype */
        t_rs = (int32)getReg (m, rs);
        t_os = offset;

        /* check for overflow */
        if (((t_rs ^ t_os) | (((t_rs ^ (~(t_rs ^ t_os)
          & (1 << (sizeof(int32)*CHAR_BIT-1)))) + t_os) ^ t_os))
            >= 0)
        {
          oflag = 1;
        }

        if (m->trace)
        {
          printf ("%08X ADDI R%d, R%d, %d\n", instr, rt, rs, offset);
        }
        if (oflag)
        {
          exception (m, EXC_OV);
        }
        else
        {
          setReg (m, PC, npc);
          setReg (m, rt, t_rs + offset);
        }
        break;
      case 0x9: /* addiu itype */
        t_rs = (int32)getReg (m, rs);
        t_os = offset;

        /* check for overflow */
        if (((t_rs ^ t_os) | (((t_rs ^ (~(t_rs ^ t_os)
          & (1 << (sizeof(int32)*CHAR_BIT-1)))) + t_os) ^ t_os))
            >= 0)
        {
          oflag = 1;
        }

        if (m->trace)
        {
          printf ("%08X ADDIU R%d, R%d, %d\n", instr, rt, rs, offset);
        }
        setReg (m, PC, npc);
        setReg (m, rt, t_rs + offset);
        break;
      case 0xa: /* slti itype */
        t_rs = (int32)getReg (m, rs);

        if (m->trace)
        {
          printf ("%08X SLTI R%d, R%d, %d\n", instr, rt, rs, offset);
        }
        setReg (m, PC, npc);
        /* compare as signed */
        setReg (m, rt, (t_rs < offset) ? 1 : 0);
        break;
      case 0xb: /* sltiu itype */
        if (m->trace)
        {
          printf ("%08X SLTIU R%d, R%d, %d\n", instr, rt, rs, offset);
        }
        setReg (m, PC, npc);
        /* compare as unsigned */
        setReg (m, rt, (getReg (m, rs) < (u_int32)offset) ? 1 : 0);
        break;
      case 0xc: /* andi itype */
        if (m->trace)
        {
          printf ("%08X ANDI R%d, R%d, %d\n", instr, rt, rs, imm);
        }
        setReg (m, PC, npc);
        setReg (m, rt, getReg (m, rs) & imm);
        break;
      case 0xd: /* ori itype */
        if (m->trace)
        {
          printf ("%08X ORI R%d, R%d, %d\n", instr, rt, rs, imm);
        }
        setReg (m, PC, npc);
        setReg (m, rt, getReg (m, rs) | imm);
        break;
      case 0xe: /* xori itype */
        if (m->trace)
        {
          printf ("%08X XORI R%d, R%d, %d\n", instr, rt, rs, imm);
        }
        setReg (m, PC, npc);
        setReg (m, rt, getReg (m, rs) ^ imm);
        break;
      case 0xf: /* lui itype */
        if (m->trace)
        {
          printf ("%08X LUI R%d, %d\n", instr, rt, imm);
        }
        setReg (m, PC, npc);
        //setReg (m, rt, (getReg (m, rt) & 0xFFFF) | (imm << 16));
        setReg (m, rt, (imm << 16));
        break;
      case 0x23: /* lw itype */
        t_addr = getReg (m, rs) + offset;

        if (m->trace)
        {
          printf ("%08X LW R%d, %d(R%d)\n", instr, rt, offset, rs);
        }
        /* new to wrap address maybe FIXME */
        t_addr = ((t_addr) >= (MEMSPACE_SIZE) ?
            ((t_addr) == (MEMSPACE_SIZE) ? 0 :
            ((t_addr)&(MEMSPACE_SIZE-1))) : (t_addr));
        /* check alignment */
        if (t_addr % WORD_SIZE)
        {
          exception (m, EXC_ADEL);
        }
        else
        {

          setReg (m, PC, npc);
          if (m->trace)
          {
            printf ("\t[word read from %08X]\n", t_addr);
          }
          setReg (m, rt, getWord (t_addr));

          /* do a dcache access */
          cacheAccess(m,t_addr,DCACHE);

        }
        break;
      case 0x24: /* lbu itype */
        t_addr = getReg (m, rs) + offset;

        if (m->trace)
        {
          printf ("%08X LBU R%d, %d(R%d)\n", instr, rt, offset, rs);
        }
        setReg (m, PC, npc);
        /* new to wrap address maybe FIXME */
        t_addr = ((t_addr) >= (MEMSPACE_SIZE) ?
            ((t_addr) == (MEMSPACE_SIZE) ? 0 :
            ((t_addr)&(MEMSPACE_SIZE-1))) : (t_addr));
        /* print trace */
        if (m->trace)
        {
          printf ("\t[byte read from %08X]\n", t_addr);
        }
        /* FIXME may need to check endianness */
        setReg (m, rt, (u_int32)(getByte (t_addr)));
        break;
      case 0x25: /* lhu itype */
        t_addr = getReg (m, rs) + offset;

        if (m->trace)
        {
          printf ("%08X LHU R%d, %d(R%d)\n", instr, rt, offset, rs);
        }

        /* check for halfword alignment */
        /* the last bit has to be zero */
        if (t_addr & 0x00000001)
        {
          exception (m, EXC_ADEL);
        }
        else
        {
          setReg (m, PC, npc);
          if (m->trace)
          {
            printf ("\t[halfword read from %08X]\n", t_addr);
          }
          /* get the halfword and set it */
          {
            /* FIXME may need to check endianness */
            u_int32 hi = (u_int32)getByte (t_addr);
            u_int32 lo = (u_int32)getByte (t_addr+1);
            setReg (m, rt, ((hi << 8) | lo));
          }
        }
        break;
      case 0x28: /* sb itype */
        t_addr = getReg (m, rs) + offset;

        if (m->trace)
        {
          printf ("%08X SB R%d, %d(R%d)\n", instr, rt, offset, rs);
        }
        setReg (m, PC, npc);
        /* new to wrap address maybe FIXME */
        t_addr = ((t_addr) >= (MEMSPACE_SIZE) ?
            ((t_addr) == (MEMSPACE_SIZE) ? 0 :
            ((t_addr)&(MEMSPACE_SIZE-1))) : (t_addr));
        /* FIXME may need to check endianness */
        /* set byte in memory */
        setByte (t_addr, (u_int8)getReg (m, rt));
        break;
      case 0x29: /* sh itype */
        t_addr = getReg (m, rs) + offset;

        if (m->trace)
        {
          printf ("%08X SH R%d, %d(R%d)\n", instr, rt, offset, rs);
        }
        /* new to wrap address maybe FIXME */
        t_addr = ((t_addr) >= (MEMSPACE_SIZE) ?
            ((t_addr) == (MEMSPACE_SIZE) ? 0 :
            ((t_addr)&(MEMSPACE_SIZE-1))) : (t_addr));
        /* check for halfword alignment */
        if (t_addr & 0x00000001)
        {
          exception (m, EXC_ADES);
        }
        else
        {
          setReg (m, PC, npc);
          /* FIXME may need to check endianness */
          /* set hi byte */
          setByte (t_addr, (u_int8)(getReg (m, rt) >> 8));
          /* set lo byte */
          setByte (t_addr+1, (u_int8)(getReg (m, rt)));
        }
        break;
      case 0x2b: /* sw itype */
        t_addr = getReg (m, rs) + offset;

        if (m->trace)
        {
          printf ("%08X SW R%d, %d(R%d)\n", instr, rt, offset, rs);
        }
        /* new to wrap address maybe FIXME */
        t_addr = ((t_addr) >= (MEMSPACE_SIZE) ?
            ((t_addr) == (MEMSPACE_SIZE) ? 0 :
            ((t_addr)&(MEMSPACE_SIZE-1))) : (t_addr));
        /* check alignment */
        if (t_addr % WORD_SIZE)
        {
          exception (m, EXC_ADES);
        }
        else
        {
          int cc, inv_cc;
          /*
           * the coherence protocol should invalidate
           * a remote processors link regiser,
           * however it should not invalidate its own
           * link register as the coherence protocol does not
           * recognise this as outbound traffic
           */

          setReg (m, PC, npc);
          /* check for coherence invalidation */
          if (m == m1)
          {
            /* get other processor link register */
            cc = ccrmw[inv_cc = 1];
          }
          else
          {
            /* get other processor link register */
            cc = ccrmw[inv_cc = 0];
          }
          /* invalidate other core link register */
          if (cc == t_addr)
          {
            if (m->trace) printf ("\t**Coherence Invalidation\n");
            ccrmw[inv_cc]++;
          }
          /* invalidate link reg */
          if (getReg (m, RMW) == t_addr)
          {
            setReg (m, RMW, t_addr+1);
          }

          /* do a dcache access */
          cacheAccess(m,t_addr,DCACHE);

          /* do the store word */
          setWord (m, t_addr, getReg (m, rt));
        }
        break;
      case 0x30: /* tsl or ll itype */
        /* test and set load for multicore
         * i used the opcode for ll from mips */
        /* ll reads content of mem into rt
         * then sets rmw state for processor */
        t_addr = getReg (m, rs) + offset;

        if (m->trace)
        {
          //printf ("%08X TSL R%d, %d(R%d)\n", instr, rt, offset, rs);
          printf ("%08X LL R%d, %d(R%d)\n", instr, rt, offset, rs);
        }
        /* new to wrap address maybe FIXME */
        t_addr = ((t_addr) >= (MEMSPACE_SIZE) ?
            ((t_addr) == (MEMSPACE_SIZE) ? 0 :
            ((t_addr)&(MEMSPACE_SIZE-1))) : (t_addr));
        /* check alignment */
        if (t_addr % WORD_SIZE)
        {
          exception (m, EXC_ADEL);
        }
        else
        {
          setReg (m, PC, npc);
          if (m->trace)
          {
            printf ("\t[word read from %08X]\n", t_addr);
          }
          /* get value at memory */
          setReg (m, rt, getWord (t_addr));
          /* set value at memory used for tsl */
          //setWord (m, t_addr, 0xffffffff);
          /* set rmw state to addr used for ll */
          setReg (m, RMW, t_addr);
          /* keep track of cc conflicts */
          if (m == m1)
            ccrmw[0] = t_addr;
          else
            ccrmw[1] = t_addr;
        }
        break;
      case 0x38: /* sc itype */
        /* sc will fail when: */
        /* a coherent store is completed by another processor */
        /* an exception occurs */
        t_addr = getReg (m, rs) + offset;

        if (m->trace)
        {
          printf ("%08X SC R%d, %d(R%d)\n", instr, rt, offset, rs);
        }
        /* new to wrap address maybe FIXME */
        t_addr = ((t_addr) >= (MEMSPACE_SIZE) ?
            ((t_addr) == (MEMSPACE_SIZE) ? 0 :
            ((t_addr)&(MEMSPACE_SIZE-1))) : (t_addr));
        /* check alignment */
        if (t_addr % WORD_SIZE)
        {
          exception (m, EXC_ADES);
        }
        else
        {
          int cc, inv_cc, ccaddr;

          setReg (m, PC, npc);
          /* check for coherence invalidation */
          if (m == m1)
          {
            /* get other processor link register */
            cc = ccrmw[inv_cc = 1];
            /* get own link address */
            ccaddr = ccrmw[0];
          }
          else
          {
            /* get other processor link register */
            cc = ccrmw[inv_cc = 0];
            /* get own link address */
            ccaddr = ccrmw[1];
          }
          /* invalidate other core link register */
          if (cc == t_addr)
          {
            if (m->trace) printf ("\t**Coherence Invalidation\n");
            ccrmw[inv_cc]++;
          }
          /* check if state is valid */
          if (getReg (m, RMW) == t_addr && ccaddr == t_addr)
          {
            /* store mem loc and set success */
            /* sc should invalidate its own processors
             * link register, just other processors link registers
             * as it is doing above 2012 -EV
             */
            setWord (m, t_addr, getReg (m, rt));
            setReg (m, rt, 1);
            setReg (m, RMW, t_addr+1);
          }
          /* rmw state not for this sc or another processor invalidated us */
          else
          {
            /* set fail */
            setReg (m, rt, 0);
          }
        }
        break;
      case 0x3f: /* halt */
        if (m->trace)
        {
          printf ("%08X HALT\n", instr);
        }
        setReg (m, PC, npc);
        printf ("HALT executed(%s).\n", m->name);
        m->halted = TRUE;
        break;
      default:
        exception (m, EXC_UNIMP_INSTR);
        printf ("Illegal instruction: %08X.\n", instr);
        return 0;
        break;
    }/* end execute switch */

    /* set halting */
    if (m2 != NULL && multicore)
    {
      halting = (m1->halted && m2->halted);
    }
    else
    {
      halting = (m1->halted);
    }

    /* decrement our time share */
    if (timeshare > 0)
    {
      timeshare--;
    }
  }/* end while */


  /* Write dcache hit count to memory */
  if(caches)
  {
    if(m1->trace) printf("Hit count stored to memory\n");
    setWord (m1, HIT_ADDR, m1->num_dhit);
  }

  /* dump machine */
  machineDump (m1, m2);

  /* return */
  return 1;
}

/* destroy machine */
void machineClean (Machine **mac)
{
  Machine *t_m = *mac;

  assert (mac != NULL);
  assert (*mac != NULL);

  free (t_m);
  *mac = NULL;
}

/* free main memory */
void mainmemFree ()
{
  u_int32 i;
  for (i = 0; i < MEMSPACE_SIZE; i++)
  {
    if (mainmem[i] != NULL)
    {
      free (mainmem[i]);
      mainmem[i] = NULL;
    }
  }
}

/*******************************************************************
 * Cache Simulation
 *******************************************************************
 */

/* use this so we don't have to link the math library
    only defined for powers of 2 */
u_int32 logb2(int i)
{
  u_int32 l;

  switch(i){
    case 1: l = 0; break;
    case 2: l = 1; break;
    case 4: l = 2; break;
    case 8: l = 3; break;
    case 16: l = 4; break;
    case 32: l = 5; break;
    case 64: l = 6; break;
    case 128: l = 7; break;
    case 256: l = 8; break;
    default: l = 0; break;
  }
  return l;
}

/* returns the tag field of a given address */
u_int32 getTag(u_int32 addr, int i)
{
  assert(i == ICACHE || i == DCACHE);
  /* icache is 0, dcache is 1 */
  int offset;

  if(i == ICACHE)
  {
    offset = logb2(WORD_SIZE) + logb2(ICACHE_BLOCKSIZE) + logb2(ICACHE_NUMSETS);
  }
  else if (i == DCACHE)
  {
    offset = logb2(WORD_SIZE) + logb2(DCACHE_BLOCKSIZE) + logb2(DCACHE_NUMSETS);
  }
  return field(addr,offset, 32 - offset);
}

/* returns the index field of a given address */
u_int32 getIndex(u_int32 addr, int i)
{
  assert(i == ICACHE || i == DCACHE);
  /* icache is 0, dcache is 1 */
  if(i == ICACHE)
  {
    return field(addr,logb2(WORD_SIZE) + logb2(ICACHE_BLOCKSIZE),logb2(ICACHE_NUMSETS));
  }
  else
  {
    return field(addr,logb2(WORD_SIZE) + logb2(DCACHE_BLOCKSIZE),logb2(DCACHE_NUMSETS));
  }
}


/* simulate a cache access and modify stats */
/* LRU is implemented using m->instruction timestamps */
void cacheAccess(Machine *m, u_int32 addr, int cache)
{
  u_int32 index;
  u_int32 tag;
  int i;

  index = getIndex(addr,cache);
  tag = getTag(addr,cache);

  if(cache == ICACHE)
  {
    for(i = 0; i < ICACHE_ASSOC; i++)
    {
      if(m->icache[index][i] == tag && m->i_v[index][i])
      {
        /* We have a hit! Update stats */
        m->num_ihit++;
        m->i_lru[index][i] = m->instructions;

        if(caches && m->trace)
        {
          if(ICACHE_ASSOC == 1)
            printf("\n\tI$[%d] HIT with Tag = 0x%X\n\t",index,tag);
          else
            printf("\n\tI$[%d][%d] HIT with Tag = 0x%X\n\t",index,i,tag);
        }

        return;
      }
    }
    /* At this point we have a miss, must allocate space */
    int lruway = 0;
    int lruval = m->i_lru[index][0];
    for(i = 0; i < ICACHE_ASSOC; i++)
    {
      if(m->i_lru[index][i] < lruval)
      {
        lruway = i;
        lruval = m->i_lru[index][i];
      }
    }
    /* We now have the least recently used way. Replace it with
       the new tag */
    m->icache[index][lruway] = tag;
    /* Make sure valid is set, may be on compulsory miss */
    m->i_v[index][lruway] = 1;
    /* Set the new lru timestamp */
    m->i_lru[index][lruway] = m->instructions;

    if(caches && m->trace)
    {
      if(ICACHE_ASSOC == 1)
        printf("\n\tI$ MISS: I$[%d].tag <-- 0x%X\n\t",index,tag);
      else
        printf("\n\tI$ MISS: I$[%d][%d].tag <-- 0x%X\n\t",index,lruway,tag);
    }

  }
  else if(cache == DCACHE)
  {
    /* We have a memory access, update stat */
    m->num_mem_access++;
    for(i = 0; i < DCACHE_ASSOC; i++)
    {
      if(m->dcache[index][i] == tag && m->d_v[index][i])
      {
        /* We have a hit! Update stats and return */
        m->num_dhit++;
        m->d_lru[index][i] = m->instructions;
        if(caches && m->trace)
        {
          if(DCACHE_ASSOC == 1)
            printf("\tD$[%d] HIT with Tag = 0x%X (%u)\n",index,tag, m->num_dhit);
          else
            printf("\tD$[%d][%d] HIT with Tag = 0x%X (%u)\n",index,i,tag, m->num_dhit);
        }

        return;
      }
    }
    /* At this point we have a miss, must allocate space */
    int lruway = 0;
    int lruval = m->d_lru[index][0];
    for(i = 0; i < DCACHE_ASSOC; i++)
    {
      if(m->d_lru[index][i] < lruval)
      {
        lruway = i;
        lruval = m->d_lru[index][i];
      }
    }

    /* We now have the least recently used way. Replace it with
       the new tag */
    m->dcache[index][lruway] = tag;
    /* Make sure valid is set, may be on compulsory miss */
    m->d_v[index][lruway] = 1;
    /* Set the new lru timestamp */
    m->d_lru[index][lruway] = m->instructions;

    if(caches && m->trace)
    {
      if(DCACHE_ASSOC == 1)
        printf("\tD$ MISS: D$[%d].tag <-- 0x%X (%u)\n",index,tag, m->num_dhit);
      else
        printf("\tD$ MISS: D$[%d][%d].tag <-- 0x%X (%u)\n",index,lruway,tag, m->num_dhit);
    }
  }
}



/* let users know how to use program */
void usage (char *cmd)
{
  fprintf (stderr, "Ver: %d.%d Written by: Eric Villasenor\n",
      version_major, version_minor);
  fprintf (stderr, "This tool simulates the program loaded in the meminit file\n\n");

  fprintf (stderr, "\nUsage: %s [options] meminit_file\n", cmd);
  fprintf (stderr, "If no filename is given sim will look for \"meminit.hex\"\n");
  fprintf (stderr, "Start PC of Core 1: 0x%04X\n", PROCONE_BASE_ADDR);
  fprintf (stderr, "Start PC of Core 2: 0x%04X\n", PROCTWO_BASE_ADDR);
  fprintf (stderr, "\n     -h  What you're looking at right now.\n");
  fprintf (stderr, "     -m  Execute program with multiple cores\n");
  fprintf (stderr, "     -c  Simulate single core with caches\n");
  fprintf (stderr, "     -t  print execution trace of program\n\n");
}
#include <unistd.h>
/* main function where the magic starts */
int main (int argc, char *argv[])
{
  int i, j;                       /* counters/flags */
  Machine *m1 = NULL;             /* processor 0 */
  Machine *m2 = NULL;             /* processor 1 */
  char *filename = "meminit.hex"; /* default init file */
  char *procone = "Core 1";       /* name of p0 */
  char *proctwo = "Core 2";       /* name of p1 */
  sleep(5);
  /* make the machines */
  m1 = machineCreate (procone);
  m2 = machineCreate (proctwo);

  /* get options */
  for (i = 1; i < argc; i++)
  {
    if (j == 1)
    {
      /* user did something dumb */
      usage (argv[0]);
      machineClean(&m1);
      machineClean(&m2);
      return 0;
    }
    if (strcmp (argv[i], "-t") == 0)
    {
      /* tracing output */
      m1->trace = 1;
      m2->trace = 1;
    }
    else if (strcmp (argv[i], "-m") == 0)
    {
      /* doing multicore */
      multicore = 1;
    }
    else if (strcmp (argv[i], "-c") == 0)
    {
      /* simulating caches */
      caches = 1;
    }
    else if (strcmp (argv[i], "-h") == 0)
    {
      /* user just wants help */
      usage (argv[0]);
      machineClean (&m1);
      machineClean (&m2);
      return 0;
    }
    else
    {
      /* user wants to
       * use a different filename
       * for memory init */
      filename = argv[i];
      j = 1;
    }
  }

  /* can't do caches and multicore (coherence not implemented yet) */
  if(caches && multicore)
  {
    fprintf(stderr,"\nCache simulation works for single core only!\n\n");
    return 0;
  }

  /* load program and execute */
  /* it doesn't matter what
   * machine load program gets as input
   * all it is used for is to print
   * the words and addresses loaded
   * from the init file if tracing is enabled */
  if (mainmemLoadProgram (m1, filename) != 0)
  {
    printf ("Starting simulation...\n\n");
    if (m1->trace)
    {
      printf ("\t%s\n", m1->name);
    }
    /* set pc of proc1 to start address */
    setReg (m1, PC, PROCONE_BASE_ADDR);

    if (m2->trace && multicore)
    {
      printf ("\t%s\n", m2->name);
    }
    else
    {
      m2->trace = 0;
    }
    /* set pc of proc2 to start address */
    setReg (m2, PC, PROCTWO_BASE_ADDR);

    /* start executing program */
    execute (m1, m2);
  }

  /* clean up */
  machineClean (&m1);
  machineClean (&m2);
  mainmemFree ();

  /* done */
  return 0;
}

