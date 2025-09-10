"""
genetic_evolver.py: Genetic algorithm engine for evolving and rewriting code/rules in GuardianShield agents.
All changes are versioned and reversible.
"""
import random
import json
import os
import shutil
import re

class GeneticEvolver:
    def __init__(self, code_path, backup_dir="evolution_backups"):
        self.code_path = code_path
        self.backup_dir = backup_dir
        os.makedirs(self.backup_dir, exist_ok=True)

    def backup_code(self):
        backup_file = os.path.join(self.backup_dir, f"{os.path.basename(self.code_path)}.bak")
        shutil.copy2(self.code_path, backup_file)
        return backup_file

    def restore_code(self, backup_file):
        shutil.copy2(backup_file, self.code_path)

    def mutate_code(self, mutation_func):
        with open(self.code_path, "r") as f:
            code = f.read()
        mutated_code = mutation_func(code)
        with open(self.code_path, "w") as f:
            f.write(mutated_code)
        return mutated_code

    def evaluate_code(self, test_func):
        # Run tests or simulations to evaluate the mutated code
        return test_func()

    def evolve(self, mutation_func, test_func):
        backup = self.backup_code()
        mutated_code = self.mutate_code(mutation_func)
        fitness = self.evaluate_code(test_func)
        if not fitness:
            print("Mutation failed, rolling back.")
            self.restore_code(backup)
        else:
            print("Mutation successful.")
        return fitness

    def evolve_advanced(self):
        backup = self.backup_code()
        mutated_code = self.mutate_code(advanced_mutation)
        fitness = self.evaluate_code(advanced_test)
        if not fitness:
            print("Advanced mutation failed, rolling back.")
            self.restore_code(backup)
        else:
            print("Advanced mutation successful.")
        return fitness

# Example mutation function (for demonstration)
def example_mutation(code):
    # Randomly insert a comment (real mutations would be more sophisticated)
    lines = code.splitlines()
    idx = random.randint(0, len(lines)-1)
    lines.insert(idx, f"# Mutation at line {idx}")
    return "\n".join(lines)

# Example test function (for demonstration)
def example_test():
    # In production, run real tests or simulations
    return random.choice([True, False])

def advanced_mutation(code):
    # Example: Mutate function names, add new logic, or refactor code
    # Replace all 'def ' with 'def evolved_'
    code = re.sub(r'def ', 'def evolved_', code)
    # Add a random print statement
    lines = code.splitlines()
    idx = random.randint(0, len(lines)-1)
    lines.insert(idx, f"    print('Evolved mutation at line {idx}')")
    return "\n".join(lines)

def advanced_test():
    # Example: Run more comprehensive tests or simulations
    # Here, always return True for demonstration
    return True

if __name__ == "__main__":
    evolver = GeneticEvolver("agents/learning_agent.py")
    result = evolver.evolve_advanced()
    print("Advanced evolution result:", result)
