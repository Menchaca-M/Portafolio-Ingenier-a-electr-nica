.global Configuracion_Pins
.global Configuracion_SSD1306
.global Configuracion_SPI
.global Configuracion_UART
    
.text    
    
Configuracion_Pins:
    
    
	# Salida Slave selector (SS)
	li $t0, 0x00
	sw $t0, TRISD


	li $t1, 0x30
	sw $t1, T2CON # Timer OFF

	# Configuracion pines de control 
	# RE0 CS#, RE1 D/C#, RE2 RES#
	li $t0, 0x00
	sw $t0, TRISE   

	# Todos los pines digitales     
	li $t0, 0xFFFF
	sw $t0, AD1PCFG      

	# Todos los pines de PORTB son input   
	li $t0, 0xFFFF
	sw $t0, TRISB
	

jr $ra   
	
/*
DO - a - PORTB12 - A4
DO# - w - PORTB5 - A7
RE - s - PORTB11 - A9
RE# - e - PORTB4 - A1 
MI - d - PORTB10 - A3
FA - f - PORTB9 - A8
FA# - t - PORTB3 - A6
SOL - g - PORTB8 - A2
SOL# - y - PORTB2 - A0
LA - h - PORTB14 - A5 
LA# - u - izq PORTB1 - 41
SI - j - der PORTB15 - A11
menu - 0 - PORTB13 - A10
BUZZER OC2 - 5
*/
    
    
Configuracion_SPI:
    
	li $t0, 0x03800000   
	sw $t0, IEC0CLR

	# Apago SPI
	li $t0, 0x0
	sw $t0, SPI2CON

	# Limpiar buffer de recepcion (se limpia leyendolo)
	lw $t0, SPI2BUF

	# Uso modo estandar
	# ENHBUF en 0
	li $t0, 0x10000
	sw $t0, SPI2CONCLR

	
	# Clk de origen 500 kHz a 50kHz
	li $t0, 0x04
	sw $t0, SPI2BRG

	# Limpiar bit de overflow

	li $t0, 0x40
	sw $t0, SPI2STATCLR

	# Escribir los bits que necesitamos en la configuracion
	li $t0, 0x120
	sw $t0, SPI2CON



	# Configuro SPI1CON
	li $t0, 0x8000
	sw $t0, SPI2CONSET


    
jr $ra


