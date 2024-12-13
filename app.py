from flask import Flask, jsonify
import requests
from bs4 import BeautifulSoup
from flask_cors import CORS
import re

app = Flask(__name__)
CORS(app)

BASE_URL = 'https://www.promiedos.com.ar/'

def fetch_html(url):
    """Fetch HTML content from the given URL."""
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        app.logger.error(f"Request error: {e}")
        return None

def get_scorers_list(scorers_text):
    """Process the scorers text into a list of scorers."""
    if not scorers_text:
        return []

    scorers_list = [scorer.strip() for scorer in scorers_text.split(';') if scorer.strip()]
    result = []
    for scorer in scorers_list:
        parts = scorer.split("'")
        if len(parts) == 2:
            result.append({'minute': parts[0].strip(), 'scorerName': parts[1].strip()})
        else:
            app.logger.warning(f"Unexpected scorer format: {scorer}")
    return result

def safe_get_text(element, default=''):
    """Safely get text from a BeautifulSoup element."""
    return element.text.strip() if element else default

def safe_get_attr(element, attr, default=None):
    """Safely get an attribute from a BeautifulSoup element."""
    return element[attr].strip() if element and element.has_attr(attr) else default

def process_match_row(row, league_title, league_logo):
    """Process a row of match data."""
    try:
        columns = row.find_all('td')
        if len(columns) < 2:
            return None

        match_link = row.find('a', href=True)
        match_id = 'Unknown'
        if match_link and 'ficha=' in match_link['href']:
            match_id = match_link['href'].split('ficha=')[-1]

        game_state = safe_get_text(row.find(class_='game-fin')) or \
                     safe_get_text(row.find(class_='game-time')) or \
                     safe_get_text(row.find(class_='game-play'))

        if row.find(class_='game-fin'):
            game_state_display = "Finalizado"
        elif row.find(class_='game-play'):
            game_state_display = safe_get_text(row.find(class_='game-play'))
        elif row.find(class_='game-time'):
            game_state_display = f"Inicio: {safe_get_text(row.find(class_='game-time'))}"
        else:
            game_state_display = game_state

        teams = row.find_all(class_='game-t1')
        home_team_section = teams[0] if len(teams) > 0 else None
        away_team_section = teams[1] if len(teams) > 1 else None

        home_team = safe_get_text(home_team_section.find(class_='datoequipo'), 'Unknown') if home_team_section else 'Unknown'
        home_logo = safe_get_attr(home_team_section.find('img'), 'src') if home_team_section else None
        home_logo = f"{BASE_URL}{home_logo}" if home_logo else None

        away_team = safe_get_text(away_team_section.find(class_='datoequipo'), 'Unknown') if away_team_section else 'Unknown'
        away_logo = safe_get_attr(away_team_section.find('img'), 'src') if away_team_section else None
        away_logo = f"{BASE_URL}{away_logo}" if away_logo else None

        home_score = safe_get_text(row.find(class_='game-r1').find('span'), '0')
        away_score = safe_get_text(row.find(class_='game-r2').find('span'), '0')

        match = {
            'id': match_id,
            'leagueTitle': league_title,
            'leagueLogo': league_logo,
            'gameState': game_state_display,
            'homeTeam': home_team,
            'homeLogo': home_logo,
            'awayTeam': away_team,
            'awayLogo': away_logo,
            'homeScore': home_score,
            'awayScore': away_score,
            'homeScorers': [],
            'awayScorers': []
        }

        return match

    except Exception as e:
        app.logger.error(f"Error processing match row: {e}")
        return None

