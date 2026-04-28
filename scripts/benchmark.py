import statistics
import time

from app import create_app
from models import db
from services.rating_service import build_leaderboard


def run_benchmark(iterations=10):
    app = create_app()
    app.config["TESTING"] = True

    times = []

    with app.app_context():
        print(f"Starting benchmark ({iterations} iterations)...")
        # Warm up
        build_leaderboard(db.session)

        for i in range(iterations):
            start = time.time()
            build_leaderboard(db.session)
            end = time.time()
            elapsed_ms = (end - start) * 1000
            times.append(elapsed_ms)
            print(f"Iteration {i+1}: {elapsed_ms:.2f} ms")

    avg = statistics.mean(times)
    med = statistics.median(times)
    print("\nResults:")
    print(f"Average: {avg:.2f} ms")
    print(f"Median:  {med:.2f} ms")
    print(f"Min:     {min(times):.2f} ms")
    print(f"Max:     {max(times):.2f} ms")


if __name__ == "__main__":
    run_benchmark()
