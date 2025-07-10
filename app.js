
// Telegram Chess Bot - Main Application
class ChessBot {
    constructor() {
        this.currentPage = 'profile';
        this.user = null;
        this.userData = {};
        this.coins = 0;
        this.tg = window.Telegram?.WebApp;
        this.gameState = null;
        this.selectedSquare = null;
        this.isPlayerTurn = true;

        this.init();
    }

    async init() {
        // Initialize Telegram WebApp
        if (this.tg) {
            this.tg.ready();
            this.tg.expand();
            this.setupTelegramTheme();
        }

        // Load user data
        await this.loadUserData();

        // Setup event listeners
        this.setupEventListeners();

        // Initialize chess engine
        await this.initChessEngine();

        // Show initial page
        this.showPage('profile');
    }

    setupTelegramTheme() {
        if (!this.tg) return;

        const root = document.documentElement;
        if (this.tg.colorScheme === 'dark') {
            root.style.setProperty('--background-dark', this.tg.themeParams.bg_color || '#1a1a2e');
            root.style.setProperty('--text-light', this.tg.themeParams.text_color || '#ffffff');
        }
    }

    async loadUserData() {
        try {
            const response = await fetch('/api/user-data', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    user_id: this.tg?.initDataUnsafe?.user?.id || 'demo',
                    username: this.tg?.initDataUnsafe?.user?.username || 'DemoUser'
                })
            });

            if (response.ok) {
                this.userData = await response.json();
                this.coins = this.userData.coins || 0;
                this.updateUI();
            }
        } catch (error) {
            console.error('Error loading user data:', error);
            // Demo data for testing
            this.userData = {
                username: 'DemoUser',
                level: 5,
                xp: 750,
                xp_needed: 1000,
                coins: 150,
                ratings: {
                    bullet: 1456,
                    blitz: 1523,
                    rapid: 1389,
                    classical: 1445
                },
                title: 'Шахматный Энтузиаст',
                customization: {}
            };
            this.coins = this.userData.coins;
            this.updateUI();
        }
    }

    setupEventListeners() {
        // Navigation tabs
        document.querySelectorAll('.nav-tab').forEach(tab => {
            tab.addEventListener('click', (e) => {
                const page = e.target.dataset.page;
                this.showPage(page);
            });
        });

        // Chess game controls
        document.getElementById('newGame')?.addEventListener('click', () => this.startNewGame());
        document.getElementById('resign')?.addEventListener('click', () => this.resignGame());

        // Shop interactions
        document.querySelectorAll('.buy-button').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const itemId = e.target.dataset.item;
                this.purchaseItem(itemId);
            });
        });

        // Modal interactions
        document.querySelector('.modal .cancel-btn')?.addEventListener('click', () => {
            this.closeModal();
        });

        document.querySelector('.modal .confirm-btn')?.addEventListener('click', () => {
            this.confirmPurchase();
        });
    }

    showPage(pageId) {
        // Update navigation
        document.querySelectorAll('.nav-tab').forEach(tab => {
            tab.classList.remove('active');
        });
        document.querySelector(`[data-page="${pageId}"]`).classList.add('active');

        // Update pages
        document.querySelectorAll('.page').forEach(page => {
            page.classList.remove('active');
        });
        document.getElementById(pageId).classList.add('active');

        this.currentPage = pageId;

        // Load page-specific data
        switch(pageId) {
            case 'leaderboard':
                this.loadLeaderboard();
                break;
            case 'chess':
                this.setupChessBoard();
                break;
            case 'shop':
                this.loadShop();
                break;
        }
    }

    updateUI() {
        // Update profile info
        document.getElementById('username').textContent = this.userData.username;
        document.getElementById('userTitle').textContent = this.userData.title || 'Новичок';
        document.getElementById('userLevel').textContent = `Уровень ${this.userData.level}`;

        // Update XP progress
        const xpProgress = ((this.userData.xp || 0) / (this.userData.xp_needed || 100)) * 100;
        document.getElementById('xpProgress').style.width = `${xpProgress}%`;
        document.getElementById('currentXp').textContent = this.userData.xp || 0;
        document.getElementById('neededXp').textContent = this.userData.xp_needed || 100;

        // Update ratings
        const ratings = this.userData.ratings || {};
        document.getElementById('bulletRating').textContent = ratings.bullet || '—';
        document.getElementById('blitzRating').textContent = ratings.blitz || '—';
        document.getElementById('rapidRating').textContent = ratings.rapid || '—';
        document.getElementById('classicalRating').textContent = ratings.classical || '—';

        // Update coins display
        document.getElementById('coinsAmount').textContent = this.coins;

        // Apply customizations
        this.applyCustomizations();
    }

    applyCustomizations() {
        const custom = this.userData.customization || {};

        // Apply custom background
        if (custom.background) {
            document.body.style.backgroundImage = `url(${custom.background})`;
        }

        // Apply custom avatar
        if (custom.avatar) {
            document.getElementById('userAvatar').src = custom.avatar;
        }

        // Apply custom banner
        if (custom.banner) {
            document.querySelector('.profile-banner').style.backgroundImage = `url(${custom.banner})`;
        }

        // Apply avatar effects
        const avatar = document.getElementById('userAvatar');
        if (custom.avatar_effect >= 1) {
            avatar.classList.add('avatar-effect-1');
        }
        if (custom.avatar_effect >= 2) {
            avatar.classList.add('avatar-effect-2');
        }
        if (custom.avatar_effect >= 3) {
            avatar.classList.add('avatar-effect-3');
        }

        // Apply profile effects
        const profileCard = document.querySelector('.profile-info');
        if (custom.profile_effect >= 1) {
            profileCard.classList.add('profile-effect-1');
        }
        if (custom.profile_effect >= 2) {
            profileCard.classList.add('profile-effect-2');
        }
        if (custom.profile_effect >= 3) {
            profileCard.classList.add('profile-effect-3');
        }
    }

    async loadLeaderboard() {
        try {
            const response = await fetch('/api/leaderboard');
            if (response.ok) {
                const leaderboard = await response.json();
                this.renderLeaderboard(leaderboard);
            }
        } catch (error) {
            console.error('Error loading leaderboard:', error);
            // Demo data
            this.renderLeaderboard([
                { rank: 1, username: 'ChessMaster', level: 12, utility: 1250000 },
                { rank: 2, username: 'TacticGuru', level: 10, utility: 980000 },
                { rank: 3, username: 'EndgameKing', level: 9, utility: 875000 },
            ]);
        }
    }

    renderLeaderboard(data) {
        const tbody = document.getElementById('leaderboardBody');
        tbody.innerHTML = '';

        data.forEach(player => {
            const row = document.createElement('div');
            row.className = 'table-row';
            row.innerHTML = `
                <div>${player.rank}</div>
                <div class="player-name" data-username="${player.username}">${player.username}</div>
                <div>${player.level}</div>
                <div>${player.utility.toLocaleString()}</div>
            `;

            row.querySelector('.player-name').addEventListener('click', () => {
                this.showPlayerProfile(player.username);
            });

            tbody.appendChild(row);
        });
    }

    async showPlayerProfile(username) {
        // Show player profile modal or navigate to profile page
        try {
            const response = await fetch(`/api/player/${username}`);
            if (response.ok) {
                const playerData = await response.json();
                this.displayPlayerModal(playerData);
            }
        } catch (error) {
            console.error('Error loading player profile:', error);
        }
    }

    displayPlayerModal(playerData) {
        // Create and show player profile modal
        const modal = document.createElement('div');
        modal.className = 'modal active';
        modal.innerHTML = `
            <div class="modal-content">
                <h3>${playerData.username}</h3>
                <div class="player-stats">
                    <p>Уровень: ${playerData.level}</p>
                    <p>Титул: ${playerData.title || 'Нет'}</p>
                    <p>Рейтинг пуля: ${playerData.ratings?.bullet || '—'}</p>
                    <p>Рейтинг блиц: ${playerData.ratings?.blitz || '—'}</p>
                    <p>Рейтинг рапид: ${playerData.ratings?.rapid || '—'}</p>
                    <p>Рейтинг классика: ${playerData.ratings?.classical || '—'}</p>
                </div>
                <button class="cancel-btn" onclick="this.closest('.modal').remove()">Закрыть</button>
            </div>
        `;
        document.body.appendChild(modal);
    }

    async initChessEngine() {
        // Initialize Stockfish worker
        if (typeof Worker !== 'undefined') {
            try {
                this.stockfish = new Worker('/static/js/stockfish.js');
                this.stockfish.onmessage = (e) => {
                    this.handleEngineMessage(e.data);
                };
            } catch (error) {
                console.error('Error initializing chess engine:', error);
            }
        }

        // Initialize chess board state
        this.resetChessGame();
    }

    resetChessGame() {
        this.gameState = {
            board: this.getInitialBoard(),
            turn: 'white',
            gameOver: false,
            winner: null
        };
    }

    getInitialBoard() {
        return [
            ['r', 'n', 'b', 'q', 'k', 'b', 'n', 'r'],
            ['p', 'p', 'p', 'p', 'p', 'p', 'p', 'p'],
            [null, null, null, null, null, null, null, null],
            [null, null, null, null, null, null, null, null],
            [null, null, null, null, null, null, null, null],
            [null, null, null, null, null, null, null, null],
            ['P', 'P', 'P', 'P', 'P', 'P', 'P', 'P'],
            ['R', 'N', 'B', 'Q', 'K', 'B', 'N', 'R']
        ];
    }

    setupChessBoard() {
        const board = document.getElementById('chessBoard');
        if (!board) return;

        board.innerHTML = '';

        for (let row = 0; row < 8; row++) {
            for (let col = 0; col < 8; col++) {
                const square = document.createElement('div');
                square.className = `chess-square ${(row + col) % 2 === 0 ? 'light' : 'dark'}`;
                square.dataset.row = row;
                square.dataset.col = col;

                const piece = this.gameState.board[row][col];
                if (piece) {
                    square.textContent = this.getPieceSymbol(piece);
                }

                square.addEventListener('click', (e) => {
                    this.handleSquareClick(row, col);
                });

                board.appendChild(square);
            }
        }
    }

    getPieceSymbol(piece) {
        const pieces = {
            'K': '♔', 'Q': '♕', 'R': '♖', 'B': '♗', 'N': '♘', 'P': '♙',
            'k': '♚', 'q': '♛', 'r': '♜', 'b': '♝', 'n': '♞', 'p': '♟'
        };
        return pieces[piece] || '';
    }

    handleSquareClick(row, col) {
        if (this.gameState.gameOver || !this.isPlayerTurn) return;

        const square = document.querySelector(`[data-row="${row}"][data-col="${col}"]`);

        if (this.selectedSquare) {
            // Try to make a move
            if (this.isValidMove(this.selectedSquare.row, this.selectedSquare.col, row, col)) {
                this.makeMove(this.selectedSquare.row, this.selectedSquare.col, row, col);
                this.clearSelection();
                this.isPlayerTurn = false;
                setTimeout(() => this.makeEngineMove(), 500);
            } else {
                this.clearSelection();
            }
        } else {
            // Select a piece
            const piece = this.gameState.board[row][col];
            if (piece && piece === piece.toUpperCase()) { // White piece
                this.selectedSquare = { row, col };
                square.classList.add('selected');
                this.highlightPossibleMoves(row, col);
            }
        }
    }

    clearSelection() {
        document.querySelectorAll('.chess-square').forEach(sq => {
            sq.classList.remove('selected', 'possible-move');
        });
        this.selectedSquare = null;
    }

    isValidMove(fromRow, fromCol, toRow, toCol) {
        // Basic move validation (simplified)
        const piece = this.gameState.board[fromRow][fromCol];
        const target = this.gameState.board[toRow][toCol];

        // Can't capture own pieces
        if (target && target === target.toUpperCase()) return false;

        // Basic boundary check
        if (toRow < 0 || toRow >= 8 || toCol < 0 || toCol >= 8) return false;

        return true; // Simplified for demo
    }

    makeMove(fromRow, fromCol, toRow, toCol) {
        const piece = this.gameState.board[fromRow][fromCol];
        const capturedPiece = this.gameState.board[toRow][toCol];

        this.gameState.board[toRow][toCol] = piece;
        this.gameState.board[fromRow][fromCol] = null;

        this.gameState.turn = this.gameState.turn === 'white' ? 'black' : 'white';
        this.setupChessBoard();

        // Check for game over
        if (this.isGameOver()) {
            this.endGame();
        }
    }

    makeEngineMove() {
        if (this.stockfish) {
            this.stockfish.postMessage('position fen ' + this.getBoardFEN());
            this.stockfish.postMessage('go depth 5');
        } else {
            // Fallback: random move
            setTimeout(() => {
                this.makeRandomMove();
                this.isPlayerTurn = true;
            }, 1000);
        }
    }

    makeRandomMove() {
        const moves = this.getAllPossibleMoves('black');
        if (moves.length > 0) {
            const randomMove = moves[Math.floor(Math.random() * moves.length)];
            this.makeMove(randomMove.fromRow, randomMove.fromCol, randomMove.toRow, randomMove.toCol);
        }
    }

    getAllPossibleMoves(color) {
        // Simplified move generation
        const moves = [];
        for (let row = 0; row < 8; row++) {
            for (let col = 0; col < 8; col++) {
                const piece = this.gameState.board[row][col];
                if (piece && ((color === 'white' && piece === piece.toUpperCase()) ||
                             (color === 'black' && piece === piece.toLowerCase()))) {
                    // Add possible moves for this piece
                    for (let toRow = 0; toRow < 8; toRow++) {
                        for (let toCol = 0; toCol < 8; toCol++) {
                            if (this.isValidMove(row, col, toRow, toCol)) {
                                moves.push({ fromRow: row, fromCol: col, toRow, toCol });
                            }
                        }
                    }
                }
            }
        }
        return moves;
    }

    highlightPossibleMoves(row, col) {
        // Highlight possible moves (simplified)
        for (let toRow = 0; toRow < 8; toRow++) {
            for (let toCol = 0; toCol < 8; toCol++) {
                if (this.isValidMove(row, col, toRow, toCol)) {
                    const square = document.querySelector(`[data-row="${toRow}"][data-col="${toCol}"]`);
                    square.classList.add('possible-move');
                }
            }
        }
    }

    startNewGame() {
        this.resetChessGame();
        this.setupChessBoard();
        this.isPlayerTurn = true;
        this.clearSelection();

        // Show game controls
        document.getElementById('newGame').style.display = 'none';
        document.getElementById('resign').style.display = 'inline-block';
    }

    resignGame() {
        this.gameState.gameOver = true;
        this.gameState.winner = 'black';
        this.endGame();
    }

    endGame() {
        const message = this.gameState.winner === 'white' ? 'Вы победили!' : 'Вы проиграли!';

        if (this.gameState.winner === 'white') {
            // Award coins for winning
            const coinsEarned = 5 + Math.floor(Math.random() * 6); // 5-10 coins
            this.coins += coinsEarned;
            this.updateCoins();

            this.showMessage(`${message} Получено ${coinsEarned} монет!`, 'success');
        } else {
            this.showMessage(message, 'error');
        }

        document.getElementById('newGame').style.display = 'inline-block';
        document.getElementById('resign').style.display = 'none';
    }

    loadShop() {
        this.updateShopItems();
    }

    updateShopItems() {
        const shopItems = [
            {
                id: 'background',
                title: 'Собственные обои',
                description: 'Установите свой фон для профиля',
                price: 50,
                requiredLevel: 1,
                type: 'customization'
            },
            {
                id: 'avatar',
                title: 'Собственный аватар',
                description: 'Установите свой аватар',
                price: 100,
                requiredLevel: 3,
                type: 'customization'
            },
            {
                id: 'banner',
                title: 'Собственный баннер',
                description: 'Установите свой баннер профиля',
                price: 200,
                requiredLevel: 5,
                type: 'customization'
            },
            {
                id: 'avatar_effect_1',
                title: 'Аура аватара 1',
                description: 'Мини-аура вокруг аватара',
                price: 500,
                requiredLevel: 6,
                type: 'effect'
            },
            {
                id: 'avatar_effect_2',
                title: 'Аура аватара 2',
                description: 'Вращающаяся аура вокруг аватара',
                price: 1000,
                requiredLevel: 6,
                type: 'effect'
            },
            {
                id: 'avatar_effect_3',
                title: 'Аура аватара 3',
                description: 'Сверкающая аура с искрами',
                price: 2000,
                requiredLevel: 6,
                type: 'effect'
            },
            {
                id: 'profile_effect_1',
                title: 'Эффект профиля 1',
                description: 'Неоновая рамка профиля',
                price: 700,
                requiredLevel: 7,
                type: 'effect'
            },
            {
                id: 'profile_effect_2',
                title: 'Эффект профиля 2',
                description: 'Неоновые акценты и рамки',
                price: 1500,
                requiredLevel: 7,
                type: 'effect'
            },
            {
                id: 'profile_effect_3',
                title: 'Эффект профиля 3',
                description: 'Полный градиент с анимацией',
                price: 3000,
                requiredLevel: 7,
                type: 'effect'
            }
        ];

        const container = document.getElementById('shopItems');
        container.innerHTML = '';

        shopItems.forEach(item => {
            const itemElement = document.createElement('div');
            itemElement.className = 'shop-item';

            const canBuy = this.userData.level >= item.requiredLevel && this.coins >= item.price;
            const alreadyOwned = this.userData.customization?.[item.id];

            itemElement.innerHTML = `
                <div class="item-header">
                    <div class="item-title">${item.title}</div>
                    <div class="item-price">${item.price} 🪙</div>
                </div>
                <div class="item-description">${item.description}</div>
                ${item.requiredLevel > this.userData.level ? 
                    `<div class="item-requirements">Требуется ${item.requiredLevel} уровень</div>` : ''}
                <button class="buy-button" 
                        data-item="${item.id}" 
                        ${!canBuy || alreadyOwned ? 'disabled' : ''}>
                    ${alreadyOwned ? 'Куплено' : canBuy ? 'Купить' : 'Недоступно'}
                </button>
            `;

            container.appendChild(itemElement);
        });

        // Re-attach event listeners
        document.querySelectorAll('.buy-button').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const itemId = e.target.dataset.item;
                this.purchaseItem(itemId);
            });
        });
    }

    purchaseItem(itemId) {
        const item = this.getShopItem(itemId);
        if (!item) return;

        if (item.type === 'customization') {
            this.showCustomizationModal(item);
        } else {
            this.confirmItemPurchase(item);
        }
    }

    showCustomizationModal(item) {
        const modal = document.getElementById('purchaseModal');
        const title = modal.querySelector('h3');
        const input = modal.querySelector('input');

        title.textContent = `Купить ${item.title}`;
        input.placeholder = 'Вставьте ссылку на изображение';
        input.value = '';

        modal.classList.add('active');
        this.currentPurchaseItem = item;
    }

    confirmPurchase() {
        const input = document.querySelector('.modal input');
        const url = input.value.trim();

        if (!url) {
            this.showMessage('Введите ссылку на изображение', 'error');
            return;
        }

        if (!this.isValidImageUrl(url)) {
            this.showMessage('Некорректная ссылка на изображение', 'error');
            return;
        }

        this.processPurchase(this.currentPurchaseItem, url);
        this.closeModal();
    }

    confirmItemPurchase(item) {
        this.processPurchase(item);
    }

    async processPurchase(item, customValue = null) {
        if (this.coins < item.price) {
            this.showMessage('Недостаточно монет!', 'error');
            return;
        }

        if (this.userData.level < item.requiredLevel) {
            this.showMessage(`Требуется ${item.requiredLevel} уровень!`, 'error');
            return;
        }

        try {
            const response = await fetch('/api/purchase', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    user_id: this.tg?.initDataUnsafe?.user?.id || 'demo',
                    item_id: item.id,
                    custom_value: customValue
                })
            });

            if (response.ok) {
                this.coins -= item.price;
                this.userData.customization = this.userData.customization || {};
                this.userData.customization[item.id] = customValue || true;

                this.updateCoins();
                this.updateShopItems();
                this.applyCustomizations();

                this.showMessage(`${item.title} успешно куплен!`, 'success');
            } else {
                throw new Error('Purchase failed');
            }
        } catch (error) {
            console.error('Purchase error:', error);
            this.showMessage('Ошибка покупки. Попробуйте позже.', 'error');
        }
    }

    getShopItem(itemId) {
        const items = {
            'background': { id: 'background', title: 'Собственные обои', price: 50, requiredLevel: 1, type: 'customization' },
            'avatar': { id: 'avatar', title: 'Собственный аватар', price: 100, requiredLevel: 3, type: 'customization' },
            'banner': { id: 'banner', title: 'Собственный баннер', price: 200, requiredLevel: 5, type: 'customization' },
            'avatar_effect_1': { id: 'avatar_effect_1', title: 'Аура аватара 1', price: 500, requiredLevel: 6, type: 'effect' },
            'avatar_effect_2': { id: 'avatar_effect_2', title: 'Аура аватара 2', price: 1000, requiredLevel: 6, type: 'effect' },
            'avatar_effect_3': { id: 'avatar_effect_3', title: 'Аура аватара 3', price: 2000, requiredLevel: 6, type: 'effect' },
            'profile_effect_1': { id: 'profile_effect_1', title: 'Эффект профиля 1', price: 700, requiredLevel: 7, type: 'effect' },
            'profile_effect_2': { id: 'profile_effect_2', title: 'Эффект профиля 2', price: 1500, requiredLevel: 7, type: 'effect' },
            'profile_effect_3': { id: 'profile_effect_3', title: 'Эффект профиля 3', price: 3000, requiredLevel: 7, type: 'effect' }
        };
        return items[itemId];
    }

    isValidImageUrl(url) {
        try {
            new URL(url);
            return /\.(jpg|jpeg|png|gif|webp)$/i.test(url);
        } catch {
            return false;
        }
    }

    closeModal() {
        document.getElementById('purchaseModal').classList.remove('active');
        this.currentPurchaseItem = null;
    }

    updateCoins() {
        document.getElementById('coinsAmount').textContent = this.coins;
    }

    showMessage(text, type = 'info') {
        const message = document.createElement('div');
        message.className = `message ${type}`;
        message.textContent = text;

        document.body.appendChild(message);

        setTimeout(() => {
            message.remove();
        }, 3000);
    }

    isGameOver() {
        // Simplified game over detection
        return false;
    }

    getBoardFEN() {
        // Convert board to FEN notation (simplified)
        return 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1';
    }

    handleEngineMessage(message) {
        if (message.startsWith('bestmove')) {
            const move = message.split(' ')[1];
            if (move !== 'none') {
                this.parseAndMakeEngineMove(move);
            }
            this.isPlayerTurn = true;
        }
    }

    parseAndMakeEngineMove(move) {
        // Parse UCI move format (e.g., "e2e4")
        const fromCol = move.charCodeAt(0) - 97; // 'a' = 0
        const fromRow = 8 - parseInt(move[1]);
        const toCol = move.charCodeAt(2) - 97;
        const toRow = 8 - parseInt(move[3]);

        this.makeMove(fromRow, fromCol, toRow, toCol);
    }
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.chessBot = new ChessBot();
});

// Handle Telegram WebApp events
window.addEventListener('beforeunload', () => {
    if (window.Telegram?.WebApp) {
        window.Telegram.WebApp.close();
    }
});
