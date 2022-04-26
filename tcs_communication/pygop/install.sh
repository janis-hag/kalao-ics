# intsll.sh
#
# faudrait faire un Makefile ...
#
swig -python pymod_libgop.i
gcc -c -fPIC -Wall -DUSE_STRERROR -DSELECT_CALL -DSYSV -DLINUX ../gop/libgop.c  pymod_libgop_wrap.c -I../gop -I/home/weber/anaconda3/include/python3.6m
ld -shared libgop.o pymod_libgop_wrap.o -o _pymod_libgop.so


#python testgop.py
