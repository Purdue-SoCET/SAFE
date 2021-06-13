	extern main
	//extern printf
	extern _setup_files
	extern _teardown
; Using Intel syntax
section .text

_start:
   call __setup_files       ;
   call _main               ; call your main
   call __teardown    ; tear down 
   jmp  __exit              ; return to OS

	
