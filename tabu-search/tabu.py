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

        
    """Heuristic report written to heuristic_report.json with overall grade 60.38"""
    """def evaluate_state(self, state: State) -> int:
        total_cost = 0
        
        # First, sort containers by urgency with special handling for negative times
        all_containers = list(state.containers.values())
        if not all_containers:
            return 0
            
        # Sort containers by:
        # 1. Negative status (expired containers first)
        # 2. Within expired containers, most expired first (smallest negative number)
        # 3. For positive times, smallest time first
        sorted_containers = sorted(all_containers, 
            key=lambda c: (c.total_seconds() >= 0, 
                        c.total_seconds() if c.total_seconds() >= 0 else -c.total_seconds()))
        
        # Calculate cost based on how many containers are blocking the most urgent ones
        for i, container in enumerate(sorted_containers):
            stack = state.get_container_position(container.id)
            if stack == "H0":
                continue  # already in hand, no cost
                
            # Find how many containers are above this one in its stack
            stack_containers = state.stack_contents[stack]
            try:
                index = [c.id for c in stack_containers].index(container.id)
                blocking_containers = len(stack_containers) - index - 1
            except ValueError:
                blocking_containers = 0
                
            # Calculate urgency weight
            if container.total_seconds() < 0:
                # Expired containers get maximum priority
                # The more negative, the higher the priority
                urgency_weight = 1000 - container.total_seconds()
            else:
                # For non-expired containers, use their position in the sorted list
                urgency_weight = len(sorted_containers) - i
                
            total_cost += blocking_containers * urgency_weight * 10
            
            # Additional penalty for not being in H0
            if stack != "H0":
                total_cost += 5 * urgency_weight
                
        return total_cost"""
        
    """Heuristic report written to heuristic_report.json with overall grade 49.87"""
    """def evaluate_state(self, state: State) -> int:
        total = 0
        for container in state.containers.values():
            total += container.total_seconds()
        for stack, containers in state.stack_contents.items():
            if stack != "H0":
                total += len(containers) * 10
        return total"""
        
    def evaluate_state(self, state: State) -> int:
        # Parse crane operation times
        times = parse_ulaz_times()
        CLEARING = times.get("clear", 5)
        MOVE = times.get("move", 1)
        LIFT = times.get("lift", 0)
        LOWER = times.get("lower", 0)
        
        total_cost = 0
        all_containers = list(state.containers.values())
        
        if not all_containers:
            return 0

        # Sort containers: overdue first (most negative first), then urgent
        sorted_containers = sorted(
            all_containers,
            key=lambda c: (c.total_seconds() < 0, c.total_seconds())
        )
        most_urgent = sorted_containers[0]

        # Stack distances to H0 (in crane moves)
        stack_dist = {"A0": 4, "B0": 3, "B1": 2, "B2": 1, "H0": 0}
        
        for i, container in enumerate(sorted_containers):
            stack = state.get_container_position(container.id)
            stack_containers = state.stack_contents[stack]
            
            # Skip containers in H0 that are processed
            if stack == "H0":
                # Bonus for having containers ready to ship
                if container.total_seconds() <= 60:
                    total_cost -= 100000 * (len(sorted_containers) - i)
                continue
                
            try:
                idx = [c.id for c in stack_containers].index(container.id)
                blockers = len(stack_containers) - idx - 1
            except ValueError:
                blockers = 0
                
            # Calculate time to ship this container (in seconds)
            time_to_ship = (
                blockers * (2*CLEARING + 2*MOVE + LIFT + LOWER) +  # Clear blockers
                stack_dist[stack] * MOVE +  # Move to stack
                CLEARING + LIFT +  # Lift container
                stack_dist[stack] * MOVE +  # Move to H0
                CLEARING + LOWER    # Lower at H0
            )
            
            # CRITICAL: Overdue container handling
            if container.total_seconds() < 0:
                # Extreme penalty for overdue containers not in H0
                lateness = abs(container.total_seconds()) + time_to_ship
                cost = 1000000 * lateness
            else:
                # For non-overdue, focus on risk of becoming overdue
                time_left = container.total_seconds()
                risk_factor = max(0, time_left - time_to_ship)
                
                # High risk if < 30 seconds buffer
                if risk_factor < 30:
                    cost = 500000 / (1 + risk_factor)
                else:
                    # Normal priority based on position
                    cost = (len(sorted_containers) - i) * 1000
            
            # Additional blocker penalty (exponential)
            cost += (2 ** blockers) * 5000
            
            total_cost += cost
        
        # Global optimization penalties
        h0_containers = state.stack_contents.get("H0", [])
        h0_count = len(h0_containers)
        
        # Severe penalty for multiple containers in H0
        if h0_count > 1:
            total_cost += 1000000 * h0_count
            
        # Reward having the most urgent container in H0
        if h0_count == 1 and h0_containers[0].id == most_urgent.id:
            total_cost -= 500000
            
        return int(total_cost)

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
        # Write safe default directly
        with open(file_path, 'w') as f:
            f.write("5 5\n")
        raise
    
def grade_heuristic(ts_class, state_class, num_tests=10):
    """
    Grades the heuristic by evaluating a set of test states.
    Normalizes each batch of scores to 0-100, accumulates batch averages,
    and reports the overall average grade.
    """
    import os

    stacks = ["A0", "B0", "B1", "B2", "H0"]
    grades = []
    details = []

    for i in range(num_tests):
        containers = []
        for cid in range(5):
            minutes = random.randint(-5, 10)
            seconds = random.randint(0, 59)
            stack = random.choice(stacks[:-1])
            containers.append({
                "id": f"C{cid}",
                "stack": stack,
                "minutes": minutes,
                "seconds": seconds
            })
        containers.append({
            "id": "C_opt",
            "stack": "H0",
            "minutes": 0,
            "seconds": 0
        })

        state = state_class(stacks, containers)
        ts = ts_class([])
        score = ts.evaluate_state(state)
        details.append({"test": i, "score": score, "containers": containers})
        grades.append(score)

    # Normalize current batch of scores to 0-100
    min_score = min(grades)
    max_score = max(grades)
    if max_score == min_score:
        normalized_scores = [100 for _ in grades]
    else:
        normalized_scores = [
            int(100 * (max_score - s) / (max_score - min_score)) for s in grades
        ]
    batch_average = sum(normalized_scores) / len(normalized_scores)

    # Accumulate batch averages
    averages_file = "heuristic_normalized_averages.json"
    if os.path.exists(averages_file):
        with open(averages_file, "r") as f:
            all_averages = json.load(f)
    else:
        all_averages = []

    all_averages.append(batch_average)
    with open(averages_file, "w") as f:
        json.dump(all_averages, f, indent=2)

    overall_grade = sum(all_averages) / len(all_averages) if all_averages else 0

    report = {
        "overall_grade": overall_grade,
        "last_batch_average": batch_average,
        "normalized_scores": normalized_scores,
        "test_details": details,
        "total_batches": len(all_averages)
    }
    with open("heuristic_report.json", "w") as f:
        json.dump(report, f, indent=2)
    print(f"Heuristic report written to heuristic_report.json with overall grade {overall_grade:.2f}")
    
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
    grade_heuristic(TabuSearch, State)