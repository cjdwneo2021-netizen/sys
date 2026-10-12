import argparse
import sys

from .config import Config
from .drive import Drive, synchronize
from .model import Deferred, Generator
from .monitoring import record_operation
from .pipeline import generate_notes
from .render import render

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["sync", "build", "render", "models"])
    parser.add_argument("--root", default=".")
    args = parser.parse_args()
    config = Config.from_env(args.root)
    try:
        if args.command == "sync":
            if not config.folder_id:
                raise ValueError("Set DRIVE_FOLDER_ID")
            status, count = "failed", None
            try:
                count = len(synchronize(config, Drive()))
                status = "completed"
                print(f"Imported {count} lecture(s)")
            finally:
                record_operation(config, "sync", status, count)
                render(config.root)
        elif args.command == "build":
            generator = Generator(config)
            status, count = "failed", None
            try:
                count = len(generate_notes(config, generator))
                status = "completed"
                print(f"Generated {count} note(s)")
            except Deferred:
                status = "deferred"
                raise
            finally:
                generator.finish(status, count)
                record_operation(config, "build", status, count)
                render(config.root)
        elif args.command == "render":
            render(config.root)
        else:
            import os
            from google import genai
            client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
            for model in client.models.list():
                print(model.name)
    except Deferred as error:
        print(str(error))
    except (ValueError, RuntimeError) as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(1)
    except Exception as error:
        # Never dump request headers, access tokens or entire source documents.
        print(f"{type(error).__name__}: operation failed; check connection and configuration", file=sys.stderr)
        raise SystemExit(1)