Configuracion_SSD1306:
    
    addiu $sp, $sp, -4
    sw $ra, ($sp)
    
    jal delay
    
    li $t0, 0x0
    sw $t0, PORTE
    
    jal delay	    # delay > 3 us
    
    li $t0, 0x1
    sw $t0, LATE
    
    
    # Display OFF
    li $a0, 0xAE
    li $a1, 0x00       # CS = 0 (activo)
    li $a2, 0x00       # DC = 0 (modo comando)
    li $a3, 0x00
    jal enviarSPI
    
    
    # Set MUX 
    li $a0, 0xA8
    li $a1, 0x00       # CS = 0 (activo)
    li $a2, 0x00       # DC = 0 (modo comando)
    li $a3, 0x01       # Doble comando
    jal enviarSPI
    
    li $a0, 0x3F       # MUX ratio 16 to 63
    li $a1, 0x00       # CS = 0 (activo)
    li $a2, 0x00       # DC = 0 (modo comando)
    li $a3, 0x00
    jal enviarSPI
    
    
    # Set Display Offset
    li $a0, 0xD3
    li $a1, 0x00       # CS = 0 (activo)
    li $a2, 0x00       # DC = 0 (modo comando)
    li $a3, 0x01       # Doble comando
    jal enviarSPI
    
    li $a0, 0x00       # Display start line 40h - 7Fh, COM0
    li $a1, 0x00       # CS = 0 (activo)
    li $a2, 0x00       # DC = 0 (modo comando)
    li $a3, 0x00
    jal enviarSPI
    
    
    # Set Display Start Line to 0
    li $a0, 0x40
    li $a1, 0x00       # CS = 0 (activo)
    li $a2, 0x00       # DC = 0 (modo comando)
    li $a3, 0x00
    jal enviarSPI

    
    # Set Segment Re-map (Horizontal)  Espeja horizontalmente si deseado
    li $a0, 0xA0
    li $a1, 0x00       # CS = 0 (activo)
    li $a2, 0x00       # DC = 0 (modo comando)
    li $a3, 0x00
    jal enviarSPI
    
    
    # Set Memory Addressing Mode 
    li $a0, 0x20       # comando
    li $a1, 0x00       # CS=0 (activo)
    li $a2, 0x00       # DC=0 (modo comando) 
    li $a3, 0x01       # comando doble
    jal enviarSPI

    li $a0, 0x00       # Horizontal Addressing Mode
    li $a1, 0x00
    li $a2, 0x00
    li $a3, 0x00       
    jal enviarSPI
    
     
    li $a0, 0x21
    li $a1, 0x00       # CS = 0 (activo)
    li $a2, 0x00       # DC = 0 (modo comando)   
    li $a3, 0x01
    jal enviarSPI
    
    li $a0, 0x00
    li $a1, 0x00       # CS = 0 (activo)
    li $a2, 0x00       # DC = 0 (modo comando)   
    li $a3, 0x01
    jal enviarSPI
    
    li $a0, 0x7F
    li $a1, 0x00       # CS = 0 (activo)
    li $a2, 0x00       # DC = 0 (modo comando)   
    li $a3, 0x00
    jal enviarSPI
    
    li $a0, 0x22
    li $a1, 0x00       # CS = 0 (activo)
    li $a2, 0x00       # DC = 0 (modo comando)   
    li $a3, 0x01
    jal enviarSPI
    
    li $a0, 0x00
    li $a1, 0x00       # CS = 0 (activo)
    li $a2, 0x00       # DC = 0 (modo comando)   
    li $a3, 0x01
    jal enviarSPI
    
    li $a0, 0x07
    li $a1, 0x00       # CS = 0 (activo)
    li $a2, 0x00       # DC = 0 (modo comando)   
    li $a3, 0x00
    jal enviarSPI

    
    # Set COM Output Scan Direction (COM0 hasta COM(N-1))
    li $a0, 0xC0
    li $a1, 0x00       # CS = 0 (activo)
    li $a2, 0x00       # DC = 0 (modo comando) 
    li $a3, 0x00
    jal enviarSPI

     
    # Set COM Pins Hardware Configuration
    li $a0, 0xDA
    li $a1, 0x00       # CS = 0 (activo)
    li $a2, 0x00       # DC = 0 (modo comando)
    li $a3, 0x01       # Comando Doble
    jal enviarSPI
    
    li $a0, 0x12       # ROW0 orden natural
    li $a1, 0x00       # CS = 0 (activo)
    li $a2, 0x00       # DC = 0 (modo comando)
    li $a3, 0x00
    jal enviarSPI
    
    
    # Set Contrast for BANK0
    li $a0, 0x81
    li $a1, 0x00       # CS = 0 (activo)
    li $a2, 0x00       # DC = 0 (modo comando)
    li $a3, 0x01       # Comando Doble
    jal enviarSPI
    
    li $a0, 0x8F       # Contraste 128 de 256
    li $a1, 0x00       # CS = 0 (activo)
    li $a2, 0x00       # DC = 0 (modo comando)
    li $a3, 0x00
    jal enviarSPI

    
    
    # Disable display ON
    li $a0, 0xA4
    li $a1, 0x00       # CS = 0 (activo)
    li $a2, 0x00       # DC = 0 (modo comando)   
    li $a3, 0x00
    jal enviarSPI
    
    
    # Set normal display
    li $a0, 0xA6
    li $a1, 0x00       # CS = 0 (activo)
    li $a2, 0x00       # DC = 0 (modo comando)    
    li $a3, 0x00
    jal enviarSPI
    
    
    # Set Display Clock Divide Ratio / Oscillator Frequency
    li $a0, 0xD5
    li $a1, 0x00       # CS = 0 (activo)
    li $a2, 0x00       # DC = 0 (modo comando)   
    li $a3, 0x01       # Comando Doble
    jal enviarSPI
    
    li $a0, 0x80       # 370 kHz
    li $a1, 0x00       # CS = 0 (activo)
    li $a2, 0x00       # DC = 0 (modo comando)    
    li $a3, 0x01 
    jal enviarSPI

    
    # Enable charge pump
    li $a0, 0x8D
    li $a1, 0x00       # CS = 0 (activo)
    li $a2, 0x00       # DC = 0 (modo comando)
    li $a3, 0x01       # Comando Doble
    jal enviarSPI
    
    li $a0, 0x14
    li $a1, 0x00       # CS = 0 (activo)
    li $a2, 0x00       # DC = 0 (modo comando)   
    li $a3, 0x00
    jal enviarSPI
    
    
    # Display ON
    li $a0, 0xAF
    li $a1, 0x00       # CS = 0 (activo)
    li $a2, 0x00       # DC = 0 (modo comando)   
    li $a3, 0x00
    jal enviarSPI

    
    lw $ra, ($sp)
    addiu $sp, $sp, 4
    
jr $ra
    
 
delay:
    
    li $t0, 10000     
    delay_loop:
    addi $t0, $t0, -1
    bnez $t0, delay_loop
    
jr $ra 
    
    
    # configuracion UART para recepcion y transmicion de datos
Configuracion_UART:
    
	# Divisor para trabajar a 1200 baudios
	li $t0, 25
	sw $t0, U1BRG

	li $t0, 0x1400
	sw $t0, U1STA

	li $t0, 0x8000
	sw $t0, U1MODE

    
jr $ra
    
    