"""Sync GPT-Lab models into the compliance registry from the command line.

Usage (from backend/):
    python -m scripts.sync_gptlab_models
    python -m scripts.sync_gptlab_models --deactivate-demos
"""

from __future__ import annotations

import argparse
import asyncio
import sys

from app.db.session import AsyncSessionLocal
from app.services.gptlab_model_sync_service import GptLabModelSyncService
from fastapi import HTTPException


async def _run(
    *,
    approve_new: bool,
    deactivate_demos: bool,
    deactivate_missing: bool,
) -> int:
    async with AsyncSessionLocal() as session:
        service = GptLabModelSyncService(session)
        try:
            result = await service.sync(
                actor_user_id=None,
                approve_new=approve_new,
                deactivate_demos=deactivate_demos,
                deactivate_missing=deactivate_missing,
            )
        except HTTPException as exc:
            print(f"Sync failed: {exc.detail}", file=sys.stderr)
            await session.rollback()
            return 1
        except Exception as exc:
            print(f"Sync failed: {exc}", file=sys.stderr)
            await session.rollback()
            return 1

        await session.commit()
        print(
            f"GPT-Lab sync complete: created={result.created}, updated={result.updated}, "
            f"deactivated={result.deactivated}, demos_deactivated={result.demos_deactivated}"
        )
        if result.models_synced:
            print(f"Synced models ({len(result.models_synced)}):")
            for name in result.models_synced:
                print(f"  - {name}")
        if result.skipped:
            print(f"Skipped non-chat models ({len(result.skipped)}):")
            for name in result.skipped:
                print(f"  - {name}")
        return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Sync GPT-Lab models into ComplianceGuard")
    parser.add_argument(
        "--no-approve-new",
        action="store_true",
        help="Register new models as not approved",
    )
    parser.add_argument(
        "--deactivate-demos",
        action="store_true",
        help="Deactivate seeded DEMO_* models after sync",
    )
    parser.add_argument(
        "--keep-missing",
        action="store_true",
        help="Do not deactivate GPTLAB_* models removed from the remote farm",
    )
    args = parser.parse_args()
    code = asyncio.run(
        _run(
            approve_new=not args.no_approve_new,
            deactivate_demos=args.deactivate_demos,
            deactivate_missing=not args.keep_missing,
        )
    )
    raise SystemExit(code)


if __name__ == "__main__":
    main()
