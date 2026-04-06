import argparse
import sys

from llm_tui.config import Config
from llm_tui.app import LlmTuiApp


def main():
    parser = argparse.ArgumentParser(description="Terminal UI for local LLM management")
    parser.add_argument("--manager-url", default=None, help="llm-manager URL (default: $LLM_MANAGER_URL or http://localhost:8000)")
    parser.add_argument("--router-url", default=None, help="llm-router URL (default: $LLM_ROUTER_URL or http://localhost:8012)")
    parser.add_argument("--gpu-poll", type=float, default=None, help="GPU poll interval in seconds (default: 2)")
    parser.add_argument("--api-poll", type=float, default=None, help="API poll interval in seconds (default: 5)")
    args = parser.parse_args()

    config = Config()
    if args.manager_url:
        config.manager_url = args.manager_url
    if args.router_url:
        config.router_url = args.router_url
    if args.gpu_poll:
        config.gpu_poll_interval = args.gpu_poll
    if args.api_poll:
        config.api_poll_interval = args.api_poll

    app = LlmTuiApp(config=config)
    app.run()


if __name__ == "__main__":
    main()
