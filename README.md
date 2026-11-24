# Catalog de note

Proiect individual la disciplina Metode avansate de programare, anul universitar 2026-2027.

## Autor

- **Nume:** Dieaconu Rebeca
- **Grupa:** 1.1
- **Marca:** ....
- **Tema:** 3 - Catalog de note

## Descriere

Aplicatia este un catalog digital simplu care gestioneaza studentii, notele pe discipline, calculul mediilor si rapoartele pe materie, reducand erorile de calcul si oferind acces rapid la situatie.

## Tehnologii

Python 3.13 cu Flask

## Rulare

```
docker build -t map-proiect .
docker run -d -p 8080:8080 map-proiect
```

Aplicatia asculta pe portul 8080. Verificati:

```
curl http://localhost:8080/health
curl http://localhost:8080/version
```

## Testare

```
pip install -r requirements.txt pytest pytest-cov
py -m pytest --cov=src
```

## Rutele implementate

| Ruta | Metoda | Descriere |
|---|---|---|
| `/health` | GET | Starea serviciului |
| `/version` | GET | Versiunea si commit-ul din care a fost construita imaginea |
| `/` | GET | Pagina de prezentare |
| `/reset` | POST | Goleste datele din memorie |
| `/students` | POST | Adauga un student (`name` si `group` obligatorii) |
| `/students` | GET | Listeaza studentii sortati dupa nume, optional filtrati dupa `?group=` |
| `/grades` | POST | Adauga o nota (1..10, maxim 5 note per disciplina) |
| `/students/<student_id>/grades` | GET | Returneaza notele unui student si media calculata |
| `/report` | GET | Returneaza raportul statistic pe o disciplina (`?subject=...`) |

## Decizii de implementare

1. **Stocarea datelor in memorie:** Am stocat studentii si notele in structuri de date Python (`Store`), cu suport pentru filtrarea studentilor dupa grupa si calculul statisticilor.
2. **Validarea notelor la introducere:** Am restrictionat notele la valori intregi de la 1 la 10 (maxim 5 note per disciplina pentru acelasi student) inainte de salvare pentru a preveni datele invalide.
3. **Calculul mediilor:** Am optat pentru calcularea mediilor direct la cerere, rotunjite la 2 zecimale (`ROUND_HALF_UP`), pentru a pastra valoarea mereu actualizata.