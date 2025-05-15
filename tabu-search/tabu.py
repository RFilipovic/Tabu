import json
import copy
import random
import os
from typing import List, Dict, Tuple

class Container:
    def __init__(self, id: str, minutes: int, seconds: int):
        self.id = id
        self.minutes = minutes
        self.seconds = seconds

    def total_seconds(self) -> int:
        return self.minutes * 60 + self.seconds

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "minutes": self.minutes,
            "seconds": self.seconds
        }

class State:
    def __init__(self, stacks: List[str], containers: List[Dict]):
        self.stacks = stacks
        self.containers = {}
        self.stack_contents = {stack: [] for stack in stacks}
        
        for container in containers:
            cont_obj = Container(container["id"], container["minutes"], container["seconds"])
            self.containers[container["id"]] = cont_obj
            self.stack_contents[container["stack"]].append(cont_obj)
    
    def get_container_position(self, container_id: str) -> str:
        for stack, containers in self.stack_contents.items():
            if any(c.id == container_id for c in containers):
                return stack
        return None
    
    def to_dict(self) -> Dict:
        containers = []
        for stack, cont_list in self.stack_contents.items():
            for container in cont_list:
                containers.append({
                    "id": container.id,
                    "stack": stack,
                    "minutes": container.minutes,
                    "seconds": container.seconds
                })
        return {
            "stacks": self.stacks,
            "containers": containers
        }

class TabuSearch:
    def __init__(self, tabu_list: List[Tuple[str, str]], tabu_size: int = 5):
        self.tabu_size = tabu_size
        self.tabu_list = tabu_list

    def evaluate_state(self, state: State) -> int:
        total = 0
        for container in state.containers.values():
            total += container.total_seconds()
        for stack, containers in state.stack_contents.items():
            if stack != "H0":
                total += len(containers) * 10
        return total

    def generate_moves(self, state: State) -> List[Tuple[str, str]]:
        moves = []
        for from_stack in state.stacks:
            if from_stack == "H0" or not state.stack_contents[from_stack]:
                continue
            for to_stack in state.stacks:
                if to_stack == "A0" or from_stack == to_stack:
                    continue
                if len(state.stack_contents[to_stack]) >= 10 and to_stack != "H0":
                    continue
                moves.append((from_stack, to_stack))
        return moves

    def apply_move(self, state: State, move: Tuple[str, str]) -> State:
        from_stack, to_stack = move
        new_state = copy.deepcopy(state)
        if new_state.stack_contents[from_stack]:
            container = new_state.stack_contents[from_stack][-1]
            new_state.stack_contents[from_stack].pop()
            new_state.stack_contents[to_stack].append(container)
        return new_state

    def is_tabu(self, move: Tuple[str, str]) -> bool:
        return move in self.tabu_list

    def add_to_tabu(self, move: Tuple[str, str]):
        self.tabu_list.append(move)
        if len(self.tabu_list) > self.tabu_size:
            self.tabu_list.pop(0)

    def find_best_move(self, current_state: State) -> Tuple[Tuple[str, str], State]:
        moves = self.generate_moves(current_state)
        best_move = None
        best_state = None
        best_score = float('inf')

        for move in moves:
            if self.is_tabu(move):
                continue
            new_state = self.apply_move(current_state, move)
            score = self.evaluate_state(new_state)
            if score < best_score:
                best_score = score
                best_move = move
                best_state = new_state

        if best_move is None and moves:
            best_move = moves[0]
            best_state = self.apply_move(current_state, best_move)

        return best_move, best_state


# File Handling Functions
def load_state(file_path: str) -> State:
    with open(file_path, 'r') as f:
        data = json.load(f)
    return State(data["stacks"], data["containers"])

def save_state(file_path: str, state: State):
    with open(file_path, 'w') as f:
        json.dump(state.to_dict(), f, indent=2)

def save_move_txt(file_path: str, move: Tuple[str, str]):
    with open(file_path, 'w') as f:
        f.write(f"{move[0]} {move[1]}\n")

def load_tabu_list(file_path: str) -> Dict:
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            data = json.load(f)
            data["tabu_moves"] = [tuple(m) for m in data.get("tabu_moves", [])]
            return data
    return {"iterations": 0, "tabu_moves": []}

def save_tabu_list(file_path: str, data: Dict):
    data["tabu_moves"] = [list(m) for m in data["tabu_moves"]]
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2)


# Main Entry Point
def main():
    state = load_state("state.json")
    tabu_data = load_tabu_list("tabu_list.json")

    # Stop if max iterations reached
    if tabu_data["iterations"] >= 100:
        with open("bestmove.txt", "w") as f:
            f.write("5 5\n")
        return

    # Initialize dummy tabu list if first iteration and empty
    if tabu_data["iterations"] == 0 and not tabu_data["tabu_moves"]:
        tabu_data["tabu_moves"] = [("0", "0")] * 5

    # Run one step of Tabu Search
    ts = TabuSearch(tabu_list=tabu_data["tabu_moves"])
    move, new_state = ts.find_best_move(state)

    if move is not None:
        save_move_txt("bestmove.txt", move)
        save_state("state.json", new_state)

        # Update tabu list and iterations
        ts.add_to_tabu(move)
        tabu_data["tabu_moves"] = ts.tabu_list
        tabu_data["iterations"] += 1
        save_tabu_list("tabu_list.json", tabu_data)
    else:
        with open("bestmove.txt", "w") as f:
            f.write("5 5\n")

if __name__ == "__main__":
    main()