document.addEventListener('DOMContentLoaded', function() {
    const leagueButtonsContainer = document.getElementById('league-buttons');
    const matchesContainer = document.getElementById('matches-container');
    const standingsContainer = document.getElementById('standings-container');
    
    // Crear el contenedor de detalles del partido y agregarlo al DOM
    const matchDetailsContainer = document.createElement('div');
    matchDetailsContainer.id = 'match-details-container';
    matchDetailsContainer.className = 'match-details-container';
    matchDetailsContainer.style.display = 'none'; // Inicialmente oculto
    const closeButton = document.querySelector('.close-standings');
    let cardsContainer = document.getElementById('cards-container');
    document.body.appendChild(matchDetailsContainer);
    const viewMoreButton = document.getElementById('view-more-button');

    const videoFrame = document.getElementById('videoFrame');
    closeButton.style.display = 'none';

    

    async function fetchChannels() {
        try {
            const response = await fetch('http://127.0.0.1:5000/canales');
            if (!response.ok) {
                throw new Error('No se pudieron obtener los canales');
            }
            const channels = await response.json();
            displayChannels(channels);
        } catch (error) {
            console.error(error);
        }
    }

    const channelImages = {
        'Azteca Deportes MX': 'azteca.png',
        'Claro Sports 1': 'claro.png',
        'DAZN 1 ES': 'dazn.png',
        'DAZN 2 ES': 'dazn.png',
        'DAZN LaLiga': 'dazn.png',
        'Dsports' : 'dsports.jpg',
        'Dsports 2' : 'dsports.jpg',
        'Dsports +' : 'dsports.jpg',
        'ESPN 1' : 'espn.png',
        'ESPN 2' : 'espn.png',
        'ESPN 3' : 'espn.png',
        'ESPN 4' : 'espn.png',
        'ESPN 5' : 'espn.png',
        'ESPN 6' : 'espn.png',
        'ESPN 7' : 'espn.png',
        'ESPN Deportes' : 'espn.png',
        'ESPN MX' : 'espn.png',
        'ESPN Premium Argentina' : 'espn.png',

        'Eurosports 1 ES' : 'eurosports.jpg',
        'Eurosports 2 ES' : 'eurosports.jpg',

        'Fox Deportes USA' : 'foxsport.png',
        'Fox Sports 1 (Argentina)' : 'foxsport.png',
        'Fox Sports 1 MX' : 'foxsport.png',
        'Fox Sports 2 (Argentina)' : 'foxsport.png',

        'Fox Sports 3 (Argentina)' : 'foxsport.png',
        'Fox Sports Premium' : 'foxsport.png',

        'GolPeru' : 'golperu.png',
        'Liga 1 MAX' : 'liga1.jpeg',

        'TNT Sports Argentina' : 'R.png',
        'TNT Sports Chile' : 'R.png',

        'TUDN USA' : 'tudn.png',
        'TV Pública' : 'tvpublica.jpeg',
        
        'Telefe' : 'telefe.jpeg',
        'TyC Sports' : 'tycsports.jpeg',

        'Win Sports' : 'winsports.png',
        'Win Sports +' : 'winsports.png',

        // Agrega más mapeos según sea necesario
    };
    
    function displayChannels(channels) {
        // Limpiar cualquier contenido existente
        cardsContainer.innerHTML = '';
    
        // Recorrer todos los canales y crear una tarjeta para cada uno
        Object.keys(channels).forEach(channelName => {
            const channelUrl = channels[channelName];
            
            // Obtener la URL de la imagen basada en el nombre del canal
            const imageUrl = channelImages[channelName] || 'path/to/default-image.png'; // Imagen por defecto si no hay mapeo
    
            // Crear el elemento de la tarjeta
            const cardElement = document.createElement('div');
            cardElement.className = 'card';
            cardElement.innerHTML = `
                <a href="#" class="card-link" data-link="${channelUrl}">
                    <div class="card-content">
                        <img src="${imageUrl}" class="card-image" />
                        <div class="card-info">
                           
                        </div>
                    </div>
                </a>
            `;
            
            // Agregar la tarjeta al contenedor
            cardsContainer.appendChild(cardElement);
        });
    
        // Agregar los event listeners a cada tarjeta
        document.querySelectorAll('.card-link').forEach(link => {
            link.addEventListener('click', function(event) {
                event.preventDefault();
                const channelUrl = event.currentTarget.getAttribute('data-link');
                showVideoPlayer(channelUrl);
            });
        });
    }
    
    
    
    
    
    function showVideoPlayer(url) {
        const videoPlayer = document.getElementById('video-player');
        const videoFrame = document.getElementById('video-frame');
    
        videoFrame.src = url;
        videoPlayer.style.display = 'flex';
    
        document.getElementById('close-video').addEventListener('click', () => {
            videoPlayer.style.display = 'none';
            videoFrame.src = ''; // Limpiar el src del iframe para detener el video
        });
    }

// Llamar a la función para obtener las tarjetas al cargar la página
fetchChannels();
//fetchCards();

    let allMatches = [];
    let currentFilter = localStorage.getItem('currentFilter') || null;

    const leagueNameMapping = {
        'Liga Alemana' : 'alemania',
        'Liga Argentina': 'primera',

        'Liga Chilena': 'chile',
        'Liga Colombiana': 'colombia',
        'Liga Paraguaya': 'paraguay',
        'Liga Brasilera': 'brasil',
        'Liga Holandesa': 'paisesbajos',
        'Liga Mexicana': 'mexico',
        'Liga Estadounidense': 'usa',
        'Liga Uruguaya': 'uruguay',
        'Liga Inglesa': 'inglaterra',

        'LIGA PROFESIONAL': 'primera',
        'Liga Española': 'espana',
        'Liga Italiana': 'italia',
        'Liga Francesa': 'francia',
        'LIGA FRANCIA': 'francia',
        'PREMIER LEAGUE': 'inglaterra',
        'SERIE A': 'italia',
        'LA LIGA': 'espana',
        'PRIMERA NACIONAL': 'bnacional',
        'B METRO': 'bmetro',
        'PRIMERA C': 'primerac',
        'Femenino': 'futbolfem',

    };

    // Agregar event listeners a los botones del encabezado
    const leagueButtons = document.querySelectorAll('main button');
    leagueButtons.forEach(button => {
        button.addEventListener('click', () => {
            const league = button.getAttribute('data-league');
            fetchStandings(league);
        });
    });
    

    document.addEventListener('DOMContentLoaded', () => {
        // Fetch cards data
        fetch('/cards')
            .then(response => response.json())
            .then(cards => {
                const cardsContainer = document.getElementById('cards-container');
                cards.forEach(card => {
                    const button = document.createElement('button');
                    button.textContent = card.text;
                    button.onclick = () => showVideoPlayer(card.link);
                    cardsContainer.appendChild(button);
                });
            })
            .catch(error => console.error('Error fetching cards:', error));
    });
    
    function showVideoPlayer(url) {
        const videoPlayer = document.getElementById('video-player');
        const videoFrame = document.getElementById('video-frame');
        
        // Aquí se ajusta la URL para que apunte al nuevo reproductor
        videoFrame.src = `${url}`;
        videoPlayer.style.display = 'flex';
        
        document.getElementById('close-video').addEventListener('click', () => {
            videoPlayer.style.display = 'none';
            videoFrame.src = ''; // Limpiar el src del iframe para detener el video
        });
    }
    
    
    document.getElementById('close-player').addEventListener('click', () => {
        const videoPlayer = document.getElementById('video-player');
        videoPlayer.style.display = 'none';
        document.getElementById('video-frame').src = ''; // Clear the video URL to stop playback
    });

    const dropdownLinks = document.querySelectorAll('.dropdown-content a');
    dropdownLinks.forEach(link => {
        link.addEventListener('click', (event) => {
            event.preventDefault();
            const league = event.target.getAttribute('data-league');
            localStorage.setItem('currentFilter', league);
            currentFilter = league;
            fetchMatches(league);
            fetchStandings(league);
        });
    });

    async function fetchMatches(filter = 'hoy') {
        let url;
        if (filter === 'ayer') {
            url = 'http://127.0.0.1:5000/results/ayer';
        } else if (filter === 'man') {
            url = 'http://127.0.0.1:5000/results/man';
        } else {
            url = 'http://127.0.0.1:5000/results';
        }

        fetch(url)
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                allMatches = data;
                if (currentFilter && !['ayer', 'man'].includes(currentFilter)) {
                    filterMatches(currentFilter);
                } else {
                    renderMatches(allMatches);
                }
                const leagues = new Set(data.map(match => match.leagueTitle));
                leagueButtonsContainer.innerHTML = '';

                const showAll = document.createElement('button');
                showAll.id = 'show-all';
                showAll.textContent = 'Hoy';
                showAll.addEventListener('click', () => {
                    localStorage.removeItem('currentFilter');
                    currentFilter = null;
                    renderMatches(allMatches);
                    standingsContainer.innerHTML = '';
                });
                leagueButtonsContainer.appendChild(showAll);

                const filters = [
                    { id: 'yesterday', text: 'Ayer', filter: 'ayer' },
                    { id: 'tomorrow', text: 'Mañana', filter: 'man' },
                ];

                filters.forEach(({ id, text, filter }) => {
                    const button = document.createElement('button');
                    button.id = id;
                    button.textContent = text;
                    button.addEventListener('click', () => {
                        localStorage.setItem('currentFilter', filter);
                        currentFilter = filter; 
                        fetchMatches(filter);
                        standingsContainer.innerHTML = '';
                    });
                    leagueButtonsContainer.appendChild(button);
                });

                leagues.forEach(league => {
                    const button = document.createElement('button');
                    button.textContent = league;
                    button.dataset.league = league;
                    button.addEventListener('click', () => {
                        localStorage.setItem('currentFilter', league);
                        currentFilter = league;
                        filterMatches(league);
                        fetchStandings(league);
                    });
                    leagueButtonsContainer.appendChild(button);
                });
            })
            .catch(error => console.error('Error fetching matches:', error));
    }

    function filterMatches(league) {
        const filteredMatches = allMatches.filter(match => match.leagueTitle === league);
        renderMatches(filteredMatches);
    }
    

    function renderMatches(matches) {
        matchesContainer.innerHTML = '';
    
        const matchesByLeague = matches.reduce((acc, match) => {
            if (!acc[match.leagueTitle]) {
                acc[match.leagueTitle] = [];
            }
            acc[match.leagueTitle].push(match);
            return acc;
        }, {});
    
        Object.keys(matchesByLeague).forEach(league => {
            const leagueContainer = document.createElement('div');
            leagueContainer.className = 'league-container';
    
            const leagueHeader = document.createElement('div');
            leagueHeader.className = 'league-header';
    
            const leagueTitle = document.createElement('h2');
            leagueTitle.textContent = league;
            leagueHeader.appendChild(leagueTitle);
    
            const showMatchesButton = document.createElement('button');
            showMatchesButton.textContent = 'Mostrar Partidos';
            showMatchesButton.className = 'show-matches-button';
            showMatchesButton.addEventListener('click', () => {
                const matchCards = leagueContainer.querySelectorAll('.match-card');
                matchCards.forEach(card => card.classList.toggle('hidden'));
                showMatchesButton.textContent = matchCards[0].classList.contains('hidden') ? 'Mostrar Partidos' : 'Ocultar Partidos';
            });
            leagueHeader.appendChild(showMatchesButton);
    
            leagueContainer.appendChild(leagueHeader);
    
            // Create a container for the matches
            const matchesList = document.createElement('div');
            matchesList.className = 'matches-list';
    
            matchesByLeague[league].forEach(match => {
                const matchCard = document.createElement('div');
                matchCard.className = 'match-card hidden'; // Initially hidden
    
                // Obtener las imágenes de los equipos
                const homeLogo = match.homeLogo || '/static/default-home-logo.png';
                const awayLogo = match.awayLogo || '/static/default-away-logo.png';
    
                const homeScorers = match.homeScorers.length > 0 
                    ? match.homeScorers.map(scorer => `${scorer.minute}' ${scorer.scorerName}`).join('<br>') 
                    : ''; 
    
                const awayScorers = match.awayScorers.length > 0 
                    ? match.awayScorers.map(scorer => `${scorer.minute}' ${scorer.scorerName}`).join('<br>') 
                    : ''; 
    
                matchCard.innerHTML = `
                    <p><strong>${match.homeTeam}</strong> vs <strong>${match.awayTeam}</strong></p>
                    <p class="score">${match.homeScore} - ${match.awayScore}</p>
                    <p>Estado: ${match.gameState || 'N/A'}</p>
                    <div class="team-container">
                        <div class="team">
                            <img src="${homeLogo}" alt="${match.homeTeam} Logo" class="team-logo">
                            <div class="scorers-list">${homeScorers}</div>
                        </div>
                        <div class="team">
                            <img src="${awayLogo}" alt="${match.awayTeam} Logo" class="team-logo">
                            <div class="scorers-list">${awayScorers}</div>
                        </div>
                    </div>
                `;
    
                if (match.image) {
                    const matchImage = document.createElement('img');
                    matchImage.src = match.image;
                    matchImage.alt = 'Imagen del partido';
                    matchImage.className = 'image';
                    matchCard.appendChild(matchImage);
                }
    
                matchCard.addEventListener('click', () => {
                    fetchMatchDetails(match.id);
                });
    
                matchesList.appendChild(matchCard);
            });
    
            leagueContainer.appendChild(matchesList);
            matchesContainer.appendChild(leagueContainer);
        });
    }
    
    
    

    function filterMatches(selectedLeague) {
        const filteredMatches = allMatches.filter(match => match.leagueTitle === selectedLeague);
        renderMatches(filteredMatches);
    }

    function closeMatchDetails() {
        matchDetailsContainer.style.display = 'none';
    }

    document.getElementById('close-match-details-btn').addEventListener('click', closeMatchDetails);

    function fetchStandings(league) {
        const leagueCode = leagueNameMapping[league];
        if (!leagueCode) {
            standingsContainer.innerHTML = '';
            standingsContainer.style.display = 'none'; // Asegúrate de ocultarlo si no hay datos
            return;
        }
        
        fetch(`http://127.0.0.1:5000/standings/${leagueCode}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                renderStandings(data);
                standingsContainer.style.display = 'block'; // Mostrar contenedor cuando hay datos
            })
            .catch(error => {
                console.error('Error fetching standings:', error);
                standingsContainer.innerHTML = `<p>Error al obtener la tabla de posiciones.</p>`;
                standingsContainer.style.display = 'none'; // Asegúrate de ocultarlo en caso de error
            });
    }
    

    function renderStandings(standings) {
        standingsContainer.innerHTML = '';
        const table = document.createElement('table');
        table.className = 'standings-table';
    
        const thead = document.createElement('thead');
        thead.innerHTML = `
            <tr>
                <th>Posición</th>
                <th>Equipo</th>
                <th>Puntos</th>
                <th>Jugados</th>
                <th>Ganados</th>
                <th>Empatados</th>
                <th>Perdidos</th>
                <th>GF</th>
                <th>GC</th>
            </tr>
        `;
        table.appendChild(thead);
    
        const tbody = document.createElement('tbody');
        standings.forEach(team => {
            const row = document.createElement('tr');
            row.innerHTML = `
            <td>${team.team}</td>
            <td>${team.played}</td>
            <td>${team.won}</td>
            <td>${team.drawn}</td>
            <td>${team.lost}</td>
            <td>${team.gf}</td>
            <td>${team.ga}</td>
            <td>${team.gd}</td>
            <td>${team.points}</td>
            `;
            tbody.appendChild(row);
        });
        closeButton.style.display = 'block';
        table.appendChild(tbody);
        standingsContainer.appendChild(table);
        closeButton.addEventListener('click', function() {
            standingsContainer.innerHTML = ''; // Ocultar los standings
            closeButton.style.display = 'none'; // Ocultar el botón
        });
    }

    function fetchMatchDetails(matchId) {
        fetch(`http://127.0.0.1:5000/ficha=${matchId}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                console.log('Datos del detalle del partido:', data);
                renderMatchDetails(data);
            })
            .catch(error => {
                console.error('Error fetching match details:', error);
                matchDetailsContainer.innerHTML = `<p>Error al obtener los detalles del partido.</p>
                                                    <button id="close-match-details">Cerrar</button>`;
                matchDetailsContainer.style.display = 'block';
                document.getElementById('close-match-details').addEventListener('click', () => {
                    matchDetailsContainer.style.display = 'none';
                });
        
                const closeButton = document.getElementById('close-match-details');
                if (closeButton) {
                    closeButton.addEventListener('click', () => {
                        matchDetailsContainer.style.display = 'none';
                    });
                }
            });
    }

    function renderMatchDetails(details) {
        // Verifica si los campos existen y asigna valores predeterminados si es necesario
        const yellowCardsLocal = details.amarillas_local || 'No hay tarjetas amarillas para el equipo local';
        const yellowCardsVisitor = details.amarillas_visitante || 'No hay tarjetas amarillas para el equipo visitante';
        const substitutions = details.cambios || 'No hay cambios';
        const goalsLocal = details.goles_local || 'No hay goles';
        const goalsVisitante = details.goles_visitante || 'No hay goles';
        const status = details.estado || 'N/A';
    
        matchDetailsContainer.innerHTML = `
            <button id="close-match-details">Cerrar</button>
            <h3>Detalles del Partido</h3>
            <p><strong>Estado:</strong> ${status}</p>
            <p><strong>Tarjetas Amarillas - Local:</strong> ${yellowCardsLocal}</p>
            <p><strong>Tarjetas Amarillas - Visitante:</strong> ${yellowCardsVisitor}</p>
            <p><strong>Cambios:</strong> ${substitutions}</p>
            <p><strong>Goles - Local:</strong> ${goalsLocal}</p>
            <p><strong>Goles - Visitante:</strong> ${goalsVisitante}</p>
        `;
        matchDetailsContainer.style.display = 'block';
    
        document.getElementById('close-match-details').addEventListener('click', () => {
            matchDetailsContainer.style.display = 'none';
        });

        const closeButton = document.getElementById('close-match-details');
        if (closeButton) {
            closeButton.addEventListener('click', () => {
                matchDetailsContainer.style.display = 'none';
            });
        }
        
    }
    
    // Suponiendo que fetchChannels y fetchMatches son funciones que has definido previamente
    async function setup() {
        await fetchChannels();
        const savedFilter = localStorage.getItem('currentFilter');
        if (savedFilter) {
            await fetchMatches(savedFilter);
        } else {
            await fetchMatches(currentFilter);
    }
}

// Llama a la función setup para inicializar los datos
setup();

// Actualiza los datos cada minuto (60000 milisegundos)
setInterval(async () => {
    await fetchMatches(currentFilter);
    }, 60000);
});
