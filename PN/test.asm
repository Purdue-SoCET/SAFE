	printf:
	addiu	$sp,$sp,-1064
	sw	$fp,1060($sp)
	addu	$fp,$sp,$0
	sw	$4,1064($fp)
	sw	$5,1068($fp)
	sw	$6,1072($fp)
	sw	$7,1076($fp)
	sw	$0,20($fp)
	sw	$0,12($fp)
	addiu	$2,$fp,1068
	sw	$2,28($fp)
	sw	$0,16($fp)
	j	$L2
	$L16:
	lw	$2,16($fp)
ori	$2, $zero, 2
	sllv	$2,$2,$2
	lw	$3,1064($fp)
	addu	$2,$3,$2
	lw	$3,0($2)
	ori	$2, $zero, 37
	beq	$3,$2,$L3
	lw	$2,16($fp)
ori	$2, $zero, 2
	sllv	$2,$2,$2
	lw	$3,1064($fp)
	addu	$2,$3,$2
	lw	$3,0($2)
	lw	$2,16($fp)
ori	$2, $zero, 2
	sllv	$2,$2,$2
	addiu	$4,$fp,8
	addu	$2,$4,$2
	sw	$3,24($2)
	lw	$2,16($fp)
	addiu	$2,$2,4
	sw	$2,16($fp)
	lw	$2,12($fp)
	addiu	$2,$2,1
	sw	$2,12($fp)
	j	$L2
	$L3:
	lw	$2,16($fp)
	addiu	$2,$2,1
ori	$2, $zero, 2
	sllv	$2,$2,$2
	lw	$3,1064($fp)
	addu	$2,$3,$2
	lw	$3,0($2)
	ori	$2, $zero, 37
	bne	$3,$2,$L4
	lw	$2,16($fp)
ori	$2, $zero, 2
	sllv	$2,$2,$2
	addiu	$3,$fp,8
	addu	$2,$3,$2
	ori	$3, $zero, 37
	sw	$3,24($2)
	lw	$2,16($fp)
	addiu	$2,$2,2
	sw	$2,16($fp)
	lw	$2,12($fp)
	addiu	$2,$2,1
	sw	$2,12($fp)
	j	$L2
	$L4:
	ori	$2, $zero, 32
	sw	$2,24($fp)
	sw	$0,8($fp)
	lw	$2,16($fp)
	addiu	$2,$2,1
	sw	$2,16($fp)
	lw	$2,16($fp)
ori	$2, $zero, 2
	sllv	$2,$2,$2
	lw	$3,1064($fp)
	addu	$2,$3,$2
	lw	$3,0($2)
	ori	$2, $zero, 48
	bne	$3,$2,$L6
	ori	$2, $zero, 48
	sw	$2,24($fp)
	lw	$2,16($fp)
	addiu	$2,$2,1
	sw	$2,16($fp)
	j	$L6
	$L8:
	lw	$3,8($fp)
	addu	$2,$3,$0
ori	$2, $zero, 2
	sllv	$2,$2,$2
	addu	$2,$2,$3
ori	$2, $zero, 1
	sllv	$2,$2,$2
	addu	$4,$2,$0
	lw	$2,16($fp)
ori	$2, $zero, 2
	sllv	$2,$2,$2
	lw	$3,1064($fp)
	addu	$2,$3,$2
	lw	$2,0($2)
	addu	$2,$4,$2
	addiu	$2,$2,-48
	sw	$2,8($fp)
	lw	$2,16($fp)
	addiu	$2,$2,1
	sw	$2,16($fp)
	$L6:
	lw	$2,16($fp)
ori	$2, $zero, 2
	sllv	$2,$2,$2
	lw	$3,1064($fp)
	addu	$2,$3,$2
	lw	$2,0($2)
ori	$2, $zero, 48
	slt	$2,$2,$2
	bne	$2,$0,$L7
	lw	$2,16($fp)
ori	$2, $zero, 2
	sllv	$2,$2,$2
	lw	$3,1064($fp)
	addu	$2,$3,$2
	lw	$2,0($2)
ori	$2, $zero, 58
	slt	$2,$2,$2
	bne	$2,$0,$L8
	$L7:
	lw	$3,12($fp)
	lw	$2,8($fp)
	addu	$2,$3,$2
ori	$2, $zero, 257
	sltu	$2,$2,$2
	bne	$2,$0,$L9
	ori	$3, $zero, 256
	lw	$2,12($fp)
	subu	$2,$3,$2
	sw	$2,8($fp)
	$L9:
	lw	$2,28($fp)
	addiu	$2,$2,4
	sw	$2,28($fp)
	lw	$2,16($fp)
ori	$2, $zero, 2
	sllv	$2,$2,$2
	lw	$3,1064($fp)
	addu	$2,$3,$2
	lw	$2,0($2)
	addiu	$2,$2,-88
ori	$3, $zero, 33
	sltu	$3,$2,$3
	beq	$3,$0,$L10
ori	$3, $zero, 2
	sllv	$3,$2,$3
	ori	$2, $zero, $L12
	addu	$2,$3,$2
	lw	$2,0($2)
	addu	$2,$2,$28
	jr	$2
	$L12:
	$L10:
lui $2,4294901760
	ori	$2, $zero, 65535
	j	$L19
	$L20:
	nop
	lw	$2,16($fp)
	addiu	$2,$2,1
	sw	$2,16($fp)
	lw	$2,12($fp)
	addiu	$2,$2,1
	sw	$2,12($fp)
	$L2:
	lw	$2,16($fp)
ori	$2, $zero, 2
	sllv	$2,$2,$2
	lw	$3,1064($fp)
	addu	$2,$3,$2
	lw	$2,0($2)
	beq	$2,$0,$L15
	lw	$2,12($fp)
ori	$2, $zero, 256
	slt	$2,$2,$2
	bne	$2,$0,$L16
	$L15:
	lw	$2,12($fp)
ori	$2, $zero, 256
	slt	$2,$2,$2
	beq	$2,$0,$L17
	lw	$2,16($fp)
ori	$2, $zero, 2
	sllv	$2,$2,$2
	addiu	$3,$fp,8
	addu	$2,$3,$2
	sw	$0,24($2)
	j	$L18
	$L17:
	lw	$2,16($fp)
	addiu	$2,$2,-1
	sw	$2,16($fp)
	lw	$2,16($fp)
ori	$2, $zero, 2
	sllv	$2,$2,$2
	addiu	$3,$fp,8
	addu	$2,$3,$2
	sw	$0,24($2)
	lw	$2,12($fp)
	addiu	$2,$2,-1
	sw	$2,12($fp)
	$L18:
	lw	$2,12($fp)
	$L19:
	addu	$sp,$fp,$0
	lw	$fp,1060($sp)
	addiu	$sp,$sp,1064
	jr	$31
	d:
	e:
	$LC0:
	main:
	addiu	$sp,$sp,-48
	sw	$31,44($sp)
	sw	$fp,40($sp)
	addu	$fp,$sp,$0
	ori	$5, $zero, 1
	ori	$4, $zero, $LC0
	jal	printf
	ori	$2, $zero, 3
	sw	$2,24($fp)
	ori	$2, $zero, 4
	sw	$2,28($fp)
	lw	$3,24($fp)
	lw	$2,28($fp)
	addu	$2,$3,$2
	sw	$2,32($fp)
	addu	$2,$0,$0
	addu	$sp,$fp,$0
	lw	$31,44($sp)
	lw	$fp,40($sp)
	addiu	$sp,$sp,48
	jr	$31
        halt

