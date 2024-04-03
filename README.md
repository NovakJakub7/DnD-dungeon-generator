# DnD-dungeon-generator

## Obsah:
Repozitář obsahuje aplikační část bakalářské práce Procedurální generování lokací do hry typu Dungeons \& Dragons.
Více informací v textové části práce zde: [Bakalářská práce](https://theses.cz/id/bn0vo6/bp_novak.pdf?lang=cs, "Textová část práce")

## Postup zprovoznění webové aplikace:
(kroky 3 až 5 volitelné)

1. Stáhnout Python
Windows:	https://www.python.org/downloads/
Unix:		apt-get install python3

2. Stáhnout správce balíčků pip
pro Windows stažen společně s jazykem Python
Unix:		apt-get install python-3 pip

3. Instalovat Python virtual environemnt
Windows:	py -m pip install --user virtualenv
Unix:		sudo apt-get install python3.8-venv

4. Vytvořit Python virtual environment ve složce s balíčkem aplikace (adresářem dungeon_generator)
Windows:	py -m venv ./venv
Unix:		python3 -m venv ./venv

5. Aktivovat virtual environment
Windows:	.\venv\Scripts\activate
Unix:		source venv/bin/activate

6. Nainstalovat potřebné knihovny/balíčky z requirements.txt
Windows:	pip install -r requirements.txt
Unix:		pip3 install -r requirements.txt
		sudo apt-get install libvips

7. Zapnout Flask aplikaci
Windows:	py app.py
Unix:		python3 app.py

Webová aplikace bude dostupná na adrese: http://127.0.0.1:5000/ nebo http://localhost:5000/
