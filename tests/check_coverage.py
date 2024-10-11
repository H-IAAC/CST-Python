import json

if __name__ == "__main__":

    with open("coverage.json") as file:
        coverage_info = json.load(file)

    assert coverage_info["totals"]["percent_covered"] > 75