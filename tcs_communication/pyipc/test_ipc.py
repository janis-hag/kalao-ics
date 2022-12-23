import sys
import time

sys.path.append("/home/weber/src/pymod_libipc/")
sys.path.append("/home/weber/src/pymod_libgop/")
import pymod_libipc as ipc
import pymod_libgop as gop
import select

timeout = 2

host = "glslogin2"
symb_name = "inter"
rcmd = "ipcsrv"
port = 12345
semkey = 1000

#
# The connection to ipcsrv on <host>:
#
socketId = ipc.init_remote_client(host, symb_name, rcmd, port, semkey)
print("ipc.init_remote_client, returns:", socketId)
if (socketId <= 0):
    print("No connection, exit")
    sys.exit(-1)

#
# 3 lignes pour acces local (sans ipcsrv)
#
#ipc.select_key_semid_block(semkey)
#sema=ipc.init_semaphore()
#bloc=ipc.init_block()

print("wait")
status = ipc.shm_wait(timeout)
print("ipc.shm_wait returns:", status)
if (status < 0):
    ipc.shm_free()
    sys.exit(-1)

print("ini_shm_kw")
ipc.ini_shm_kw()

print("put_shm_kw 1")
ipc.put_shm_kw("1er", "2eme")

print("put_shm_kw 2")
ipc.put_shm_kw("salut", "poilu")

print("get_shm_kw")
returnList = ipc.get_shm_kw("salut")
print("Content of 'salut' = >", returnList[1], "<")
returnList = ipc.get_shm_kw("salutXX")
print("Content of 'salutXX' = >", returnList[1], "<")

print("get_shm_kw_n 0")
returnList = ipc.get_shm_kw_n(0)
print("key=", returnList[1], "content=", returnList[2])

print("shm_free")
ipc.shm_free()

print("send_cmd")
ipc.send_cmd("write test remote 1", timeout, timeout)
print("send_cmd")
ipc.send_cmd("write test remote 2", timeout, timeout)
print("send_cmd")
ipc.send_cmd("write test remote 3", timeout, timeout)
print("send_cmd")
ipc.send_cmd("write test remote 4", timeout, timeout)
