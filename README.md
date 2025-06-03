# Algoritmo di assegnazioni Area Domus

## Obiettivo : 
<div> 

<p> Questo algoritmo ha l'obbiettivo di assegnare i task giornalieri di Area Domus ai cleaner disponibili in modo automatico tenendo conto di vari parametri per la priorità delle assegnazioni </p>

## Funzionamento :

<p> 

### Prima parte:
L'algoritmo, dopo aver preso tutti i cleaner attivi, controlla chi sono quelli da scartare perché devono stare a riposo e seleziona poi quelli da convocare in base al ranking e a chi deve fare più ore. Il numero dei cleaner da scegliere è basato anche sulla previsione degli appartamenti da pulire il giorno seguente, e la stessa cosa vale per gli orari di convocazione.  
Una volta generata la lista, viene presentata su una maschera con i cleaner selezionati evidenziati in verde e la richiesta di conferma per inviare il messaggio automatico di convocazione. Dalla maschera sarà possibile anche selezionare e deselezionare i cleaner da utilizzare.  
Confermando, arriverà il messaggio di convocazione su Telegram a tutti i cleaner, che dovranno necessariamente confermare o rifiutare la convocazione.(dovremmo fare un api per il bot?)

### Seconda parte:
Prende in seguito gli appartamenti, ognuno con le proprie specifiche, e calcola la priorità di ogni task in base agli orari di check-in e check-out.  
Inizia ad assegnare gli appartamenti con priorità più alta ai cleaner premium, valutando anche il loro orario di convocazione e scegliendo il migliore per quel task. Dopo il primo giro di assegnazioni, si passa a quelli successivi, dove vengono assegnati ulteriori appartamenti ai cleaner, valutando il tempo di pulizia, la grandezza degli appartamenti e la distanza da quello precedente. Si procede nello stesso modo anche per i cleaner standard.  
Infine, avendo la lista delle assegnazioni, questa viene passata all'area di controllo per rivederla e aggiustarla, se necessario. Successivamente, viene validata in una maschera sul gestionale dove sarà confermata.

</p>

## Stato di avanzamento

### Pre Sviluppo
<p> 
    <ul>
        <li>Connessione al db con i dati già disponibili ✔️</li>
        <li>Impostare il timing sulla tabella housekeeping DA FARE</li>
        <li>Creare maschera risorse umane per controllare disponibilità dei cleaner ✔️</li>
        <li>Controllare le dotazioni piccole ✔️</li>
        <li>Pescare il minimo ore 😒(Fatto sull'algoritmo ma non su adam)</li>
    </ul>
</p>

### Sviluppo
<p> 
    <ul>
        <li>Sviluppo dell'algoritmo delle assegnazioni in python 🕓</li>
        <li>Aggiunta dell'integrazione con openai per utilizzo di AI 😒</li>
    </ul>
</p>

### Post Sviluppo
<p> 
    <ul>
        <li>Gestire output assegnazioni</li>
        <li>Creazioni maschere su ADAM per i risultati</li>
        <li>Integrazione con servizi esterni(Telegram e OptimoRoute)</li>
        <li>Attendere la risposta di Paolo per il nome💕</li>
    </ul>
</p>

</div>






# COSA CHIEDERE A CHATGPT

Gli appartamenti premium li puliranno solo cleaner premium mentre gli altri saranno puliti da cleaner standard
Quindi il codice assegnerà prima quelli standard poi quelli premium
Quello che intendo Io con "Priorità" è la sequenza con cui il cleaner deve pulire gli appartamenti. Quindi il cleaner se ha 4 appartamenti da pulire, avrà 4 priorità.
Quindi vorrei fare un codice che mi imposti le priorità in base al json degli apt, nello specifico in base all'orario di checkin. Se il check-in è alle 14 allora avrà priorità 1(sarà il primo apt che il cleaner pulirà nella sua giornata lavorativa) se invece l'orario di checkin è più tardi delle 14 avrà un altra priorità(non necessariamente priorità 2 può essere anche 3 o 4). 
Solo che ci sono dei parametri che deve considerare anche se l'apt con priorità 1 ed è grosso da pulire(la quantità di roba da pulire si comprende da 3 parametri principalemente in base ai pax_out/pax_in, tipologia_intervento, dimensione apt) 




Prende in seguito gli appartamenti, ognuno con le proprie specifiche, e calcola la priorità di ogni task in base agli orari di check-in e check-out.  
Inizia ad assegnare gli appartamenti con priorità più alta ai cleaner premium, valutando anche il loro orario di convocazione e scegliendo il migliore per quel task. Dopo il primo giro di assegnazioni, si passa a quelli successivi, dove vengono assegnati ulteriori appartamenti ai cleaner, valutando il tempo di pulizia, la grandezza degli appartamenti e la distanza da quello precedente. Si procede nello stesso modo anche per i cleaner standard.  
Infine, avendo la lista delle assegnazioni, questa viene passata all'area di controllo per rivederla e aggiustarla, se necessario. Successivamente, viene validata in una maschera sul gestionale dove sarà confermata

Dati che mancano per l'algoritmo
1 manca il conteggio delle ore
2 mancano i giorni di riposo
3 manca il minimo ore da contratto