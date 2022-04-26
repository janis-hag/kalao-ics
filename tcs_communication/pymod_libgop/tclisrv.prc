
server /connect="test_server"
server /write="/test" /read /timeout=1
sh srvans
server /write="/quit" /read
