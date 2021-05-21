"""Command-line interface."""
import click


@click.command()
@click.version_option()
def main() -> None:
    """Joseki."""


if __name__ == "__main__":
    main(prog_name="joseki")  # pragma: no cover