def extract_matches(soup):
    """Extract match data from the parsed HTML, including scorers and game time images."""
    matches = []
    rows = soup.find_all('tr', attrs={'name': ['nvp', 'vp']})

    if not rows:
        app.logger.warning("No rows found.")
        return []

    league_title = None
    league_logo = None

    for row in rows:
        try:
            # Buscar el título y logo de la liga (si está disponible)
            league_title_element = row.find_previous_sibling(class_='tituloin')
            if league_title_element:
                league_title = safe_get_text(league_title_element.find('a'), 'Unknown')
                league_logo = safe_get_attr(league_title_element.find('img'), 'src')
                league_logo = f"{BASE_URL}{league_logo}" if league_logo else None

            # Procesar la fila del partido
            match = process_match_row(row, league_title, league_logo)
            
            # Verificar si hay información de la hora del juego y alguna imagen dentro de 'game-time'
            game_time = row.find(class_='game-time')
            if game_time:
                time_text = game_time.get_text(strip=True)
                img_element = game_time.find('img')
                img_url = img_element['src'] if img_element else None

                if img_url and not img_url.startswith('http'):
                    img_url = f'{BASE_URL}{img_url}' 
                
                # Añadir la información de la hora e imagen al partido procesado
                match['time'] = time_text
                match['image'] = img_url if img_url else None

            # Añadir el partido a la lista de partidos si se procesó correctamente
            if match:
                matches.append(match)
                app.logger.info(f"Processed match: {match}")

            # Procesar la fila de los goleadores, si existe
            scorers_row = row.find(class_='goles')
            if scorers_row:
                td_elements = scorers_row.find_all('td')
                if len(td_elements) >= 2:
                    home_scorers_text = safe_get_text(td_elements[0])
                    away_scorers_text = safe_get_text(td_elements[1])

                    if matches:
                        # Actualizar los datos del partido con los goleadores
                        matches[-1]['homeScorers'] = get_scorers_list(home_scorers_text)
                        matches[-1]['awayScorers'] = get_scorers_list(away_scorers_text)
                        app.logger.info(f"Updated home scorers: {matches[-1]['homeScorers']}")
                        app.logger.info(f"Updated away scorers: {matches[-1]['awayScorers']}")

        except Exception as e:
            app.logger.error(f"Error processing row: {e}")

    return matches



def extract_table_positions(url):
    """Extract the table of positions from a given league URL."""
    html_content = fetch_html(url)
    if not html_content:
        app.logger.error(f"Failed to fetch content from {url}")
        return None

    soup = BeautifulSoup(html_content, 'html.parser')
    table = soup.find(class_='tablesorter1')
    if not table:
        app.logger.warning(f"No table found at {url}")
        return None

    rows = table.find_all('tr')
    positions = []
    for row in rows:
        cols = row.find_all('td')
        name_attr = row.get('name', None)
        if cols:
            # Extract additional info from the row's "name" attribute


            # Build the position dictionary
            position = {
                'team': safe_get_text(cols[0]),
                'played': safe_get_text(cols[1]),
                'won': safe_get_text(cols[2]),
                'drawn': safe_get_text(cols[3]),
                'lost': safe_get_text(cols[4]),
                'gf': safe_get_text(cols[5]),
                'ga': safe_get_text(cols[6]),
                'gd': safe_get_text(cols[7]),
                'points': safe_get_text(cols[8]),
                'name': row.get('name', None)
            }

            if name_attr:
                team_url = f"https://www.promiedos.com.ar/club={name_attr}"
                team_details = fetch_team_details(team_url)
                position['team_details'] = team_details


            positions.append(position)
            

    return positions

@app.route('/results', methods=['GET'])
@app.route('/results/<path:day>', methods=['GET'])
def get_results(day=None):
    url = f"{BASE_URL}{day}" if day else BASE_URL
    html_content = fetch_html(url)
    if not html_content:
        return jsonify({"error": "No se pudo acceder a la página"}), 500

    soup = BeautifulSoup(html_content, 'html.parser')
    matches = extract_matches(soup)

    if matches:
        return jsonify(matches)
    else:
        return jsonify({"error": "No se encontraron partidos en la página"}), 404

@app.route('/standings/<league_name>', methods=['GET'])
def get_standings(league_name):
    league_url = f"{BASE_URL}{league_name}"
    positions = extract_table_positions(league_url)
    if positions:
        return jsonify(positions)
    else:
        return jsonify({"error": "No se encontraron posiciones para la liga solicitada"}), 404


def fetch_team_details(url):
    """Fetch additional details for a team from the given URL."""
    html_content = fetch_html(url)
    if not html_content:
        app.logger.error(f"Failed to fetch content from {url}")
        return None

    soup = BeautifulSoup(html_content, 'html.parser')

    # Extract specific team details based on the page structure
    details = {
        'nombre': safe_get_text(soup.find('strong')),  # Nombre del equipo
        'nombreCompleto': safe_get_text(
            soup.find(text=re.compile(r'Nombre completo:')).find_parent().find_next('br').next_sibling
        ).strip() if soup.find(text=re.compile(r'Nombre completo:')) else "No encontrado",
        'fundado': safe_get_text(
            soup.find(text=re.compile(r'Fundación:')).find_parent().find_next('br').next_sibling
        ).split("(")[0].strip() if soup.find(text=re.compile(r'Fundación:')) else "No encontrado",
        'apodo': safe_get_text(
            soup.find(text=re.compile(r'Apodo:')).find_parent().find_next('br').next_sibling
        ).strip() if soup.find(text=re.compile(r'Apodo:')) else "No encontrado",
        'estadio': safe_get_text(
            soup.find(text=re.compile(r'Estadio local:')).find_parent().find_next('br').next_sibling
        ).strip() if soup.find(text=re.compile(r'Estadio local:')) else "No encontrado",
        'imagen': soup.find('div', class_='clubder').find('img')['src'] if soup.find('div', class_='clubder') else "No imagen encontrada"
    }
    return details


