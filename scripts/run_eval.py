from movie_intelligence_agent.cli import main


if __name__ == "__main__":
    import sys

    args = ["eval", "--force-local"]
    sys.argv = [sys.argv[0], *args]
    main()
