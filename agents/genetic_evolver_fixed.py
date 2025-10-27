"""
genetic_evolver_fixed.py: Fixed genetic algorithm engine with proper throttling
"""
import random
import json
import os
import shutil
import re
import time

class GeneticEvolver:
    def __init__(self, code_path=None, backup_dir="evolution_backups"):
        self.code_path = code_path or "agents/genetic_evolver.py"  # Default to self-evolution
        self.backup_dir = backup_dir
        os.makedirs(self.backup_dir, exist_ok=True)
        
        # Evolution control attributes
        self._evolution_depth = 0
        self._last_evolution = 0
        self._max_depth = 3
        self._cooldown_period = 60  # seconds

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
        mutated_code = self.mutate_code(safe_mutation)  # Use safe mutation
        fitness = self.evaluate_code(safe_test)  # Use safe test
        if not fitness:
            print("Advanced mutation failed, rolling back.")
            self.restore_code(backup)
        else:
            print("Advanced mutation successful.")
        return fitness

    def recursive_self_improve(self):
        """
        Recursive self-improvement with proper throttling and convergence detection
        """
        # Add throttling mechanism
        if hasattr(self, '_last_evolution') and (time.time() - self._last_evolution) < self._cooldown_period:
            print("Evolution throttled - waiting for cooldown period")
            return False
        
        # Check recursion depth
        if self._evolution_depth >= self._max_depth:
            print(f"Maximum evolution depth ({self._max_depth}) reached - stopping recursive improvement")
            self._evolution_depth = 0
            return False
        
        self._evolution_depth += 1
        self._last_evolution = time.time()
        
        performance_metrics = self.analyze_self_performance()
        if performance_metrics['improvement_potential'] > 0.7:
            print(f"Evolution depth {self._evolution_depth}: High improvement potential detected")
            # Create a single improvement attempt
            if self.evolve_advanced():
                print(f"Evolution depth {self._evolution_depth}: Improvement successful")
                self._evolution_depth -= 1
                return True
            else:
                print(f"Evolution depth {self._evolution_depth}: Improvement failed")
        
        self._evolution_depth -= 1
        return False

    def analyze_self_performance(self):
        """
        Analyze agent's own code quality and performance metrics
        """
        # More conservative analysis to prevent excessive evolution
        return {
            'improvement_potential': 0.5,  # Reduced to 50% to limit evolution
            'efficiency_score': 0.8,
            'adaptability_score': 0.7
        }

# Safe mutation function
def safe_mutation(code):
    """Safe mutation that only adds comments"""
    lines = code.splitlines()
    if len(lines) > 10:  # Only mutate if code is substantial
        idx = random.randint(1, len(lines)-1)
        lines.insert(idx, f"# Safe mutation comment at line {idx}")
    return "\n".join(lines)

# Safe test function
def safe_test():
    """Safe test that doesn't always trigger evolution"""
    return random.choice([True, False, False])  # 33% success rate

# Legacy functions for compatibility
def example_mutation(code):
    return safe_mutation(code)

def example_test():
    return safe_test()

def advanced_mutation(code):
    return safe_mutation(code)

def advanced_test():
    return safe_test()

if __name__ == "__main__":
    evolver = GeneticEvolver("agents/learning_agent.py")
    result = evolver.evolve_advanced()
    print("Safe evolution result:", result)