@app.route('/club=<name>', methods=['GET'])
def get_club_details(name):
    team_url = f"https://www.promiedos.com.ar/club={name}"
    team_details = fetch_team_details(team_url)
    if team_details:
        return jsonify(team_details)
    else:
        return jsonify({"error": "Failed to fetch team details"}), 500



@app.route('/ficha=<match_id>', methods=['GET'])
def get_ficha(match_id):
    match_url = f"{BASE_URL}ficha={match_id}"
    html_content = fetch_html(match_url)
    if not html_content:
        return jsonify({"error": "No se pudo acceder a la página del partido"}), 500

    soup = BeautifulSoup(html_content, 'html.parser')
    content = extract_usoficha_to_estadisticas(soup)

    if content:
        parsed_data = parse_match_content(content)
        #parsed_data = content
        return jsonify(parsed_data)
    else:
        return jsonify({"error": "No se encontró el contenido entre 'usoficha' y 'ficha-estadisticas'"}), 404
    
def extract_usoficha_to_estadisticas(soup):
    """Extract content between 'usoficha' and 'ficha-estadisticas', if both are present."""
    try:
        usoficha_element = soup.find(attrs={'id': 'usoficha'})
        
        if not usoficha_element:
            app.logger.warning("Element 'usoficha' not found.")
            return None
        
        # Use find_all_next to get all elements starting from usoficha
        content_elements = usoficha_element.find_all_next(string=True)
        
        content = []
        for element in content_elements:
            # Stop if we reach ficha-estadisticas
            if element == soup.find(attrs={'id': 'ficha-estadisticas'}):
                break
            content.append(element.strip())

        return "\n".join(content)
    
    except Exception as e:
        app.logger.error(f"Error extracting content: {e}")
        return None


import re

def parse_match_content(content):
    # Define regex patterns for different sections
    estado_pattern = re.compile(r"(Finalizado|Entretiempo|Inicio: .+|En juego|Suspendido)")
    goles_pattern = re.compile(r"GOLES\n(.*?)\n(AMARILLAS|ROJAS)", re.DOTALL)
    amarillas_pattern = re.compile(r"AMARILLAS\n(.*?)\nCAMBIOS", re.DOTALL)
    cambios_pattern = re.compile(r"CAMBIOS\n(.*?)\n", re.DOTALL)
    
    # Extract sections using regex
    estado_match = estado_pattern.search(content)
    goles_match = goles_pattern.search(content)
    amarillas_matches = amarillas_pattern.findall(content)
    cambios_match = cambios_pattern.search(content)
    
    # Prepare variables to hold goal information
    goles_local = "No hay"
    goles_visitante = "No hay"
    
    if goles_match:
        goles_text = goles_match.group(1).strip()

        # Split the text of the goals into lines
        goles_lines = goles_text.split('\n')

        # Assuming we know the teams are organized in some clear way
        # For this example, let's assume the content includes team identifiers like "local" or "visitante"
        local_goals = []
        visitante_goals = []

        # Loop through each line and decide if it belongs to local or visitante
        for line in goles_lines:
            # Check if this line mentions local or visitante
            if "local" in line.lower():
                local_goals.append(line.strip())
            elif "visitante" in line.lower():
                visitante_goals.append(line.strip())
            else:
                # If we don't know, assume it's general (adjust this logic to your real case)
                local_goals.append(line.strip())

        # Join results back into strings
        goles_local = "\n".join(local_goals) if local_goals else "No hay"
        goles_visitante = "\n".join(visitante_goals) if visitante_goals else "No hay"

    # Prepare result dictionary
    result = {
        "estado": estado_match.group(0) if estado_match else "En juego",
        "goles_local": goles_local,
        "goles_visitante": goles_visitante,
        "amarillas_local": amarillas_matches[0].strip() if len(amarillas_matches) > 0 else "No hay",
        "amarillas_visitante": amarillas_matches[1].strip() if len(amarillas_matches) > 1 else "No hay",
        "cambios": cambios_match.group(1).strip() if cambios_match else "No hubo",
    }
    
    return result






