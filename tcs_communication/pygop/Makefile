

#PYTHON_INCLUDE = /home/weber/anaconda3/include/python3.6m
PYTHON_INCLUDE =  /usr/include/python3.8/

_pymod_libgop.so: pymod_libgop_wrap.o
	ld -shared libgop.o pymod_libgop_wrap.o -o _pymod_libgop.so

pymod_libgop_wrap.c: pymod_libgop.i
	swig -python pymod_libgop.i

pymod_libgop_wrap.o: pymod_libgop_wrap.c
	gcc -c -fPIC -Wall -DUSE_STRERROR -DSELECT_CALL -DSYSV -DLINUX ../libgop/libgop.c  pymod_libgop_wrap.c -I../libgop -I$(PYTHON_INCLUDE)

clean:
	/bin/rm -f *.o *.so pymod_libgop.py pymod_libgop_wrap.c
