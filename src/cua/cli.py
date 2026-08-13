from __future__ import annotations
import argparse
import asyncio
import json
import logging
from pathlib import Path

from playwright.async_api import async_playwright

from cua.agent.model import AgentObservation
from cua.agent.offline import OfflinePlanner
from cua.agent.ollama import OllamaPlanner
from cua.artifact.compiler import demo_member_balance_artifact
from cua.escalation.manager import InterventionManager
from cua.logging_utils import configure
from cua.replay.engine import ReplayEngine
from cua.replay.errors import BusinessOutcome, InterventionRequired, ReplayError

async def discover(args):
    logger = logging.getLogger("cua")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=not args.headed)
        page = await browser.new_page()
        await page.goto(args.url)
        surface = __import__("cua.surfaces.browser", fromlist=["BrowserSurface"]).BrowserSurface(page)
        planner = OfflinePlanner() if args.planner == "offline" else OllamaPlanner()

        for i in range(20):
            obs = await surface.observe()
            action = planner.next_action(
                args.goal,
                AgentObservation(**obs)
            )
            logger.info("discovery step=%s action=%s reason=%s", i + 1, action.type, action.reason)

            if action.type == "done":
                break
            if action.type == "fill":
                await surface.fill(action.strategy, action.target, action.value)
            elif action.type == "click":
                await surface.click(action.strategy, action.target)
            elif action.type == "extract":
                value = await surface.extract(action.strategy, action.target)
                logger.info("extracted output=%s", value)
            elif action.type == "navigate":
                await surface.navigate(action.value)

        artifact = demo_member_balance_artifact(args.url)
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(
            artifact.model_dump_json(indent=2),
            encoding="utf-8"
        )
        logger.info("artifact written to %s", args.output)
        await browser.close()

async def replay(args):
    logger = logging.getLogger("cua")
    artifact = __import__("cua.artifact.schema", fromlist=["CapabilityArtifact"]).CapabilityArtifact.model_validate_json(
        Path(args.artifact).read_text(encoding="utf-8")
    )
    intervention = InterventionManager(args.interventions)
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=not args.headed)
        page = await browser.new_page()
        surface = __import__("cua.surfaces.browser", fromlist=["BrowserSurface"]).BrowserSurface(page)
        engine = ReplayEngine(
            artifact, surface,
            intervention=intervention,
            escalate=args.escalate
        )
        try:
            result = await engine.run({"member_id": args.member_id})
            logger.info("REPLAY SUCCESS")
            print(json.dumps(result, indent=2))
        except BusinessOutcome as exc:
            logger.info("BUSINESS_OUTCOME %s", exc.outcome)
            print(f"BUSINESS_OUTCOME\n{exc.outcome}\n{exc}")
        except InterventionRequired as exc:
            logger.error("INTERVENTION_REQUIRED %s", exc)
            print(f"INTERVENTION_REQUIRED\n{exc}")
        except ReplayError as exc:
            logger.error("%s %s", exc.code, exc)
            print(f"{exc.code}\n{exc}")
        finally:
            if args.keep_open:
                await asyncio.sleep(3600)
            await browser.close()

def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)

    d = sub.add_parser("discover")
    d.add_argument("--url", required=True)
    d.add_argument("--goal", required=True)
    d.add_argument("--planner", choices=["offline", "ollama"], default="offline")
    d.add_argument("--output", default="evidence/discovery-artifact.json")
    d.add_argument("--log")
    d.add_argument("--headed", action="store_true")

    r = sub.add_parser("replay")
    r.add_argument("--artifact", required=True)
    r.add_argument("--url", required=True)
    r.add_argument("--member-id", required=True)
    r.add_argument("--log")
    r.add_argument("--headed", action="store_true")
    r.add_argument("--escalate", action="store_true")
    r.add_argument("--keep-open", action="store_true")
    r.add_argument("--interventions", default="evidence/interventions")

    args = parser.parse_args()
    configure(getattr(args, "log", None))

    if args.command == "discover":
        asyncio.run(discover(args))
    elif args.command == "replay":
        asyncio.run(replay(args))

if __name__ == "__main__":
    main()
