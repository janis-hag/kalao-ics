# Makefile pour libipc
# --------------------
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
LIBIPC = libipc_${OPSYS}.a


.KEEP_STATE:

all: all_lib all_exe

all_lib: $(LIBIPC)
all_exe:  

clean:
	rm *$(OPSYS).a


.KEEP_STATE:
.PRECIOUS: $(LIBIPC)

$(LIBIPC): 		$(LIBIPC)(libipc.o)		\
			libipc.c			\
			ipcdef.h			\
			$(INC_DIR)/gop.h
	$(RANLIB) $(LIBIPC)
	


