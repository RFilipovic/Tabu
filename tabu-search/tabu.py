import json
import copy
import os
import sys
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
            print("All moves tabu - resetting tabu list")
            self.tabu_list = []
            best_move = moves[0]
            best_state = self.apply_move(current_state, best_move)

        return best_move, best_state

def safe_write_json(file_path: str, data):
    """Atomically write JSON file"""
    temp_path = file_path + ".tmp"
    try:
        with open(temp_path, 'w') as f:
            json.dump(data, f, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(temp_path, file_path)
    except Exception as e:
        print(f"Error writing {file_path}: {e}", file=sys.stderr)
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise

def safe_write_move(file_path: str, content: str):
    """Atomically write move file"""
    temp_path = file_path + ".tmp"
    try:
        with open(temp_path, 'w') as f:
            f.write(content + "\n")
            f.flush()
            os.fsync(f.fileno())
        os.replace(temp_path, file_path)
    except Exception as e:
        print(f"Error writing move file: {e}", file=sys.stderr)
        if os.path.exists(temp_path):
            os.remove(temp_path)
        # Write safe default directly
        with open(file_path, 'w') as f:
            f.write("5 5\n")
        raise

def main():
    try:
        # Ensure required files exist
        if not os.path.exists("state.json"):
            raise FileNotFoundError("state.json missing")
            
        # Initialize tabu list if missing
        if not os.path.exists("tabu_list.json"):
            with open("tabu_list.json", 'w') as f:
                json.dump({"iterations": 0, "tabu_moves": []}, f)

        # Load state
        with open("state.json", 'r') as f:
            state_data = json.load(f)
        state = State(state_data["stacks"], state_data["containers"])

        # Load tabu list
        with open("tabu_list.json", 'r') as f:
            tabu_data = json.load(f)
        tabu_data["tabu_moves"] = [tuple(m) for m in tabu_data.get("tabu_moves", [])]

        # Reset if max iterations reached
        if tabu_data["iterations"] >= 100:
            print("Resetting tabu list after 100 iterations")
            tabu_data = {"iterations": 0, "tabu_moves": []}
            safe_write_json("tabu_list.json", tabu_data)
            safe_write_move("bestmove.txt", "5 5")
            return

        # Run Tabu Search
        ts = TabuSearch(tabu_list=tabu_data["tabu_moves"])
        move, new_state = ts.find_best_move(state)

        if move is not None:
            # Convert stack names to indices
            stack_map = {"A0": 0, "B0": 1, "B1": 2, "B2": 3, "H0": 4}
            try:
                move_str = f"{stack_map[move[0]]} {stack_map[move[1]]}"
            except KeyError as e:
                print(f"Invalid stack in move: {move}", file=sys.stderr)
                raise ValueError(f"Invalid stack name in move {move}")

            # Save outputs atomically
            safe_write_move("bestmove.txt", move_str)
            safe_write_json("state.json", new_state.to_dict())
            
            # Update tabu list
            ts.add_to_tabu(move)
            tabu_data["tabu_moves"] = ts.tabu_list
            tabu_data["iterations"] += 1
            safe_write_json("tabu_list.json", tabu_data)
        else:
            print("No valid move found")
            safe_write_move("bestmove.txt", "5 5")

    except Exception as e:
        print(f"Critical error in main: {e}", file=sys.stderr)
        # Ensure we always leave valid files
        if not os.path.exists("tabu_list.json"):
            with open("tabu_list.json", 'w') as f:
                json.dump({"iterations": 0, "tabu_moves": []}, f)
        safe_write_move("bestmove.txt", "5 5")
        sys.exit(1)

if __name__ == "__main__":
    main()