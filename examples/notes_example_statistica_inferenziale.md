## Statistica inferenziale – test di ipotesi

Il test di ipotesi è un procedimento statistico che parte dall'assunzione di un'ipotesi nulla ($H_0$), ad esempio "la media è 5", e confronta questa con un'ipotesi alternativa ($H_1$) che può essere direzionale (maggiore o minore) o non direzionale (diversa da 5). Dopo aver raccolto i dati, si calcola il valore $p$-per osservare un risultato così estremo o più estremo assumendo che l'ipotesi nulla sia vera, con la fondamentale distinzione che la $p$-value non rappresenta la probabilità che l'ipotesi nulla sia vera. Se la $p$-value è inferiore a un livello di significatività $\alpha$ (solitamente 0,05), si rifiuta l'ipotesi nulla, ma questo rifiuto non implica che l'ipotesi alternativa sia vera al 100%, bensì che i dati osservati sono incompatibili con l'ipotesi nulla.

## Errori e potenza del test

Esistono due tipi di errori statistici: il tipo I, che consiste nel rifiutare un'ipotesi nulla vera (falso positivo) con una probabilità pari a $\alpha$, e il tipo II, che è il mancato rifiuto di un'ipotesi nulla falsa (falso negativo) con probabilità $\beta$. La potenza del test, definita come $1 - \beta$, rappresenta la probabilità di rilevare correttamente un effetto ed è influenzata dal dimensionamento del campione, dall'effetto size e dal livello di significatività $\alpha$.

## Test statistici più comuni

I test statistici più utilizzati includono il $t$-test per confrontare le medie di uno o due campioni assumendo la normalità, il test del $\chi^2$ per analizzare variabili categoriche e tabelle di contingenza, l'ANOVA per confrontare più di due medie (one way o two way), i test non parametrici di Mann-Whitney e Wilcoxon quando la normalità non è soddisfatta, e il test di Kolmogorov-Smirnov per verificare l'uguaglianza tra due distribuzioni.

## Testing multiplo e correzioni

Quando si eseguono numerosi test sullo stesso dataset, il rischio di ottenere falsi positivi aumenta esponenzialmente, un fenomeno noto come $p$-hacking. Per mitigare questo problema si possono applicare correzioni come quella di Bonferroni, che divide $\alpha$ per il numero di test, o la correzione FDR di Benjamini-Hochberg.

## Intervalli di confidenza e interpretazioni

Un intervallo di confidenza al 95% indica che, se ripetessimo l'esperimento infinite volte, il 95% degli intervalli calcolati conterrebbe il vero parametro; è fondamentale notare che non si può affermare che esista un 95% di probabilità che il parametro specifico sia contenuto nell'intervallo attuale, poiché questa è un'interpretazione bayesiana.

## Approccio frequentista e bayesiano

La distinzione tra approcci frequentista e bayesiano risiede nella visione del parametro: i frequentisti lo considerano fisso e i dati come variabili casuali, mentre i bayesiani invertono questo ruolo. Nel framework bayesiano, si combina una prior con una likelihood per ottenere una posterior attraverso il teorema di Bayes. Sebbene il corso si basi principalmente sull'approccio frequentista, il professore ha sottolineato che nell'industria attuale l'uso di metodi bayesiani è molto diffuso, spesso supportato da framework come PyMC o Stan.

## Scelta tra t-test e z-test

Un dubbio frequente riguarda la scelta tra $t$-test e $z$-test: il $z$-test si utilizza quando si conosce la varianza vera della popolazione, condizione rara nella realtà, mentre il $t$-test è applicabile quando la varianza viene stimata dal campione. Quando il dimensionamento del campione è grande, i risultati dei due test tendono a coincidere.