
// Stockfish Chess Engine Web Worker
// This is a simplified version for demo purposes
// In production, you would use the actual Stockfish WASM build

class SimpleChessEngine {
    constructor() {
        this.depth = 3;
        this.pieces = {
            'P': 100, 'N': 320, 'B': 330, 'R': 500, 'Q': 900, 'K': 20000,
            'p': -100, 'n': -320, 'b': -330, 'r': -500, 'q': -900, 'k': -20000
        };

        // Position value tables
        this.pawnTable = [
            0,  0,  0,  0,  0,  0,  0,  0,
            50, 50, 50, 50, 50, 50, 50, 50,
            10, 10, 20, 30, 30, 20, 10, 10,
            5,  5, 10, 25, 25, 10,  5,  5,
            0,  0,  0, 20, 20,  0,  0,  0,
            5, -5,-10,  0,  0,-10, -5,  5,
            5, 10, 10,-20,-20, 10, 10,  5,
            0,  0,  0,  0,  0,  0,  0,  0
        ];

        this.knightTable = [
            -50,-40,-30,-30,-30,-30,-40,-50,
            -40,-20,  0,  0,  0,  0,-20,-40,
            -30,  0, 10, 15, 15, 10,  0,-30,
            -30,  5, 15, 20, 20, 15,  5,-30,
            -30,  0, 15, 20, 20, 15,  0,-30,
            -30,  5, 10, 15, 15, 10,  5,-30,
            -40,-20,  0,  5,  5,  0,-20,-40,
            -50,-40,-30,-30,-30,-30,-40,-50
        ];
    }

    evaluateBoard(board) {
        let score = 0;

        for (let row = 0; row < 8; row++) {
            for (let col = 0; col < 8; col++) {
                const piece = board[row][col];
                if (piece) {
                    score += this.pieces[piece];
                    score += this.getPositionValue(piece, row, col);
                }
            }
        }

        return score;
    }

    getPositionValue(piece, row, col) {
        const index = row * 8 + col;

        switch (piece.toLowerCase()) {
            case 'p':
                return piece === 'P' ? this.pawnTable[index] : -this.pawnTable[63 - index];
            case 'n':
                return piece === 'N' ? this.knightTable[index] : -this.knightTable[63 - index];
            default:
                return 0;
        }
    }

    generateMoves(board, isWhite) {
        const moves = [];

        for (let row = 0; row < 8; row++) {
            for (let col = 0; col < 8; col++) {
                const piece = board[row][col];
                if (piece && ((isWhite && piece === piece.toUpperCase()) || 
                             (!isWhite && piece === piece.toLowerCase()))) {
                    moves.push(...this.getPieceMoves(board, row, col, piece));
                }
            }
        }

        return moves;
    }

    getPieceMoves(board, row, col, piece) {
        const moves = [];
        const directions = this.getMoveDirections(piece.toLowerCase());

        for (const [dx, dy] of directions) {
            let newRow = row + dx;
            let newCol = col + dy;

            while (newRow >= 0 && newRow < 8 && newCol >= 0 && newCol < 8) {
                const target = board[newRow][newCol];

                if (!target) {
                    moves.push({ from: [row, col], to: [newRow, newCol] });
                } else {
                    // Check if we can capture
                    if ((piece === piece.toUpperCase() && target === target.toLowerCase()) ||
                        (piece === piece.toLowerCase() && target === target.toUpperCase())) {
                        moves.push({ from: [row, col], to: [newRow, newCol] });
                    }
                    break; // Can't move further
                }

                // For pawns and kings, only move one square
                if (piece.toLowerCase() === 'p' || piece.toLowerCase() === 'k') {
                    break;
                }

                newRow += dx;
                newCol += dy;
            }
        }

        return moves;
    }

    getMoveDirections(piece) {
        switch (piece) {
            case 'p': return [[-1, 0], [-1, -1], [-1, 1]]; // Simplified pawn moves
            case 'r': return [[-1, 0], [1, 0], [0, -1], [0, 1]];
            case 'n': return [[-2, -1], [-2, 1], [-1, -2], [-1, 2], [1, -2], [1, 2], [2, -1], [2, 1]];
            case 'b': return [[-1, -1], [-1, 1], [1, -1], [1, 1]];
            case 'q': return [[-1, -1], [-1, 0], [-1, 1], [0, -1], [0, 1], [1, -1], [1, 0], [1, 1]];
            case 'k': return [[-1, -1], [-1, 0], [-1, 1], [0, -1], [0, 1], [1, -1], [1, 0], [1, 1]];
            default: return [];
        }
    }

    minimax(board, depth, isMaximizing, alpha = -Infinity, beta = Infinity) {
        if (depth === 0) {
            return this.evaluateBoard(board);
        }

        const moves = this.generateMoves(board, !isMaximizing);

        if (moves.length === 0) {
            return isMaximizing ? -10000 : 10000;
        }

        if (isMaximizing) {
            let maxEval = -Infinity;
            for (const move of moves) {
                const newBoard = this.makeMove(board, move);
                const eval_ = this.minimax(newBoard, depth - 1, false, alpha, beta);
                maxEval = Math.max(maxEval, eval_);
                alpha = Math.max(alpha, eval_);
                if (beta <= alpha) break;
            }
            return maxEval;
        } else {
            let minEval = Infinity;
            for (const move of moves) {
                const newBoard = this.makeMove(board, move);
                const eval_ = this.minimax(newBoard, depth - 1, true, alpha, beta);
                minEval = Math.min(minEval, eval_);
                beta = Math.min(beta, eval_);
                if (beta <= alpha) break;
            }
            return minEval;
        }
    }

    makeMove(board, move) {
        const newBoard = board.map(row => [...row]);
        const [fromRow, fromCol] = move.from;
        const [toRow, toCol] = move.to;

        newBoard[toRow][toCol] = newBoard[fromRow][fromCol];
        newBoard[fromRow][fromCol] = null;

        return newBoard;
    }

    findBestMove(board) {
        const moves = this.generateMoves(board, false); // Black's turn
        let bestMove = null;
        let bestValue = Infinity;

        for (const move of moves) {
            const newBoard = this.makeMove(board, move);
            const value = this.minimax(newBoard, this.depth - 1, true);

            if (value < bestValue) {
                bestValue = value;
                bestMove = move;
            }
        }

        return bestMove;
    }

    moveToUCI(move) {
        if (!move) return 'none';

        const [fromRow, fromCol] = move.from;
        const [toRow, toCol] = move.to;

        const fromSquare = String.fromCharCode(97 + fromCol) + (8 - fromRow);
        const toSquare = String.fromCharCode(97 + toCol) + (8 - toRow);

        return fromSquare + toSquare;
    }
}

// Web Worker message handling
const engine = new SimpleChessEngine();
let currentBoard = null;

self.onmessage = function(e) {
    const message = e.data;

    if (message.startsWith('position fen')) {
        // Parse FEN and set up board (simplified)
        currentBoard = getInitialBoard();
    } else if (message.startsWith('go depth')) {
        const depth = parseInt(message.split(' ')[2]) || 3;
        engine.depth = depth;

        if (currentBoard) {
            const bestMove = engine.findBestMove(currentBoard);
            const uciMove = engine.moveToUCI(bestMove);
            self.postMessage(`bestmove ${uciMove}`);
        } else {
            self.postMessage('bestmove none');
        }
    }
};

function getInitialBoard() {
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