def extract_cards_from_containers(soup):
    """Extract card elements within card-container and their links from the parsed HTML."""
    card_containers = soup.find_all(class_='card-container')
    extracted_data = []

    for container in card_containers:
        cards = container.find_all(class_='card')
        for card in cards:
            link_element = card.find('a', href=True)
            if link_element:
                link_url = link_element['href']
                
                # Excluir los enlaces que no deseas scrapeear
                if link_url in ["/en-vivo/fox-sports-2-en-vivo-por-internet", "/en-vivo/fox-sports-3-en-vivo-por-internet"]:
                    continue

                extracted_data.append({
                    'link': link_url,
                    'text': safe_get_text(link_element)
                })
    
    return extracted_data


def fetch_and_scrape_links(base_url, links):
    """Fetch and scrape each link, appending the base URL to form the full URL."""
    scraped_data = []

    for link in links:
        full_url = f"{base_url}{link}"
        html_content = fetch_html(full_url)
        if not html_content:
            app.logger.error(f"Failed to fetch content from {full_url}")
            continue

        # Process the content of each URL as needed
        soup = BeautifulSoup(html_content, 'html.parser')
        # Extract specific data from each page if needed
        # For demonstration, just collecting the URL and a short excerpt of the content
        page_data = {
            'url': full_url,
            'content_excerpt': soup.get_text()[:200]  # Extract a short excerpt from the page content
        }
        scraped_data.append(page_data)

    return scraped_data


def fetch_video_frame_url(base_url, links):
    """Fetch the URL of the video frame from each channel link."""
    video_frames = []

    for link in links:
        full_url = f"{base_url}{link}"
        html_content = fetch_html(full_url)
        if not html_content:
            app.logger.error(f"Failed to fetch content from {full_url}")
            continue

        soup = BeautifulSoup(html_content, 'html.parser')
        iframe = soup.find('iframe', id='videoFrame')

        if iframe:
            video_frame_url = safe_get_attr(iframe, 'src')
            video_frames.append({
                'url': full_url,
                'videoFrameUrl': video_frame_url
            })
        else:
            app.logger.warning(f"No iframe with id 'videoFrame' found at {full_url}")

    return video_frames


@app.route('/video-frames', methods=['GET'])
def video_frames():
    base_url = 'https://rojadirectaenhd.net/'
    
    # Simulating the previously obtained links
    links = [
        "/en-vivo/liga-1-max",
        "/en-vivo/win-sports-premium",
        "/en-vivo/espn-en-vivo-por-internet",
        "/en-vivo/espn-2-en-vivo-por-internet",
        "/en-vivo/espn-3-en-vivo-por-internet",
        "/en-vivo/fox-sports-en-vivo-por-internet",
        "/en-vivo/espn-premium-en-vivo-por-internet",
        "/en-vivo/tnt-sports-en-vivo-por-internet"
    ]
    
    video_frames = fetch_video_frame_url(base_url, links)

    if video_frames:
        return jsonify(video_frames)
    else:
        return jsonify({"error": "No se encontró el reproductor de video en las URLs proporcionadas"}), 404



@app.route('/scrape-links', methods=['GET'])
def scrape_links():
    base_url = 'https://rojadirectaenhd.net/'
    
    # Simulating the previously obtained links
    links = [
        "/en-vivo/liga-1-max",
        "/en-vivo/win-sports-premium",
        "/en-vivo/espn-en-vivo-por-internet",
        "/en-vivo/espn-2-en-vivo-por-internet",
        "/en-vivo/espn-3-en-vivo-por-internet",
        "/en-vivo/fox-sports-en-vivo-por-internet",
        "/en-vivo/espn-premium-en-vivo-por-internet",
        "/en-vivo/tnt-sports-en-vivo-por-internet"
    ]
    
    scraped_data = fetch_and_scrape_links(base_url, links)

    if scraped_data:
        return jsonify(scraped_data)
    else:
        return jsonify({"error": "No se pudo obtener datos de las URLs proporcionadas"}), 404
    



