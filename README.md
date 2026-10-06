# Catalog de note

Proiect individual la disciplina Metode avansate de programare, anul universitar 2026-2027.

## Autor

- **Nume:** Dieaconu Rebeca
- **Grupa:** 1.1
- **Marca:** LH715680
- **Tema:** 3 - Catalog de note

## Descriere

Aplicatia este un catalog digital simplu care automatizeaza gestionarea notelor, absentelor si calculul mediilor pentru elevi. Aceasta elimina evidenta manuala pe hartie si reduce erorile de calcul, oferind acces rapid si la situatia scolara.

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
python -m pytest --cov=src
```

## Rutele implementate

| Ruta | Metoda | Descriere |
|---|---|---|
| `/health` | GET | Starea serviciului |
| `/version` | GET | Versiunea si commit-ul din care a fost construita imaginea |
| `/` | GET | Pagina de prezentare |
| `/reset` | POST | Goleste datele din memorie |
| `/note` | GET | Listeaza toate notele elevilor|
| `/note` | POST | adauga o nota noua |
| `/medie` | GET | Calculeaza media unui elev |
| `/absenta` | POST |  Inregistreaza o absenta |
| `/elevi` | POST | Adauga un elev in catalog |

## Decizii de implementare

1. **Stocarea datelor in memorie:** Am stocat elevii si notele in structuri de date Python (dictionare si liste).
2. **Validarea notelor la introducere:** Am restrictionat notele la valori de la 1 la 10 inainte de salvare pentru a preveni salvarea datelor invalide sau eronate in catalog.
3. **Calculul mediilor:** Am optat pentru calcularea mediilor direct la cerere, pe baza notelor existente, pentru a garanta ca valoarea este mereu actualizata corect la adaugarea sau stergerea unei note.