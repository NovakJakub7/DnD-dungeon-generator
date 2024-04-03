# DnD-dungeon-generator

## Obsah:
Repozitář obsahuje aplikační část bakalářské práce Procedurální generování lokací do hry typu Dungeons \& Dragons.
Více informací v textové části práce zde: [Bakalářská práce]([https://stag.upol.cz/portal/studium/prohlizeni.html?pc_phs=-2121444242&pc_mode=view&pc_windowid=10308&_csrf=dcf8255f-da10-4284-87aa-82eb30892b91&pc_phase=action&pc_pagenavigationalstate=AAAAAQAFMTAzMDgTAQAAAAEACHN0YXRlS2V5AAAAAQAULTkyMjMzNzIwMzY4NTQ3NjczMTgAAAAA&pc_type=portlet&pc_interactionstate=JBPNS_rO0ABXetAAlwcmFjZUlkbm8AAAABAAYyODQyNTIAEHByb2hsaXplbmlBY3Rpb24AAAABADpjei56Y3Uuc3RhZy5wb3J0bGV0czE2OC5wcm9obGl6ZW5pLnByYWNlLlByYWNlRGV0YWlsQWN0aW9uAAZkZXRhaWwAAAABAAlwcmFjZUluZm8ACHN0YXRlS2V5AAAAAQAULTkyMjMzNzIwMzY4NTQ3NjczMTgAB19fRU9GX18*&pc_windowstate=normal&pc_navigationalstate=JBPNS_rO0ABXctAAhzdGF0ZUtleQAAAAEAFC05MjIzMzcyMDM2ODU0NzY3MzE4AAdfX0VPRl9f#prohlizeniSearchResult](https://stag.upol.cz/StagPortletsJSR168/PagesDispatcherServlet?pp_destElement=%23ssSouboryStudentuDivId_17466&pp_locale=cs&pp_reqType=render&pp_portlet=souboryStudentuPagesPortlet&pp_page=souboryStudentuDownloadPage&pp_nameSpace=G10308&soubidno=338086) "Textová část práce")

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
