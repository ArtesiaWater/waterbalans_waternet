# Waterbalansen in Python

Deze repository bevat de scripts om de waterbalansen van Waternet te runnen,
zoals uitgewerkt door Maarten Ouboter in de Excel Waterbalansen. De waterbalans
module zelf is beschikbaar via [deze
repository](https://github.com/ArtesiaWater/waterbalans).

Auteurs:

- R.A. Collenteur, Artesia Water 2018
- D.A. Brakenhoff, Artesia Water 2018

<img src="https://github.com/ArtesiaWater/waterbalans/blob/master/logo.png?raw=true" alt="Logo Waterbalansen" width="100"/>

## Installatie

- Er is geen installatie nodig voor het runnen van deze scripts. Download de
bestanden door de repository te clonen via b.v. GitHub Desktop of via de
website zelf.

- Wel moet de waterbalans module geinstalleerd zijn. Zie daarvoor de
[instructies op de github pagina voor deze
module](https://github.com/ArtesiaWater/waterbalans#installatie).

- De `environment.yml` file bevat een lijst met alle benodigde Python packages.
Voor het maken van een environment gebruik `conda create -n <jouw naam hier> -f
environment.yml`

## Data

De data voor het runnen van de waterbalansen wordt meegeleverd in deze
repository. Dit is een snapshot van de export vanuit de Waterbalansen Database.
Voor het uitpakken en klaarzetten van de data zie het script
`prepare_input_data.py` in de waterbalansen_scripts map.

## Project Groep

- Maarten Wensing (Projectleider)
- Jan Willem Voort (Gebruiker)
- Laura Moria (Gebruiker)
- Maarten Ouboter (Maker Excel-balans)
- Davíd Brakenhoff (Python Programmeur)
- Ben Staring (FEWS)
- Stefan Fritz (GIS)
- Jeroen van Schijndel (Waterbalansen Database)

Niet langer betrokken maar veel belangrijk werk verricht in de eerste fase:

- Pytrik Graafstra (Conceptueel overzicht)
- Raoul Collenteur (Python Programmeur)
