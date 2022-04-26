	program	fclient

	integer	connect, verbose, status, ilen
	character*128	answer

	call init_signal_sigint()

	call connect_client(connect, verbose, status)

	do while (1)

		call get_input_cmd("Tapez n'importe quoi > ", answer, ilen)
		if(answer(1:4).eq.'quit')stop

		call write_cmd(connect, status)
		call read_buf(connect, status)
		call write_buf(connect, status)

	enddo

	end

cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc
	subroutine handler_ctrlc(signal)
cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc
	implicit none
	integer		signal		! in: No du signal
c
c---description---
c       handler du <ctrl>-C
c---routines------
c       ---


	call reinit_signal_sigint()

	write(*,*)'handler FORTRAN pour SIGINT'

	return
	end
