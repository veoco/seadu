import asyncio, argparse, json
from pathlib import Path

from .download import Downloader
from .upload import Uploader
from .common import Settings

HOME = Path.home()
CONFIG_FILE = HOME / ".seadu/config.json"


async def run(settings: Settings, path: Path, runner: str, multi: int):
    Runner = Downloader if runner == "down" else Uploader

    async with Runner(
        server_url=settings.server_url, token=settings.token, base_dir=path, multi=multi
    ) as runner:
        await runner.run()


def init_config(args):
    if not CONFIG_FILE.parent.exists():
        CONFIG_FILE.parent.mkdir(parents=True)

    data = {
        "token": args.token,
        "server_url": args.server_url,
    }
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f)

    print("Config file initialized successfully")


def run_load(args):
    if not CONFIG_FILE.exists():
        print("Config file not exists")
        return

    settings = None
    with open(CONFIG_FILE, "r") as f:
        data = json.load(f)
        settings = Settings(**data)

    path = Path(args.path)
    asyncio.run(run(settings, path, args.command, args.multi))


def main():
    parser = argparse.ArgumentParser(
        prog="seadu",
        description="A command-line program for Seafile download and upload",
    )
    subparsers = parser.add_subparsers(dest="command")

    init_parser = subparsers.add_parser("init", help="Initialize configuration file.")
    init_parser.add_argument(
        "-s",
        "--server-url",
        help="Server URL, eg. http://cloud.seafile.com",
        required=True,
    )
    init_parser.add_argument("-t", "--token", help="API Token", required=True)

    download_parser = subparsers.add_parser("down", help="Download files")
    download_parser.add_argument("path", help="Path to download files")
    download_parser.add_argument(
        "-m", "--multi", help="Multi threads to download", default=4, type=int
    )

    upload_parser = subparsers.add_parser("up", help="Upload files")
    upload_parser.add_argument("path", help="Path to upload files")
    upload_parser.add_argument(
        "-m", "--multi", help="Multi threads to upload", default=4, type=int
    )

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
    elif args.command == "init":
        init_config(args)
    else:
        run_load(args)


if __name__ == "__main__":
    main()
