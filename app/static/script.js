document.addEventListener('DOMContentLoaded', () => {
    const input = document.getElementById('guessInput');
    const suggestions = document.getElementById('suggestions');
    // const resultsDiv = document.getElementById('results'); // Déjà déclaré plus bas si besoin, mais on garde la portée
    let gameOver = false;
    
    // Variable pour suivre la position dans la liste (-1 = rien sélectionné)
    let currentFocus = -1;

    let attempts = 0;
    let allSnippets = [];

    let currentMode = 'daily'; 

    const initialSnippetDiv = document.querySelector('#lyrics-container .snippet');
    if (initialSnippetDiv) {
        // On nettoie les guillemets éventuels
        allSnippets = [initialSnippetDiv.innerText.replace(/"/g, '')]; 
    }

    // --- GESTION DES MODES ---
    async function switchMode(mode) {
        console.log("Mode changé vers : " + mode);
        currentMode = mode;
        
        // Update visuel des boutons
        document.getElementById('btn-daily').classList.toggle('active', mode === 'daily');
        document.getElementById('btn-unlimited').classList.toggle('active', mode === 'unlimited');
        
        // Reset du jeu (vide la grille, reset les essais)
        resetGameUI();
        document.getElementById('next-song-container').style.display = 'none';

        if (mode === 'daily') {
            // Recharger la page pour ravoir la daily (plus simple)
            window.location.reload(); 
        } else {
            // Lancer une partie illimitée
            await startUnlimitedGame();
        }
    }

    const btnDaily = document.getElementById('btn-daily');
    const btnUnlimited = document.getElementById('btn-unlimited');

    if (btnDaily) {
        btnDaily.addEventListener('click', () => switchMode('daily'));
    }

    if (btnUnlimited) {
        btnUnlimited.addEventListener('click', () => switchMode('unlimited'));
    }

    async function startUnlimitedGame() {
        resetGameUI();
        document.getElementById('next-song-container').style.display = 'none';
        
        // Appel au backend pour piocher une nouvelle chanson
        try {
            const res = await fetch('/api/start_unlimited');
            const data = await res.json();
            
            // Mise à jour du premier snippet
            allSnippets = [data.snippet];
            attempts = 0;
            updateLyricsDisplay();
            
        } catch (e) { console.error(e); }
    }

    function resetGameUI() {
        // Vide les résultats
        document.getElementById('results').innerHTML = '';
        // Vide les paroles
        document.getElementById('lyrics-container').innerHTML = '';
        allSnippets = [];
        attempts = 0;
        gameOver = false;
        document.getElementById('guessInput').disabled = false;
        document.getElementById('guessInput').value = '';
        document.getElementById('guessInput').focus();
        // Cache la modal de victoire si elle est ouverte
        document.getElementById('winModal').style.display = 'none';
    }

    // --- 1. Autocomplétion & Navigation ---
    
    input.addEventListener('input', async function() {
        if (gameOver) return;
        const val = this.value;
        
        // Reset du focus quand on écrit
        currentFocus = -1;

        if (val.length < 2) { 
            suggestions.innerHTML = ''; 
            return; 
        }
        
        try {
            const res = await fetch(`/api/search?q=${encodeURIComponent(val)}`);
            const data = await res.json();
            
            suggestions.innerHTML = '';
            
            if (data.length === 0) return;

            data.forEach(s => {
                const li = document.createElement('li');
                // On met en gras la partie qui correspond à la recherche (optionnel mais sympa)
                // Ici on affiche simplement Titre - Artiste
                li.innerHTML = `<span class="song-title">${s.title}</span> <span class="artist-hint">${s.artist}</span>`;
                
                li.addEventListener('click', () => makeGuess(s.title));
                suggestions.appendChild(li);
            });
        } catch (e) { console.error(e); }
    });

    // --- GESTION DU CLAVIER (FLÈCHES + ENTRÉE) ---
    input.addEventListener('keydown', function(e) {
        let items = suggestions.getElementsByTagName('li');
        
        if (e.key === 'ArrowDown') {
            currentFocus++;
            addActive(items);
        } else if (e.key === 'ArrowUp') {
            currentFocus--;
            addActive(items);
        } else if (e.key === 'Enter') {
            e.preventDefault(); // Empêcher la soumission du formulaire
            
            if (currentFocus > -1) {
                // Si un élément est sélectionné avec les flèches, on le "clique"
                if (items && items[currentFocus]) {
                    items[currentFocus].click();
                }
            } else if (items.length > 0) {
                // Si rien n'est sélectionné mais qu'il y a une liste, on prend le premier (comportement par défaut)
                items[0].click();
            }
        }
    });

    function addActive(items) {
        if (!items) return false;
        removeActive(items); // On nettoie d'abord
        
        // Boucle : si on descend trop bas, on remonte au début et inversement
        if (currentFocus >= items.length) currentFocus = 0;
        if (currentFocus < 0) currentFocus = (items.length - 1);
        
        // Ajouter la classe CSS
        items[currentFocus].classList.add("suggestion-active");
        
        // Scroll automatique si la liste est longue
        items[currentFocus].scrollIntoView({ block: 'nearest' });
    }

    function removeActive(items) {
        for (let i = 0; i < items.length; i++) {
            items[i].classList.remove("suggestion-active");
        }
    }

    function updateLyricsDisplay() {
    const container = document.getElementById('lyrics-container');
    if (!container) return;

    // On vide tout pour reconstruire proprement (évite les doublons)
    container.innerHTML = ''; 

    // Sécurité : Si on n'a pas de snippets, on ne fait rien
    if (!allSnippets || allSnippets.length === 0) return;

    // On détermine combien de lignes on doit afficher
    // C'est soit le nombre d'essais + 1 (la ligne de départ), 
    // soit le maximum de lignes disponibles si on a dépassé.
    const linesToShow = Math.min(attempts + 1, allSnippets.length);

    for (let i = 0; i < linesToShow; i++) {
        const lineDiv = document.createElement('div');
        lineDiv.className = 'snippet'; // On garde ta classe CSS
        lineDiv.innerText = allSnippets[i];
        
        // Petit effet visuel pour distinguer la nouvelle ligne des anciennes
        if (i === attempts) {
            lineDiv.style.color = "#fff"; // La dernière est bien blanche
            lineDiv.style.fontWeight = "bold";
        } else {
            lineDiv.style.color = "#ccc"; // Les anciennes un peu grisées
        }

        container.appendChild(lineDiv);
    }
}

    // --- 2. Faire une tentative ---
    async function makeGuess(title) {
        const input = document.getElementById('guessInput');
        const suggestions = document.getElementById('suggestions');
        const resultsDiv = document.getElementById('results');

        // Nettoyage UI immédiat
        input.value = '';
        suggestions.innerHTML = '';
        input.disabled = true;

        try {
            const res = await fetch('/api/guess', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ title: title, mode: currentMode })
            });

            const data = await res.json();

            // --- CORRECTION MAJEURE ICI ---
            // 1. On met à jour la liste complète des snippets si l'API nous la donne
            if (data.snippets && data.snippets.length > 0) {
                allSnippets = data.snippets;
            }

            createResultRow(data, resultsDiv);

            if (data.is_correct) {
                gameOver = true;
                setTimeout(() => showVictory(data.title), 1000);
                if (currentMode === 'unlimited') {
                    document.getElementById('next-song-container').style.display = 'block';
                }
            } else {
                // 2. Si c'est faux, on augmente le compteur d'essais
                attempts++;
                
                // 3. Et on force la mise à jour de l'affichage
                updateLyricsDisplay();
                
                // On rend la main au joueur
                input.disabled = false;
                input.focus();
            }

        } catch (e) {
            console.error("Erreur jeu:", e);
            input.disabled = false;
        }
    }

    // --- 3. Création et Animation ---
    function createResultRow(data, container) {
        const row = document.createElement('div');
        row.className = 'guess-row';

        const configs = [
            { val: data.title, status: data.is_correct ? 'correct' : 'wrong', label: 'Titre' },
            { val: data.artist.value, status: data.artist.status, label: 'Artiste' },
            { val: data.genre.value, status: data.genre.status, label: 'Genre' },
            { val: data.country.value, status: data.country.status, label: 'Pays' },
            { val: data.year.value, status: data.year.status, dir: data.year.direction, label: 'Année' },
            { val: data.streams.value, status: data.streams.status, dir: data.streams.direction, label: 'Streams' }
        ];

        const tiles = configs.map(conf => {
            const tile = document.createElement('div');
            tile.className = 'tile';
            
            let arrow = '';
            if(conf.dir === 'up') arrow = '⬆️';
            if(conf.dir === 'down') arrow = '⬇️';

            tile.innerHTML = `<span>${conf.label}</span>${conf.val} <div class="arrow">${arrow}</div>`;
            row.appendChild(tile);
            return { element: tile, status: conf.status };
        });

        container.appendChild(row);

        // Animation séquentielle (600ms entre chaque carte)
        tiles.forEach((item, index) => {
            setTimeout(() => {
                item.element.classList.add('revealed');
                item.element.classList.add(`status-${item.status}`);
            }, index * 600);
        });
    }

    function showVictory(title) {
        document.getElementById('win-song-title').innerText = title;
        document.getElementById('winModal').style.display = 'flex';
    }

    window.closeModal = function() {
        document.getElementById('winModal').style.display = 'none';
    }

    // Fermer suggestions au clic extérieur
    document.addEventListener('click', (e) => {
        if (e.target !== input) {
            suggestions.innerHTML = '';
            currentFocus = -1;
        }
    });
});