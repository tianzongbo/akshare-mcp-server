from __future__ import annotations

from datetime import datetime
import time
from typing import Any

import akshare as ak
import pandas as pd
from mcp.server.fastmcp import FastMCP

mcp = FastMCP(
    name="akshare-finance",
    instructions=(
        "Use these tools to retrieve China A-share market data and macro/index data via AkShare. "
        "Prefer get_a_share_quote for one symbol and get_a_share_history for date-range analysis."
    ),
)


def _normalize_symbol(symbol: str) -> str:
    text = symbol.strip()
    if text.isdigit() and len(text) < 6:
        return text.zfill(6)
    return text


def _validate_yyyymmdd(value: str, field_name: str) -> None:
    try:
        datetime.strptime(value, "%Y%m%d")
    except ValueError as exc:
        raise ValueError(f"{field_name} must be in YYYYMMDD format") from exc


def _to_sina_symbol(symbol: str) -> str:
    if symbol.startswith(("5", "6", "9")):
        return f"sh{symbol}"
    return f"sz{symbol}"


def _df_to_records(df: pd.DataFrame, limit: int) -> list[dict[str, Any]]:
    safe_df = df.where(pd.notnull(df), None)
    clipped = safe_df.head(max(limit, 0))
    return clipped.to_dict(orient="records")


@mcp.tool()
def get_a_share_quote(symbol: str) -> dict[str, Any]:
    normalized = _normalize_symbol(symbol)
    try:
        spot_df = ak.stock_zh_a_spot_em()
        rows = spot_df[spot_df["代码"] == normalized]
        if not rows.empty:
            return {
                "ok": True,
                "source": "stock_zh_a_spot_em",
                "symbol": normalized,
                "data": _df_to_records(rows, 1),
            }
    except Exception as exc:  # noqa: BLE001
        spot_error = str(exc)
    else:
        spot_error = "symbol not found in realtime source"

    try:
        hist_df = ak.stock_zh_a_daily(symbol=_to_sina_symbol(normalized))
        if hist_df.empty:
            return {
                "ok": False,
                "symbol": normalized,
                "error": "No data returned from fallback historical source",
                "realtime_error": spot_error,
            }
        latest = hist_df.tail(1)
        return {
            "ok": True,
            "source": "stock_zh_a_daily_fallback",
            "symbol": normalized,
            "note": "Realtime endpoint failed, returned latest daily bar as fallback",
            "realtime_error": spot_error,
            "data": _df_to_records(latest, 1),
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "ok": False,
            "symbol": normalized,
            "error": str(exc),
            "realtime_error": spot_error,
        }


@mcp.tool()
def get_a_share_history(
    symbol: str,
    start_date: str,
    end_date: str,
    period: str = "daily",
    adjust: str = "",
    limit: int = 120,
) -> dict[str, Any]:
    normalized = _normalize_symbol(symbol)
    _validate_yyyymmdd(start_date, "start_date")
    _validate_yyyymmdd(end_date, "end_date")
    if period not in {"daily", "weekly", "monthly"}:
        raise ValueError("period must be one of: daily, weekly, monthly")
    if adjust not in {"", "qfq", "hfq"}:
        raise ValueError("adjust must be one of: '', qfq, hfq")

    try:
        df = ak.stock_zh_a_hist(
            symbol=normalized,
            period=period,
            start_date=start_date,
            end_date=end_date,
            adjust=adjust,
        )
        source = "stock_zh_a_hist"
    except Exception as exc:  # noqa: BLE001
        if period != "daily":
            return {
                "ok": False,
                "symbol": normalized,
                "error": str(exc),
                "note": "Fallback only supports daily period",
            }
        daily_df = ak.stock_zh_a_daily(symbol=_to_sina_symbol(normalized)).copy()
        daily_df["date"] = pd.to_datetime(daily_df["date"], errors="coerce")
        start_dt = pd.to_datetime(start_date)
        end_dt = pd.to_datetime(end_date)
        df = daily_df[(daily_df["date"] >= start_dt) & (daily_df["date"] <= end_dt)]
        source = "stock_zh_a_daily_fallback"

    return {
        "ok": True,
        "source": source,
        "symbol": normalized,
        "rows": len(df),
        "data": _df_to_records(df, limit),
    }


@mcp.tool()
def get_china_index_snapshot(limit: int = 20) -> dict[str, Any]:
    for _ in range(2):
        try:
            df = ak.stock_zh_index_spot_sina()
            return {
                "ok": True,
                "source": "stock_zh_index_spot_sina",
                "rows": len(df),
                "data": _df_to_records(df, limit),
            }
        except Exception:  # noqa: BLE001
            time.sleep(1)

    symbols = ["sh000001", "sz399001", "sz399006"]
    data: list[dict[str, Any]] = []
    errors: list[str] = []
    for symbol in symbols:
        try:
            daily_df = ak.stock_zh_index_daily_em(symbol=symbol)
            latest = daily_df.tail(1).copy()
            latest.insert(0, "symbol", symbol)
            data.extend(_df_to_records(latest, 1))
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{symbol}: {exc}")

    if data:
        return {
            "ok": True,
            "source": "stock_zh_index_daily_em_fallback",
            "rows": len(data),
            "data": data[: max(limit, 0)],
            "note": "Used daily index fallback because snapshot endpoint was unavailable",
            "errors": errors,
        }

    return {
        "ok": False,
        "error": "All index sources failed",
        "errors": errors,
    }


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
