 .text
.global enviarSPI
.globl imprimir_bitmap
  
    
# a0 DATA 8-bits, a1 Chip Selector, a2 Data/Command(bit0) Reset(bit1), a3 Argumento Doble
# Comando Doble, para comandos con dos argumentos CS debe mantenerse en 0
enviarSPI: 
    
	# Lectura y mascara de pines de control  
	move $t4, $a3
	li $t0, 0x1
	li $t5, 0x2   

	and $t1, $t0, $a1
	and $t2, $t0, $a2
	and $t3, $t5, $a2

	# Shifteo y junto los bits    
	sll $t2, $t2, 1    
	sll $t3, $t3, 2    

	or $t1, $t1, $t2
	or $t1, $t1, $t3

	# Actualizo Puerto E    
	sw $t1, LATE

	sw $a0, SPI2BUF 

	li $t0, 0x800

	# Se completo el envio 
	loopBusy:

	    lw $t1, SPI2STAT
	    and $t1, $t1, $t0
	    beq $t1, $t0, loopBusy

	beq $t4, 1, comandoDoble    
	lw  $t4, PORTE
	ori $t4, $t4, 0x0001     # Fuerzo bit 0 = 1
	sw  $t4, LATE

	comandoDoble:     
    
jr $ra
  
    
  
# $a0 -> llega direccion de lo que quiero imprimir
imprimir_bitmap:
    
	addi $sp, $sp, -28   
	sw $s0, 0($sp)
	sw $s1, 4($sp)
	sw $s2, 8($sp)
	sw $s3, 12($sp)
	sw $s4, 16($sp)
	sw $s5, 20($sp)
	sw $ra, 24($sp)

	la $s0, ($a0)          # puntero a bitmap
	li $s1, 128           # ancho: columnas
	li $a2, 64            # alto: 64 píxeles
	li $s3, 8
	div $a2, $s3
	mflo $s4              # s4 = cantidad de páginas (64/8 = 8)
	li $s2, 0             # s2 = página actual

	loop_filas:
	# Setear página (0xB0 + número de página)
	li $a0, 0xB0   # fila 1
	add $a0, $a0, $s2
	li $a1, 0x00
	li $a2, 0x00          # DC = 0 ? comando
	li $a3, 0x00
	jal enviarSPI

	# Setear columna baja (0x00)
	li $a0, 0x00
	li $a1, 0x00
	li $a2, 0x00
	li $a3, 0x00
	jal enviarSPI

	# Setear columna alta (0x10)
	li $a0, 0x10
	li $a1, 0x00
	li $a2, 0x00
	li $a3, 0x00
	jal enviarSPI

	# Imprimir 128 bytes (una línea horizontal de una página)
	li $s5, 128

	loop_columnas:
	lb $a0, ($s0)
	li $a1, 0x00
	li $a2, 0x01          # DC = 1 datos
	li $a3, 0x00
	jal enviarSPI

	addi $s0, $s0, 1
	addi $s5, $s5, -1
	bne $s5, $zero, loop_columnas

	addi $s2, $s2, 1
	bne $s2, $s4, loop_filas

	# Restaurar registros
	lw $s0, 0($sp)
	lw $s1, 4($sp)
	lw $s2, 8($sp)
	lw $s3, 12($sp)
	lw $s4, 16($sp)
	lw $s5, 20($sp)
	lw $ra, 24($sp)
	addi $sp, $sp, 28

jr $ra
    
   
  