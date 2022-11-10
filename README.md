# KIV/DS - 1. úkol

## Volba leadera

K volbě leadera (mastera) jsem využil Bully algoritmus (
viz [https://en.wikipedia.org/wiki/Bully_algorithm](https://en.wikipedia.org/wiki/Bully_algorithm)),
který za předpokladu splnění několika předpokladů dokáže spolehlivě zvolit leadera.
Hlavní předpoklady algoritmu pro první úkol:

- doručování zpráv mezi nody je možné považovat za spolehlivé
- každý node zná všechny ostatní nody a dokáže s nimi napřímo komunikovat

Tyto podmínky jsem schopni splnit. Pro účely této semestrální práce je do environmentu (env)
přidána pro každý node hodnota IP_NETWORK ve formátu XXX.XXX.XXX, která určuje první část IP adresy. Dále
je jako předáván parametr IP_OFFSET, který určuje IP adresu prvního nodu. V tomto cvičení
systém předpokládá, že jsou IP adresy všech nodů za sebou, každou IP adresu je tedy možné dopočítat přičtením
čísla nodu k IP_OFFSET.

### Algoritmus volby

Existují 3 základní zprávy:

- ELECTION: oznámení o konání volby.
- ANSWER: odpověď na oznámení o volbě
- VICTORY: oznámení ostatním, že se daný node stal leaderem

Při spuštění nodu P (nebo v budoucnu ve chvíli, kdy dojde k obnově P), P vykoná následující akce:

- Pokud má P nejvyšší ID, samovolně se prohlásí za leadera a všem pošle VICTORY zprávu (žádný jiný node nemá vyšší ID)
- P pošle všem nodům s vyšším ID (ty se teoreticky mohou stát leaderem) zprávu typu ELECTION. Pokud žádný z nich
  neodpoví v časovém limitu, P se prohlásí za leadera a opět to oznámí ostatním nodům zprávou VICTORY.
- Pokud P obdrží ANSWER od nodu s vyšším ID, nepodniká v této volbě žádné kroky. Pokud nedojde ke zvolení leadera do
  určitého času, začne novou volbu (podle stejných pravidel)
- Pokud P obdrží ELECTION zprávu od nodu s nižším ID, odpoví na ni zprávou typu ANSWER a pokud zrovna neprobíhá žádná
  volba, tak volby zahájí
- Pokud P obdrží zprávu typu VICTORY, bude jejího odesílatele považovat za leadera.

### Zjištění stavu nodů

Poté, co je zvolen nový leader, vyšle tento nový leader zprávu typu PING na všechny nody. Jakmile jakýkoliv node
obdrží zprávu tohoto typu, okamžitě odpoví zprávou typu PONG. Při obdržení zprávy PONG je node označen za živého.

## Spuštění

Celý cluster je možné spustit příkazem: <code>vagrant up</code>

Jednotlivé uzly na standardní výstup vypisují všechny podstatné události a změny.

Počet nodů je možné upravit změnou parametru <code>NODES_COUNT</code> v souboru <code>Vagrantfile</code>

Ve výpisu barev z pohledu leadera: "-" značí, že daný node neodpovídá na ping, z toho důvodu nemá přidělenou barvu. Pozice v poli odpovídá ID nodu (indexováno od 0)

## Implementace

Veškerý kód je implementován v Pythonu (vyvíjeno a testováno v Pythonu verze 3.9.6 v prostředí macOS 13.0 a Dockeru
4.12.0). Protože vývoj probíhal na macOS na zařízení s procesorem s ARM architekturou, nebylo možné využít předvytvořený
dockerfile, vytáhl jsem si proto příkazy prováděné v původním dockerfilu a za ně jsem přidal vlastní. Pro lepší možnosti
cachování bych mohl do budoucna docker image otagovat.

### Struktura projektu
- **main.py**: vstupní bod programu, obsahuje obsluhu Flask serveru
- **node.py**: obsluha nodu, udržování stavových informací a logika spojená s volbou leadera
- **cluster.py**: obsluha clusteru, uchovává informace o všech nodech, poskytuje funkce spojené s více nody, řeší obarvování nodů
- messaging.py: soubor zodpovědný za odesílání zpráv
- consts.py: soubor obsahující základní konstanty (které se nenačítají z ENV)
- utils.py: základní podpůrné funkce

### Využívané knihovny

Flask - webový server, zpřístupnění HTTP endpointů
Requests - vytváření HTTP requestů
jsonpickle - manipulace s JSON (encode, decode)