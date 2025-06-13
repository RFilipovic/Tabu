import json
import copy
import os
import sys
import random
import re
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
        self.last_moved_container = None
        self.last_move_destination = None
        self.late_containers = set()
        
        for container in containers:
            cont_obj = Container(container["id"], container["minutes"], container["seconds"])
            self.containers[container["id"]] = cont_obj
            self.stack_contents[container["stack"]].append(cont_obj)
            if cont_obj.total_seconds() < 0 and container["stack"] != "H0":
                self.late_containers.add(cont_obj.id)
    
    def get_container_position(self, container_id: str) -> str:
        for stack, containers in self.stack_contents.items():
            if any(c.id == container_id for c in containers):
                return stack
        return None

    def update_late_containers(self):
        for stack_name, containers in self.stack_contents.items():
            if stack_name != "H0":
                for container in containers:
                    if container.total_seconds() < 0:
                        self.late_containers.add(container.id)
    
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
        self.look_ahead_depth = 2
        self.last_moved_container = None

    def evaluate_state(self, state: State) -> int:
        total_cost = 0
        all_containers = list(state.containers.values())
        if not all_containers:
            return 0

        h0_containers = len(state.stack_contents.get("H0", []))
        middle_containers = sum(len(state.stack_contents.get(s, [])) 
                            for s in ["A0", "B0", "B1", "B2"])
        
        for stack_name, containers in state.stack_contents.items():
            if stack_name in ["A0", "B0", "B1", "B2"]:
                for depth, container in enumerate(containers):
                    containers_above = len(containers) - depth - 1
    
                    if container.total_seconds() > 0:
                        burial_penalty = (1 / container.total_seconds()) * (containers_above + 1) * 1000
                        total_cost += int(burial_penalty)
                    else:
                        total_cost += 50000 * (containers_above + 1)

        overdue_count = sum(1 for c in all_containers if c.total_seconds() < 0)
        blocked_overdue = sum(1 for c in all_containers 
                            if c.total_seconds() < 0 
                            and state.get_container_position(c.id) != "H0")
        
        total_cost += middle_containers * 1000
        total_cost -= h0_containers * 2000
        total_cost += overdue_count * 5000
        total_cost += blocked_overdue * 10000
        
        return total_cost

    def generate_moves(self, state: State) -> List[Tuple[str, str]]:
        moves = []
        for from_stack in state.stacks:
            if from_stack == "H0" or not state.stack_contents[from_stack]:
                continue
            
            top_container = state.stack_contents[from_stack][-1]
            if top_container.id == state.last_moved_container:
                continue
                
            for to_stack in state.stacks:
                if to_stack == "A0" or from_stack == to_stack:
                    continue
                if len(state.stack_contents[to_stack]) >= 10 and to_stack != "H0":
                    continue
                moves.append((from_stack, to_stack))
        return moves

    def generate_random_moves(self, state: State, num_moves: int = 3) -> List[Tuple[str, str]]:
        all_moves = self.generate_moves(state)
        if not all_moves:
            return []
        return random.sample(all_moves, min(num_moves, len(all_moves)))

    def look_ahead(self, state: State, depth: int) -> int:
        if depth == 0:
            return self.evaluate_state(state)

        moves = self.generate_random_moves(state)
        if not moves:
            return self.evaluate_state(state)

        scores = []
        for move in moves:
            if not self.is_tabu(move):
                new_state = self.apply_move(state, move)
                score = self.look_ahead(new_state, depth - 1)
                scores.append(score)

        return min(scores) if scores else self.evaluate_state(state)

    def apply_move(self, state: State, move: Tuple[str, str]) -> State:
        from_stack, to_stack = move
        new_state = copy.deepcopy(state)
        if new_state.stack_contents[from_stack]:
            container = new_state.stack_contents[from_stack][-1]
            new_state.stack_contents[from_stack].pop()
            new_state.stack_contents[to_stack].append(container)
            new_state.last_moved_container = container.id
            new_state.update_late_containers()
        return new_state

    def is_tabu(self, move: Tuple[str, str]) -> bool:
        return move in self.tabu_list

    def add_to_tabu(self, move: Tuple[str, str]):
        self.tabu_list.append(move)
        if len(self.tabu_list) > self.tabu_size:
            self.tabu_list.pop(0)

    def find_best_move(self, current_state: State) -> Tuple[Tuple[str, str], State]:
        for stack in current_state.stack_contents:
            if stack == "H0":
                continue
            containers = current_state.stack_contents[stack]
            if containers and containers[-1].total_seconds() < 0:
                move = (stack, "H0")
                self.last_moved_container = containers[-1].id
                return move, self.apply_move(current_state, move)

        moves = self.generate_random_moves(current_state, num_moves=5)
        best_move = None
        best_state = None
        best_score = float('inf')

        for move in moves:
            if not self.is_tabu(move):
                new_state = self.apply_move(current_state, move)
                score = self.look_ahead(new_state, self.look_ahead_depth)
                if score < best_score:
                    best_score = score
                    best_move = move
                    best_state = new_state

        if best_move is None and moves:
            non_tabu_moves = [m for m in moves if not self.is_tabu(m)]
            if non_tabu_moves:
                best_move = random.choice(non_tabu_moves)
            else:
                self.tabu_list.clear()
                best_move = random.choice(moves)
            best_state = self.apply_move(current_state, best_move)

        if best_move:
            from_stack = best_move[0]
            self.last_moved_container = current_state.stack_contents[from_stack][-1].id

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
    
