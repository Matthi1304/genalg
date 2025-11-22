import sys
import visualization

if __name__ == "__main__":
    if len(sys.argv) > 1:
        visualization.start(config=sys.argv[1])
    else:
        visualization.start()