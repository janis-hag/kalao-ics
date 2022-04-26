	program test_f_libsrvgop
c
c	test fortran pour libsrvgop.c
c
c xsdbmanager -s -f libsrvgop.sdb &
c
c f77 test_f_libsrvgop.f -o test_f_libsrvgop -L ~/lib/SunOS_5.4 -l srvgop -lgop -ltpudummy -lnsl -lsocket
c
	integer		ci, ilen, status, timeout
	character*256	answer, err
	character*8	gop_stat
	character*8	gop_class
	
	timeout = 0
									
	call srvg_connect("", "test_f", "libsrvgop", 0, "", 2, 0, 
	1			1, 1, ci)
	if(ci.lt.0)then
		call srvg_get_error_string(err, ilen)
		write(*,'(a)')"erreur : "//err(1:ilen)
c		stop
	endif
	call srvg_verbose(ci, 0, status)
	if(status.lt.0)then
		call srvg_get_error_string(err, ilen)
		write(*,'(a)')"erreur : "//err(1:ilen)
c		stop
	endif
	do i=1,400
		call srvg_write(ci, "read VALUE", status)
		if(status.lt.0)then
			call srvg_get_error_string(err, ilen)
			write(*,'(a)')"erreur : "//err(1:ilen)
			stop
		endif
		call srvg_read(ci, answer, sizeof(answer), 
	1			gop_stat, gop_class, timeout, status)
		if(status.lt.0)then
			call srvg_get_error_string(err, ilen)
			write(*,'(a)')"erreur : "//err(1:ilen)
			stop
		endif
		write(*,'("answer = >", a, "<  status = ", i4,
	1		" gop_stat = ", a, " gop_class = ",a)')
	2			answer(1:status), status,
	3			gop_stat(1:4),gop_class(1:4)
	enddo
	call srvg_disconnect(ci, status)
	end
