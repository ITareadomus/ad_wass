# Algoritmo di assegnazioni Area domus

## Obiettivo : 
<div> 

<p> Questo algoritmo ha l'obbiettivo di assegnare i task giornalieri di Area Domus ai cleaner disponibili in modo automatico tenendo conto di vari parametri per la priorità delle assegnazioni </p>

## Funzionamento :

<p> 

### Prima parte:
L'algoritmo, dopo aver preso tutti i cleaner attivi, controlla chi sono quelli da scartare perché devono stare a riposo e seleziona poi quelli da convocare in base al ranking e a chi deve fare più ore. Il numero dei cleaner da scegliere è basato anche sulla previsione degli appartamenti da pulire il giorno seguente, e la stessa cosa vale per gli orari di convocazione.  
Una volta generata la lista, viene presentata su una maschera con i cleaner selezionati evidenziati in verde e la richiesta di conferma per inviare il messaggio automatico di convocazione. Dalla maschera sarà possibile anche selezionare e deselezionare i cleaner da utilizzare.  
Confermando, arriverà il messaggio di convocazione su Telegram a tutti i cleaner, che dovranno necessariamente confermare o rifiutare la convocazione.

### Seconda parte:
Prende in seguito gli appartamenti, ognuno con le proprie specifiche, e calcola la priorità di ogni task in base agli orari di check-in e check-out.  
Inizia ad assegnare gli appartamenti con priorità più alta ai cleaner premium, valutando anche il loro orario di convocazione e scegliendo il migliore per quel task. Dopo il primo giro di assegnazioni, si passa a quelli successivi, dove vengono assegnati ulteriori appartamenti ai cleaner, valutando il tempo di pulizia, la grandezza degli appartamenti e la distanza da quello precedente. Si procede nello stesso modo anche per i cleaner standard.  
Infine, avendo la lista delle assegnazioni, questa viene passata all'area di controllo per rivederla e aggiustarla, se necessario. Successivamente, viene validata in una maschera sul gestionale dove sarà confermata.</p>

</div>