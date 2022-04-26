# Makefile pour gop
# -----------------
#
# OPSYS doit contenir:  <operating_system>_<version>
#	       exemple:  SunOS_4.1.3, SUNOS_5.3, Linux_1.1.18
#
# definitions specifiques a l'operating system
#
include Rules_${OPSYS}.mke
#
# targets specifiques a l'operating system
#
LIBGOP		= libgop_${OPSYS}.a
GOP_WAIT	= gop_wait_${OPSYS}
GOP_TIMER	= gop_timer_${OPSYS}
TEST_GOP_TIMER	= test_gop_timer_${OPSYS}
CLIENT		= client_${OPSYS}
TRANSMITTER	= transmitter_${OPSYS}
SERVER		= server_${OPSYS}
FCLIENT		= fclient_${OPSYS}
TORTURE_CLIENT	= torture_client_${OPSYS}
SUBCLIENT_O	= subclient_${OPSYS}.o
LIBSRVGOP       = libsrvgop_${OPSYS}.a
TEST_F_LIBSRVGOP= test_f_libsrvgop_${OPSYS}
TEST_C_LIBSRVGOP= test_c_libsrvgop_${OPSYS}



.KEEP_STATE:
.PRECIOUS: $(LIBGOP)

all: all_lib all_exe

all_lib: $(LIBGOP) $(LIBSRVGOP)
all_exe: $(GOP_WAIT) $(GOP_TIMER)

clean:
	rm *$(OPSYS).a *$(OPSYS).o 

# $(TEST_GOP_TIMER) $(SERVER) $(CLIENT) $(TRANSMITTER) $(FCLIENT) 
# $(TORTURE_CLIENT) $(TEST_F_LIBSRVGOP) $(TEST_C_LIBSRVGOP)

#
# depences standards pour tout les utilitaires
#
DEPENDENCIES =  gop.h					\
		$(LIBGOP)                 



$(LIBGOP):		$(LIBGOP)(libgop.o)		\
			gop.h
	$(RANLIB) $(LIBGOP)

$(LIBSRVGOP): 	$(LIBSRVGOP)(libsrvgop.o)	\
			gop.h			\
			srvgop.h
	$(RANLIB) $(LIBSRVGOP)


$(SUBCLIENT_O):		subclient.c			\
			$(DEPENDENCIES)
	$(CC) $(CFLAGS) subclient.c -c -o $(SUBCLIENT_O)


$(FCLIENT):		fclient.f $(SUBCLIENT_O)	\
			$(DEPENDENCIES)
	$(FC) $(LDFLAGS) fclient.f $(SUBCLIENT_O) -o $(FCLIENT) $(LIBGOP) $(LDLIBS) -lreadline -ltermcap


$(CLIENT):		client.c			\
			$(DEPENDENCIES)
	$(CC) $(CFLAGS) $(LDFLAGS) client.c -o $(CLIENT) $(LIBGOP)  $(LDLIBS)


$(SERVER):		server.c			\
			$(DEPENDENCIES)
	$(CC) $(CFLAGS) $(LDFLAGS) server.c -o $(SERVER) $(LIBGOP) $(LDLIBS)

$(GOP_WAIT):		gop_wait.c			\
			$(DEPENDENCIES)
	$(CC) $(CFLAGS) $(LDFLAGS) gop_wait.c -o $(GOP_WAIT) $(LIBGOP) -llogbook $(LDLIBS)

$(GOP_TIMER).o:		gop_timer.c			\
			$(DEPENDENCIES)
	$(CC) $(CFLAGS) $(CFLAGS_THREAD) $(LDFLAGS) gop_timer.c -c -o $(GOP_TIMER).o  

$(GOP_TIMER):		$(GOP_TIMER).o			\
			$(DEPENDENCIES)
	$(CC) $(CFLAGS) $(CFLAGS_THREAD) $(LDFLAGS) $(GOP_TIMER).o -o $(GOP_TIMER) $(LIBGOP) -llogbook $(LDLIBS) $(LDLIBS_THREAD) 

$(TEST_GOP_TIMER):		test_gop_timer.c			\
			$(DEPENDENCIES)
	$(CC) $(CFLAGS) $(LDFLAGS) test_gop_timer.c -o $(TEST_GOP_TIMER) $(LIBGOP) $(LDLIBS)

$(TRANSMITTER):		transmitter.c			\
			$(LIB_DIR)/liblogbook.a		\
			$(DEPENDENCIES)
	$(CC) $(CFLAGS) $(LDFLAGS) transmitter.c -o $(TRANSMITTER) -llogbook  $(LIBGOP) $(LDLIBS)

$(TORTURE_CLIENT):	torture_client.c		\
			$(DEPENDENCIES)
	$(CC) $(CFLAGS) $(LDFLAGS) torture_client.c -o $(TORTURE_CLIENT) $(LIBGOP) $(LDLIBS)

$(TEST_F_LIBSRVGOP):	test_f_libsrvgop.f		\
			srvgop.h			\
			$(LIBSRVGOP)			\
			$(DEPENDENCIES)
	$(FC) $(FFLAGS) $(LDFLAGS) test_f_libsrvgop.f -o $(TEST_F_LIBSRVGOP) $(LIBSRVGOP) $(LIBGOP) $(LDLIBS)

$(TEST_C_LIBSRVGOP):	test_c_libsrvgop.c		\
			srvgop.h			\
			$(LIBSRVGOP)			\
			$(DEPENDENCIES)
	$(CC) $(CFLAGS) $(LDFLAGS) test_c_libsrvgop.c -o $(TEST_C_LIBSRVGOP) $(LIBSRVGOP) $(LIBGOP) $(LDLIBS)
