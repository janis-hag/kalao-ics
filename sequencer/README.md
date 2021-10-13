## EDP 

Edp gère les poses KalAO. 

Le nom des poses suit ce format K_xxxxxx. Les paramètres de poses sont envoyés au Synchro qui les transmets à de la maniere adéquate à KalAO.

La taille des message vers KalAO est limitée ainsi on a défini que le caractère de continuation est le "#" en dernier position.

### Liste de poses:

| Nom	| Autre nom	| Commentaire   |
|-------|-----------|---------------|
|       |           |               |		
|       |           |               |		
|       |           |               |		
|       |           |               |		
|       |           |               |		
|       |           |               |		
		
		
		
		
		
		
		

 

La configuration des parametres de pose se fait dans $THOME/config/general/edp_poses_definition.cfg

Lorsqu'il n'y a plus de poses dans la liste EDP, EDP envoie un status "Nothing" au synchro qui arrête la procedure d'acquisition KalAO.

 
## acquisition_kalao.prc

C'est la procédure qui tourne sur le Synchro. Elle gère l'envoi des paramètres de poses sur KalAO et reste en écoute du statut KalAO à intervalle constant, certainement une fois par seconde (TBC).
Paramètres de poses

Les paramètres de poses sont les ceux indiqués sur l'EDP. 

 
## Statuts

Le statut de KalAO est une commande, le premier caractère est le delimiteur. La liste des statuts est:

* **BUSY** KalAO est en cours de pose, aucune action 
* **ERROR** KalAO est en erreur, sortie de la procedure acquisition_KalAO.prc
* **WAITING** KalAO est prêt à recevoir les paramètres d'une pose

	
	
	
	
	
	
	

 

 

 
## AO et guidage en offset

L'AO a une connexion permanente avec l'Inter-T120 et lui permet d'envoyer des commandes en offset, même si aucune pose n'est à disposition sur l'EDP

La communication se fait à travers ipcsrv (par GOP) qui gère les aspect de communication à travers la mémoire partagée et sémaphore.

Cette communication se fait en python avec le module pymod_libipc (gitlab)

LUC: faire un programme de test qui envoye en permanence des commandes d'offset d'une machine sur la host de Inter-T120. Avec le télescope en marche on pourra tester la fréquence maximum d'envoi des commandes.

 

L'arrêt de l'AO se fait en envoyant une commande via le synchro, donc avec un type de pose spécifique style K_ENDAO (TBC).