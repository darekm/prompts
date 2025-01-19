## Rejestry VAT - powiązanie z polami w JPK_V7M 
[link poznajmadar](http://poznajmadar.blogspot.com/2016/08/rejetsry-vat-powiazanie-z-polami-vat-7.html)
Wprowadzając dokument do rejestru vatowskiego należy szczególnie zwrócić uwagę na kilka pól, które mają kluczowe znaczenie przy prawidłowym ich ujmowaniu w JPK_V7M (VAT7 + JPK_VAT).
-  rejestr - rejestr określonego typu dokumentów (FA_V,PZ,KSZ,korPZ)
-  daty - według których określany jest moment obowiązku podatkowego (okresu sprawozdawczego do którego przynależy),
-  rodzaj - zależnie od wybranego rejestru, wymagany dla niektórych dokumentów,
-  stawki - stawki podatku (w tym stawki szczególne jak "oo - odwrotne opodatkowanie, NOV - nie odliczany VAT, PB - nabycie paliw samochodowych"),
-  wariant - wariant podatku VAT wymagany przy niektórych dokumentach, mający bezpośredni wpływ na to do którego pola deklaracji dana kwota trafi oraz która data stanowy wyznacznik okresu opodatkowania.

 Poniższa tabela zawiera powiązanie poszczególnych dokumentów z polami w deklaracji VAT7 w zależności od wybranych parametrów danego dokumentu.
|rodzaj transakcji|Rejestr VAT  opcja: księgowość - rejestry VAT|pola w deklaracji:  VAT należny / JPK_V7M (VAT7_20 / JPK_VAT[3])|pola w deklaracji VAT naliczony JPK_V7M (VAT7_20 / JPK_VAT[3])|
|------|----|--|--|
|sprzedaż Faktury VAT  |Typ: FA_V // wariant VAT: [-- p u s t e --]   | VAT zw: 10 // VAT 0%: 13 // VAT 5%: 15, 16 // VAT 8%: pola: 17, 18 // VAT 23%: pola:19, 20  |	---|
|Odwrotne obsiążenie|przy zastosowaniu stawki* oo //nieaktualne (zastosowanie tylko do korekt deklaracji VAT7)| VAT należny: 31   |	---|
|Do pliku JPK pobierane są: //- DataWystawienia - data z pola: data FA //DataSprzedazy - data z pola: data VAT| --- |
|zakup materiałów| Typ: KSZ|---| pola 42,43|
|zakup usług  |Typ: KSZU|---| pola 42,43|
|PZ towary handlowe |Typ: PZ|---| pola 42,43|
|korekta zakupu| Typ: zwPZ|---| pola 42,43|
|korekta zakupu towarów |Typ: korPZ   |	VAT należny: ----| pola 42,43|
|zakup środków trwałych|Typ: SrTrw|VAT należny: ----|  VAT naliczony: 40, 41|
|Eksport usług | invoice NP Typ: Inv // księgowość - fakturowanie: // faktura NP - invoice// stawka vat:NP |wariant VAT: [-- p u s t e --] |VAT należny: pole 11|  |
|Eksport usług UE (art UE 28b)|invoice NP Typ: Inv , stawka vat NPe//wariant VAT: [opodatkowanie UE 28b]|	VAT należny: pole 12 //VAT-UE [usługi]  |	--- |
| eksport nie podlegający VAT                |wariant VAT: nie podlega VAT  |	VAT należny: ---   |	---|
|---|---|---|---|
|import usług|Typ: iusl  //  księgowość - fakturowanie: Import usług - IUSL|wariant VAT: [-- p u s t e --]// stawki: 23% ,NOV|	wg data VAT//VAT należny pole: 27, 28 |	wg data VAT// VAT naliczony pole:42, 43}|         "    |wariant VAT: [WNT Należny inny okres]| wg pola:	`data VAT`// VAT należny: 27, 28	|`data księgowania`// VAT naliczony pole: 42, 43||          "   | wariant VAT: [WNT Naliczony inny okres]|wg pola:	data księgowania//VAT należny pole: 27, 28|	`data VAT`//VAT naliczony 42, 43|
|          "   |wariant VAT: [opodatkowanie UE 28b]// 23%,OO,NOV (VAT 23%)|	wg data VAT//VAT należny pole: 29, 30| 	wg data VAT//VAT naliczony 42, 43|
|     "        |wariant VAT: [podatek rozlicza nabywca art 17 (32)]|	VAT należny: 31, 32|   |
|      "        |dowolny wariant VAT  [^2]|puste pole: `data VAT`|	wg `data VAT`//VAT należny: 29, 30  |  	wg `data VAT`|
[^2]:) Dla Importu usług z zastosowaniem stawek np. oo oraz inną datą VAT należnego i naliczonego należy wprowadzić 2 dokumenty:
1. Import usług - pozostawiając pole data VAT puste - dla VAT należnego
2. Nabycie wewnętrzne - dla VAT naliczonego
|import towarów|rejestr `vat od importu`, typ: FI|wariant VAT: [-- p u s t e --] 	|VAT należny: -- 	|VAT naliczony pola:42, 43|
|        "     |wariant VAT: [import bezpośredni 33a] |	VAT należny: 25, 26  |	VAT naliczony 42, 43|
|wewnętrzne nabycie NW|Typ: pw|wariant VAT: -- p u s t e --] 	VAT należny: -- 	VAT naliczony: 42, 43|
|Wewnątrz unijne nabycie| rejestr WNT Typ: WNT   |wariant VAT: [-- p u s t e --]|stawki:23%,NOV,ZW,(wntVatZwolnione=1) ZW,NP,//pola 23,24|VAT naliczony pola: 42, 43|
|                |wariant VAT: [WNT inny okres]|data księgowania:data VAT/|	wg data księgowania //VAT należny: 23, 24| -- 	wg data VAT   }
|rodzaj: korekta VAT należny//ulga na złe długi|korekta opodatkowania REK//Typ: potZ//data księgowania//data VAT|(+) VAT należny 19, 20//(-) VAT należny 19, 20//podstawa 68, VAT 69|------ //------|
|rodzaj: korekta VAT naliczony//ulga na złe długi|korekta opodatkowania REK//Typ: potZ//|-----//-----|(-) naliczony: 46//(+) naliczony: 47|
|rodzaj: korekta deklaracji p.44 śr Trwałe|| -- |(+) naliczony: 44|
|rodzaj: korekta deklaracji p.45 pozostałe|| -- |(+) naliczony: 45|
|rodzaj: podatek p.33 remanent|| (+) należny: 33|
|podatek p.34 kasy fiskalne  ||(+) należny: 34|
|podatek p.35 WNT środków transportu  ||  (-) należny: 35  |
|rodzaj: podatek p.36 WNT paliwo||(-) należny: 36|
