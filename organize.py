import random
import math
import pandas as pd
import json
from statistics import variance

with open("books.json", "r") as f:
    books = [json.loads(line) for line in f]

processed_books = []
for book in books:
    if "Dimensions" in book:
        book["width"] = int(book["Dimensions"].split("x")[1].strip(" mm"))
        book["weight"] = int(book["Weight"].strip("g"))
        processed_books.append(book)

num_shelves = 7
shelf_width = 800
max_weight = 10000


def calculate_author_proximity(shelves):
    penalty = 0
    for author in set(book["Author"] for shelf in shelves for book in shelf):
        positions = [
            (i, j)
            for i, shelf in enumerate(shelves)
            for j, book in enumerate(shelf)
            if book["Author"] == author
        ]
        if len(positions) > 1:
            for j in range(len(positions) - 1):
                shelf_diff = abs(positions[j + 1][0] - positions[j][0])
                index_diff = abs(positions[j + 1][1] - positions[j][1])
                penalty += shelf_diff + index_diff
    return penalty


def is_valid_solution(shelves, shelf_width, max_weight):
    for shelf in shelves:
        if sum(book["width"] for book in shelf) > shelf_width:
            return False
        if sum(book["weight"] for book in shelf) > max_weight:
            return False
    return True


def objective_function(shelves):
    if not is_valid_solution(shelves, shelf_width, max_weight):
        return float("inf")
    space_penalty = sum(
        shelf_width - sum(book["width"] for book in shelf) for shelf in shelves
    )
    weight_variance_penalty = (
        variance([sum(book["weight"] for book in shelf) for shelf in shelves])
        if len(shelves) > 1
        else 0
    )
    author_proximity_penalty = calculate_author_proximity(shelves)
    total_penalty = (
        50 * space_penalty
        + 20 * weight_variance_penalty
        + 10 * author_proximity_penalty
    )
    return total_penalty


def generate_initial_solution(books, shelves):
    solution = [[] for _ in range(shelves)]
    author_groups = {}
    for book in books:
        if book["Author"] not in author_groups:
            author_groups[book["Author"]] = []
        author_groups[book["Author"]].append(book)

    for author, books_by_author in author_groups.items():
        placed = False
        attempt_count = 0
        while not placed and attempt_count < 100:
            shelf_idx = random.choice(range(shelves))
            if (
                sum(b["width"] for b in solution[shelf_idx])
                + sum(b["width"] for b in books_by_author)
                <= shelf_width
                and sum(b["weight"] for b in solution[shelf_idx])
                + sum(b["weight"] for b in books_by_author)
                <= max_weight
            ):
                solution[shelf_idx].extend(books_by_author)
                placed = True
            attempt_count += 1
    return solution


def cooling_schedule(T, alpha):
    return T * alpha


def perturb_solution(solution, shelf_width, max_weight):
    new_solution = [shelf[:] for shelf in solution]
    valid_move = False
    attempt_count = 0
    while not valid_move and attempt_count < 100:
        shelf1, shelf2 = random.sample(range(len(new_solution)), 2)
        if new_solution[shelf1]:
            book_idx = random.choice(range(len(new_solution[shelf1])))
            book = new_solution[shelf1].pop(book_idx)

            if (
                sum(b["width"] for b in new_solution[shelf2]) + book["width"]
                <= shelf_width
                and sum(b["weight"] for b in new_solution[shelf2]) + book["weight"]
                <= max_weight
            ):
                new_solution[shelf2].append(book)
                valid_move = True
            else:
                new_solution[shelf1].append(book)
        attempt_count += 1

    for shelf in new_solution:
        shelf.sort(key=lambda x: x["Author"])

    return new_solution


def simulated_annealing(books, num_shelves, shelf_width, max_weight):
    T = 1000.0
    alpha = 0.95
    max_iterations = 10000
    current_solution = generate_initial_solution(books, num_shelves)
    current_cost = objective_function(current_solution)
    best_solution = current_solution
    best_cost = current_cost

    for _ in range(max_iterations):
        T = cooling_schedule(T, alpha)
        if T <= 1e-3:
            break

        new_solution = perturb_solution(current_solution, shelf_width, max_weight)
        if not is_valid_solution(new_solution, shelf_width, max_weight):
            continue

        new_cost = objective_function(new_solution)

        delta = new_cost - current_cost
        acceptance_prob = math.exp(-delta / T) if delta > 0 else 1.0

        if random.random() < acceptance_prob:
            current_solution = new_solution
            current_cost = new_cost

            if new_cost < best_cost:
                best_solution = new_solution
                best_cost = new_cost

    return best_solution


best_arrangement = simulated_annealing(
    processed_books, num_shelves, shelf_width, max_weight
)

for i, shelf in enumerate(best_arrangement):
    total_weight = sum(book["weight"] for book in shelf)
    total_width = sum(book["width"] for book in shelf)
    print(
        f"Shelf {i + 1} (Total Width: {total_width} mm, Total Weight: {total_weight} g):"
    )
    for book in shelf:
        print(
            f"  - {book['Author']} - {book['Title']} (Width: {book['width']} mm, Weight: {book['weight']} g)"
        )
    print()


# Final result test
def final_result_test(best_arrangement, shelf_width, max_weight):
    for i, shelf in enumerate(best_arrangement):
        total_width = sum(book["width"] for book in shelf)
        total_weight = sum(book["weight"] for book in shelf)
        assert (
            total_width <= shelf_width
        ), f"Shelf {i + 1} exceeds width limit: {total_width} mm (limit: {shelf_width} mm)"
        assert (
            total_weight <= max_weight
        ), f"Shelf {i + 1} exceeds weight limit: {total_weight} g (limit: {max_weight} g)"
        print(
            f"Shelf {i + 1} is within limits: Width {total_width} mm / {shelf_width} mm, Weight {total_weight} g / {max_weight} g"
        )

    for shelf in best_arrangement:
        author_books = {}
        for idx, book in enumerate(shelf):
            author = book["Author"]
            if author not in author_books:
                author_books[author] = []
            author_books[author].append(idx)
        for positions in author_books.values():
            if len(positions) > 1:
                assert (
                    max(positions) - min(positions) == len(positions) - 1
                ), f"Books by the same author are not adjacent: {positions}"
        print("All books by the same author are adjacent in each shelf.")


if __name__ == "__main__":
    final_result_test(best_arrangement, shelf_width, max_weight)
    print("Final result test passed successfully.")