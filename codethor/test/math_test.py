from statistics import mode


def top_25_percent_mode(numbers):
    numbers.sort()
    top_25_index = len(numbers) // 4

    return top_25_index, mode(numbers)


def top_percentile(lst, p):
    sortedl = sorted(lst)
    return sortedl[int(len(sortedl) * p / 100)]


# Example usage:
numbers = [1, 2, 2, 3, 4, 4, 4, 5, 5, 5, 6, 6, 6, 6, 6, 6, 6, 6, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
print(top_percentile(numbers, 70))
