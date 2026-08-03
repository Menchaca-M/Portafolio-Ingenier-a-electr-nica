.data
    
    .align 4                    # Alineación a 4 bytes (word)
    Inicio_Row: .space 516    # Row de 128 words = 512 bytes + 4 byte para terminador
    Puntero_Row: .space 4
    
.global InicializacionRow
.global AlmacenarNotaRow
.global Borrar_Row
.global Guardar_Flash
.global Clear_Flash   
    
    
.text # Row hace referencia al array en la RAM donde se recopilan las notas
    
    InicializacionRow: # Guardo en Puntero_Row la posicion del array 
	la $t0, Inicio_Row
	sw $t0, Puntero_Row 
    
	
    AlmacenarNotaRow: # Recibo en $a0 la nota a agregar a la row
	lw $t0, Puntero_Row
	la $t1, Inicio_Row
	sub $t1, $t0, $t1
	beq $t1, 513, RowCompleta 
	
	sb $a0, ($t0)
	addiu $t0, $t0, 1
	sw $t0, Puntero_Row

	RowCompleta:
    jr $ra

    
    Borrar_Row: # Borra el contenido de Row con 0
	li $t0, 0
	la $t1, Inicio_Row
	li $t2, 0
	Borro_Row_loop:
	    beq $t0, 128, Fin_Borrar
	    sw $t2, ($t1)
	    addiu $t1, $t1, 4
	    addiu $t0, $t0, 1
	    
	j Borro_Row_loop
	
	Fin_Borrar:
	la $t0, Inicio_Row
	sw $t0, Puntero_Row 
	
    jr $ra
    
  Guardar_Flash: 
    
	di # Disable interrupts
	la $t1, Inicio_Row # dir virtual Row en RAM
	
	li $t0, 0x1D07FE00 # Dir fisica Flash
	
	lui $t3, 0x1FFF
	ori $t3, $t3, 0xFFFF
	and $t2, $t1, $t3  # dir fisica Row en RAM
	
	sw $t0, NVMADDR
	sw $t2, NVMSRCADDR
	
	
	# Unlock Sequence
	li $t0, 0x4003
	sw $t0, NVMCON

	loopLVD:
	lw $t0, NVMCON
	and $t0, $t0, $t5
	beq $t0, 0x800, loopLVD
	
	lui $t0, 0xAA99
	ori $t0, $t0, 0x6655
	lui $t1, 0x5566
	ori $t1, $t1, 0x99AA
	lui $t2, 0x0000
	ori $t2, $t2, 0x8000
	
	sw $t0, NVMKEY
	sw $t1, NVMKEY
	sw $t2, NVMCONSET
	
	loopNVMCONG:
	lw $t0, NVMCON
	li $t1, 0x8000
	and $t2, $t0, $t1
	bne $t2, 0 , loopNVMCONG
	
	li $t0, 0x4000
	sw $t0, NVMCONCLR
	
	lw $t0, NVMCON
    
	ei # Enable interrupts
    jr $ra
    
    
    Clear_Flash:
    
	di # Disable interrupts
	
	li $t0, 0x1D07FE00 # Dir fisica Flash
	
	sw $t0, NVMADDR
	
	# Unlock Sequence
	li $t0, 0x4004
	sw $t0, NVMCON
	
	loopLVD2:
	lw $t0, NVMCON
	and $t0, $t0, $t5
	beq $t0, 0x800, loopLVD2
	
	lui $t0, 0xAA99
	ori $t0, $t0, 0x6655
	lui $t1, 0x5566
	ori $t1, $t1, 0x99AA
	lui $t2, 0x0000
	ori $t2, $t2, 0x8000
	
	sw $t0, NVMKEY
	sw $t1, NVMKEY
	sw $t2, NVMCONSET
	
	loopNVMCONB:
	lw $t0, NVMCON
	li $t1, 0x8000
	and $t2, $t0, $t1
	bne $t2, 0 , loopNVMCONB
	
	li $t0, 0x4000
	sw $t0, NVMCONCLR
	
	lw $t0, NVMCON
	
	ei # Enable interrupts
    jr $ra
    