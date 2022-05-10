#

#gcc -c -fPIC -Wall -DUSE_STRERROR -DSELECT_CALL -DSYSV -DLINUX ../libipc/libipc.c  pymod_libipc_wrap.c -I../libipc -I../gop -I/home/weber/anaconda3/include/python3.6m

#ld -shared libipc.o ../gop/libgop.a pymod_libipc_wrap.o -o _pymod_libipc.so

PYTHON_INCLUDE = /usr/include/python3.8/

_pymod_libipc.so: pymod_libipc_wrap.o
	ld -shared libipc.o ../libgop/libgop_${OPSYS}.a pymod_libipc_wrap.o -o _pymod_libipc.so

pymod_libipc_wrap.c: pymod_libipc.i
	  swig -python pymod_libipc.i
          
pymod_libipc_wrap.o: pymod_libipc_wrap.c
	gcc -c -fPIC -Wall -DUSE_STRERROR -DSELECT_CALL -DSYSV -DLINUX ../libipc/libipc.c  pymod_libipc_wrap.c -I../libipc -I../libgop -I$(PYTHON_INCLUDE)        

clean:
	/bin/rm -f *.o *.so pymod_libipc.py pymod_libipc_wrap.c
