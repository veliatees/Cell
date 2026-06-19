from cell_engine.io.snapshots import snapshot_to_json
from cell_engine.processes.hepatocyte import build_hepatocyte_definition, initial_hepatocyte_state


def main() -> None:
    definition = build_hepatocyte_definition()
    state = initial_hepatocyte_state(definition)
    print(snapshot_to_json(definition, state))


if __name__ == "__main__":
    main()