def parse_ulaz_times(ulaz_path="../simulator/ulaz.txt"):
        times = {}
        with open(ulaz_path, "r") as f:
            for line in f:
                if "<CRANE LIFT>" in line:
                    m = re.search(r"<CRANE LIFT>([\d:]+)</CRANE LIFT>", line)
                    if m:
                        min_, sec = map(int, m.group(1).split(":"))
                        times["lift"] = min_ * 60 + sec
                if "<CRANE MOVE>" in line:
                    m = re.search(r"<CRANE MOVE>([\d:]+)</CRANE MOVE>", line)
                    if m:
                        min_, sec = map(int, m.group(1).split(":"))
                        times["move"] = min_ * 60 + sec
                if "<CRANE LOWER>" in line:
                    m = re.search(r"<CRANE LOWER>([\d:]+)</CRANE LOWER>", line)
                    if m:
                        min_, sec = map(int, m.group(1).split(":"))
                        times["lower"] = min_ * 60 + sec
                if "<CLEARING TIME>" in line:
                    m = re.search(r"<CLEARING TIME>([\d:]+)</CLEARING TIME>", line)
                    if m:
                        min_, sec = map(int, m.group(1).split(":"))
                        times["clear"] = min_ * 60 + sec
        return times

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
        with open(file_path, 'w') as f:
            f.write("5 5\n")
        raise
    
def main():
    try:
        if not os.path.exists("state.json"):
            raise FileNotFoundError("state.json missing")
            
        if not os.path.exists("tabu_list.json"):
            with open("tabu_list.json", 'w') as f:
                json.dump({"iterations": 0, "tabu_moves": []}, f)

        # Initialize or load late containers tracking
        late_containers_file = "late_containers.json"
        if not os.path.exists(late_containers_file):
            with open(late_containers_file, 'w') as f:
                json.dump({"total_late": [], "count": 0}, f)

        with open("state.json", 'r') as f:
            state_data = json.load(f)
        state = State(state_data["stacks"], state_data["containers"])

        with open("tabu_list.json", 'r') as f:
            tabu_data = json.load(f)
        tabu_data["tabu_moves"] = [tuple(m) for m in tabu_data.get("tabu_moves", [])]

        # Load total late containers
        with open(late_containers_file, 'r') as f:
            late_data = json.load(f)
            total_late = set(late_data["total_late"])

        if tabu_data["iterations"] >= 100:
            print("Resetting tabu list after 100 iterations")
            print(f"Total containers that were late: {len(total_late)}")
            print(f"Container IDs that were late: {sorted(list(total_late))}")
            tabu_data = {"iterations": 0, "tabu_moves": []}
            safe_write_json("tabu_list.json", tabu_data)
            safe_write_move("bestmove.txt", "5 5")
            return

        ts = TabuSearch(tabu_list=tabu_data["tabu_moves"])
        move, new_state = ts.find_best_move(state)

        if move is not None:
            stack_map = {"A0": 0, "B0": 1, "B1": 2, "B2": 3, "H0": 4}
            try:
                move_str = f"{stack_map[move[0]]} {stack_map[move[1]]}"
            except KeyError as e:
                print(f"Invalid stack in move: {move}", file=sys.stderr)
                raise ValueError(f"Invalid stack name in move {move}")

            safe_write_move("bestmove.txt", move_str)
            
            # Update total late containers
            total_late.update(new_state.late_containers)
            late_data["total_late"] = list(total_late)
            late_data["count"] = len(total_late)
            safe_write_json(late_containers_file, late_data)
            
            safe_write_json("state.json", new_state.to_dict())
            
            ts.add_to_tabu(move)
            tabu_data["tabu_moves"] = ts.tabu_list
            tabu_data["iterations"] += 1
            safe_write_json("tabu_list.json", tabu_data)
        else:
            print("No valid move found")
            print(f"Total containers that were late: {len(total_late)}")
            print(f"Container IDs that were late: {sorted(list(total_late))}")
            safe_write_move("bestmove.txt", "5 5")

    except Exception as e:
        print(f"Critical error in main: {e}", file=sys.stderr)
        if not os.path.exists("tabu_list.json"):
            with open("tabu_list.json", 'w') as f:
                json.dump({"iterations": 0, "tabu_moves": []}, f)
        safe_write_move("bestmove.txt", "5 5")
        sys.exit(1)

if __name__ == "__main__":
    main()