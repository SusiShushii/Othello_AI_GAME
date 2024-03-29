"""
This module contains agents that play reversi.

Version 3.1
"""

import abc
import random
import asyncio
import traceback
import time
from multiprocessing import Process, Value
from typing import Tuple, List

import numpy as np

from game import is_terminal, make_move, get_legal_moves

def actions(board: np.ndarray, player: int) -> List[Tuple[int, int]]:
    """Return valid actions."""
    return get_legal_moves(board, player)


def transition(board: np.ndarray, player: int, action: Tuple[int, int]) -> np.ndarray:
    """Return a new board if the action is valid, otherwise None."""

    new_board = make_move(board, action, player)
    return new_board


def terminal_test(board: np.ndarray) -> bool:
    return is_terminal(board)

class ReversiAgent(abc.ABC):
    """Reversi Agent."""

    def __init__(self, color):
        """
        Create an agent.

        Parameters
        -------------
        color : int
            BLACK is 1 and WHITE is -1.

        """
        super().__init__()
        self._move = None
        self._color = color

    @property
    def player(self) -> int:
        """Return the color of this agent."""
        return self._color

    @property
    def pass_move(self) -> Tuple[int, int]:
        """Return move that skips the turn."""
        return (-1, 0)

    @property
    def best_move(self) -> Tuple[int, int]:
        """Return move after the thinking.

        Returns
        ------------
        move : np.array
            The array contains an index x, y.

        """
        if self._move is not None:
            return self._move
        else:
            return self.pass_move

    async def move(self, board, valid_actions) -> Tuple[int, int]:
        """Return a move. The returned is also availabel at self._move."""
        self._move = None
        output_move_row = Value('d', -1)
        output_move_column = Value('d', 0)
        try:
            
            p = Process(
                target=self.search,
                args=(
                    board, valid_actions,
                    output_move_row, output_move_column))
            p.start()
            while p.is_alive():
                await asyncio.sleep(0.1)
                self._move = (int(output_move_row.value), int(output_move_column.value))
        except asyncio.CancelledError as e:
            print('The previous player is interrupted by a user or a timer.')
        except Exception as e:
            print(type(e).__name__)
            print('move() Traceback (most recent call last): ')
            traceback.print_tb(e.__traceback__)
        finally:
            p.kill()
            self._move = (int(output_move_row.value), int(output_move_column.value))
        return self.best_move

    @abc.abstractmethod
    def search(
            self, board, valid_actions,
            output_move_row, output_move_column):
        
        raise NotImplementedError('You will have to implement this.')


# ============================================================
# Random Agent (DO NOT CHANGE)
# ============================================================


class RandomAgent(ReversiAgent):
   

    def search(
            self, board, valid_actions,
            output_move_row, output_move_column):
        
        # If you want to "simulate a move", you can call the following function:
        # transition(board, self.player, valid_actions[0])

        # To prevent your agent to fail silently we should an
        # explicit trackback printout.
        try:
            # while True:
            #     pass
            # time.sleep(0.1)
            randidx = random.randint(0, len(valid_actions) - 1)
            random_action = valid_actions[randidx]
            output_move_row.value = random_action[0]
            output_move_column.value = random_action[1]
        except Exception as e:
            print(type(e).__name__, ':', e)
            print('search() Traceback (most recent call last): ')
            traceback.print_tb(e.__traceback__)