@app.route('/cards', methods=['GET'])
def get_cards():
    url = 'https://rojadirectaenhd.net/'
    html_content = fetch_html(url)
    if not html_content:
        return jsonify({"error": "No se pudo acceder a la página"}), 500

    soup = BeautifulSoup(html_content, 'html.parser')
    card_data = extract_cards_from_containers(soup)

    if card_data:
        return jsonify(card_data)
    else:
        return jsonify({"error": "No se encontraron tarjetas en la página"}), 404


@app.route('/card-containers', methods=['GET'])
def get_card_containers():
    url = 'https://rojadirectaenhd.net/'
    html_content = fetch_html(url)
    if not html_content:
        return jsonify({"error": "No se pudo acceder a la página"}), 500

    soup = BeautifulSoup(html_content, 'html.parser')
    card_data = extract_cards_from_containers(soup)

    if card_data:
        return jsonify(card_data)
    else:
        return jsonify({"error": "No se encontraron contenedores de tarjetas en la página"}), 404
    


@app.route('/canales')
def get_cardss():
    channels = {
            'ESPN 1': 'https://streamtp.live/global1.php?stream=espn1',
            'ESPN 2': 'https://streamtp.live/global1.php?stream=espn2',
            'ESPN 3': 'https://streamtp.live/global1.php?stream=espn3',
            'ESPN 5': 'https://streamtp.live/global1.php?stream=espn5',
            'ESPN 6': 'https://streamtp.live/global1.php?stream=espn6',
            'ESPN 7': 'https://streamtp.live/global1.php?stream=espn7',
            'Win Sports +': 'https://streamtp.live/global1.php?stream=winplus',
            'Win Sports': 'https://streamtp.live/global1.php?stream=winsports',
            'Fox Sports 1 (Argentina)': 'https://streamtp.live/global1.php?stream=fox1ar',
            'Fox Sports 2 (Argentina)': 'https://streamtp.live/global1.php?stream=fox2ar',
            'Fox Sports 3 (Argentina)': 'https://streamtp.live/global1.php?stream=fox3ar',
            'Dsports': 'https://streamtp.live/global1.php?stream=dsports',
            'Dsports 2': 'https://streamtp.live/global1.php?stream=dsports_2',
            'Dsports +': 'https://streamtp.live/global1.php?stream=dsports_plus',
            'TNT Sports Chile': 'https://streamtp.live/global1.php?stream=tnt_chile',
            'TNT Sports Argentina': 'https://streamtp.live/global1.php?stream=tntsports_argentina',
            'ESPN Premium Argentina': 'https://streamtp.live/global1.php?stream=espn_premium',
            'TyC Sports': 'https://streamtp.live/global1.php?stream=tyc_sports',
            'Telefe': 'https://streamtp.live/global1.php?stream=telefe',
            'TV Pública': 'https://streamtp.live/global1.php?stream=tv_publica',
            'Liga 1 MAX': 'https://streamtp.live/global1.php?stream=l1max',
            'GolPeru': 'https://streamtp.live/global1.php?stream=golperu',
            'ESPN Deportes': 'https://streamtp.live/global1.php?stream=espn_deportes',
            'TUDN USA': 'https://streamtp.live/global1.php?stream=tudn_usa',
            'Fox Deportes USA': 'https://streamtp.live/global1.php?stream=fox_deportes_usa',
            'Claro Sports 1': 'https://streamtp.live/global1.php?stream=clarosports1',
            'Azteca Deportes MX': 'https://streamtp.live/global1.php?stream=azteca_deportes',
            'Fox Sports 1 MX': 'https://streamtp.live/global1.php?stream=foxsportsmx',
            'Fox Sports Premium': 'https://streamtp.live/global1.php?stream=foxsportspremium',
            'ESPN MX': 'https://streamtp.live/global1.php?stream=espnmx',
            'Eurosports 1 ES': 'https://streamtp.live/global1.php?stream=eurosports1_es',
            'Eurosports 2 ES': 'https://streamtp.live/global1.php?stream=eurosports2_es',
            'DAZN 1 ES': 'https://streamtp.live/global1.php?stream=dazn1',
            'DAZN 2 ES': 'https://streamtp.live/global1.php?stream=dazn2',
            'DAZN LaLiga': 'https://streamtp.live/global1.php?stream=dazn_laliga'
    }
    return jsonify(channels)


##if __name__ == '__main__':
    #app.run(host='0.0.0.0', port=5000)

