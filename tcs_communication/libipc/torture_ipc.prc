! Torture test de libipc pour Inter
!
! Etat de base:
!	avoir un Inter lancé en mode serveur
!		unix> inter -server -echo
!	dans une autre fenêtre:
!		unix> inter -client
!		inter> @torture_ipc
!
! A la fin le serveur doit être libre, en attente de commande
!
! attente
!
local shmstat val result=""

shmstat=shmwait()
if shmstat.ne.0 call die "Problem with shmwait()"
!
! ecriture
!
shmstat=shminit()
if shmstat.ne.0 call die "Problem with ini_shmkw()"
shmstat=shmadd("COMMAND","i=shmput(RESULT,""xyz"")")
if shmstat.ne.0 call die "Problem with shmadd()"
!
! relecture
!
result=shmget("COMMAND")
if (lne(result,"i=shmput(RESULT,""xyz"")")) call die "Problem with shmget("COMMAND")"
!
! ecriture
!
shmstat=shmadd("ARG1","1234")
if shmstat.ne.0 call die "Problem with shmadd()"
shmstat=shmadd("ARG2","abcdef")
if shmstat.ne.0 call die "Problem with shmadd()"
shmstat=shmadd("ARG3","-56")
if shmstat.ne.0 call die "Problem with shmadd()"
!
! envoi de la commande et attente du resultat
!
shmstat=shmack()
if shmstat.ne.0 call die "Problem with shm_ack()"
shmstat=shmwack()
if shmstat.ne.0 call die "Problem with shm_wack()"
!
! relecture
!
result=shmget("RESULT")
if (lne(result,"xyz")) call die "Problem with shmget("COMMAND")"
shmstat=shmfree()
if shmstat.ne.0 call die "Problem with shmfree()"
!
! Nouvelle attente
!
shmstat=shmwait()
if shmstat.ne.0 call die "Problem with shmwait()"
shmstat=shmadd("COMMAND","VWX")
if shmstat.ne.0 call die "Problem with shmadd()"
!
! envoi signal
!
shmstat=signal(2)
if shmstat.ne.0 call die "Problem with signal(2)"
shmstat=shmcont()
if shmstat.ne.0 call die "Problem with shmcont()"
!
! lecture des erreur
!
shmstat=shmwait()
if shmstat.ne.0 call die "Problem with shmwait()"
shmstat=shmgerr()
if shmstat.lt.0 call die "Problem with shmgerr()"
if shmstat.ne.1 call die "Problem with shmgerr() could be 1"
result=shmgcod()
if lne(result,"int_nocomm") call die "Problem with shmgcod()"
shmstat=shmgsta()
if shmstat.lt.0 call die "Problem with shmgsta()"
if shmstat.ne.0 call die "Problem with shmgsta() could be 0"



!
! lecture ncnt
!
shmstat=shmncnt()
if shmstat.lt.0 call die "Problem with shmncnt()"
if shmstat.ne.0 call die "Problem with shmncnt() could be 0"
!
! on efface les erreurs
shmstat=clearsv()
if shmstat.lt.0 call die "Problem with clearsv()"
shmstat=shmgerr()
if shmstat.lt.0 call die "Problem with shmgerr() after clearsv()"
if shmstat.ne.0 call die "Problem with shmgerr() could be 1 after clearsv()"
result=shmgcod()
if lne(result,"") call die "Problem with shmgcod() after clearsv()"


shmstat=shmfree()
if shmstat.ne.0 call die "Problem with shmfree()"

write "Torture test de lipipc sous perl OK (test des 16 fonctions)"


endproc



subroutine die string=c
erreur /set string
return
endproc