class NorAgent(ReversiAgent):
   
    DEPTH_LIMIT = 5

    def search(
            self, board, valid_actions,
            output_move_row, output_move_column):
       
        # valid_actions = actions(board, self.player)
        # print(valid_actions)
        if len(valid_actions) == 0:
            output_move_row.value = -1
            output_move_column.value = -1
            return  # skip the turn.
        v = -999999
        # default to first valid action
        output_move_row.value = valid_actions[0][0]
        output_move_column.value = valid_actions[0][1]
        for action in valid_actions:
            new_v = self.min_value(transition(board, self.player, action), depth=1)
            if new_v > v:
                v = new_v
                output_move_row.value = action[0]
                output_move_column.value = action[1]
        return v


    def min_value(self, board: np.ndarray, depth: int) -> float:
        opponent = self.player * -1 # opponent's turn
        if is_terminal(board):
            return self.utility(board)
        if depth >= NorAgent.DEPTH_LIMIT:
            return self.evaluation(board)
        valid_actions = actions(board, opponent)
        if len(valid_actions) == 0:
            return self.max_value(board, depth + 1)  # skip the turn.
        v = 999999
        for action in valid_actions:
            v = min(v, self.max_value(transition(board, opponent, action), depth+1))
        return v

    def max_value(self, board: np.ndarray, depth: int) -> float:
        if is_terminal(board):
            return self.utility(board)
        if depth >= NorAgent.DEPTH_LIMIT:
            return self.evaluation(board)
        valid_actions = actions(board, self.player)
        if len(valid_actions) == 0:
            return self.min_value(board, depth + 1)  # skip the turn.
        v = -999999
        for action in valid_actions:
            v = min(v, self.min_value(transition(board, self.player, action), depth+1))
        return v

    def utility(self, board: np.ndarray) -> float:
        if (board == self.player).sum() > (board == (self.player * -1)).sum():
            return 9999
        elif (board == self.player).sum() < (board == (self.player * -1)).sum():
            return -9999
        else:
            return 0

    def evaluation(self, board: np.ndarray) -> float:
        # a dummy evaluation that return diff scores
        return (board == self.player).sum() - (board == (self.player * -1)).sum()


class MineAgent(ReversiAgent):
    DEPTH_LIMIT = 3
    def search(
            self, board, valid_actions,
            output_move_row, output_move_column):
        alpha = -999999
        beta = 999999

       
        if len(valid_actions) == 0:
            output_move_row.value = -1
            output_move_column.value = -1
            return  
        v = -999999
        output_move_row.value = valid_actions[0][0]
        output_move_column.value = valid_actions[0][1]
        for action in valid_actions:
            new_v = self.min_value(transition(board, self.player, action    ), depth=1, alpha=alpha, beta=beta)
            if new_v > v:
                v = new_v
                output_move_row.value = action[0]
                output_move_column.value = action[1]
            alpha = max(alpha,v)
            if v >= beta:
                break
        return v


    def min_value(self, board: np.ndarray, depth: int, alpha: float, beta:float) -> float:
        opponent = self.player * -1 
        if is_terminal(board):
            return self.utility(board)
        if depth >= MineAgent.DEPTH_LIMIT:
            return self.evaluation(board)
        valid_actions = actions(board, opponent)
        if len(valid_actions) == 0:
            return self.max_value(board, depth + 1, alpha, beta)  
        v = 999999
        for action in valid_actions:
            v = min(v, self.max_value(transition(board, opponent, action), depth+1, alpha, beta))

            if v <= alpha:
                return v 
            beta = min(beta,v)
        return v

    def max_value(self, board: np.ndarray, depth: int, alpha: float, beta: float) -> float:
        if is_terminal(board):
            return self.utility(board)
        if depth >= MineAgent.DEPTH_LIMIT:
            return self.evaluation(board)
        valid_actions = actions(board, self.player)
        if len(valid_actions) == 0:
            return self.min_value(board, depth + 1,alpha,beta)  
        v = -999999
        for action in valid_actions:
            v = max(v, self.min_value(transition(board, self.player, action), depth+1, alpha,beta))

            if v >= beta:
                return v
            alpha = max(alpha, v)

        return v

    def utility(self, board: np.ndarray) -> float:
        if (board == self.player).sum() > (board == (self.player * -1)).sum():
            return 9999
        elif (board == self.player).sum() < (board == (self.player * -1)).sum():
            return -9999
        else:
            return 0

    def evaluation(self, board: np.ndarray) -> float:
 
        pieces = 1.0 
        movable = 0.5
        corner = 2.0

        piece_count_diff = (board == self.player).sum() - (board == (self.player * -1)).sum()

        player_mobility = len(actions(board, self.player))
        opponent_mobility = len(actions(board, self.player * -1))
        mobility_diff = player_mobility - opponent_mobility

        corners = [(0, 0), (0, 7), (7, 0), (7, 7)]
        player_corners = sum([board[pos] == self.player for pos in corners])
        opponent_corners = sum([board[pos] == (self.player * -1) for pos in corners])
        corner_diff = player_corners - opponent_corners

        total_score = (
            pieces * piece_count_diff +
            movable * mobility_diff +
            corner * corner_diff
        )

        return total_score
