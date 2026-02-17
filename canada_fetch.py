#!/usr/bin/env python3
"""
Canada Health Product & Medical Device Recalls Fetcher
Source: Health Canada / CFIA Recalls & Safety Alerts open data
Bulk JSON updated daily — no API key or pagination needed.
"""

import requests
import pandas as pd
from datetime import datetime, date
from io import StringIO

BULK_URL = (
    "https://recalls-rappels.canada.ca/sites/default/files/"
    "opendata-donneesouvertes/HCRSAMOpenData.json"
)

# Recall class severity order (Type I = most severe)
RECALL_CLASS_ORDER = {"Type I": 0, "Type II": 1, "Type III": 2, "": 3}

# Known device categories in the dataset
DEVICE_CATEGORIES = [
    "Anaesthesiology",
    "Cardiovascular",
    "Dental",
    "Ear, nose and throat",
    "Gastroenterology and urology",
    "General and plastic surgery",
    "General hospital and personal use",
    "In vitro diagnostics",
    "Neurology",
    "Obstetrics and gynaecology",
    "Ophthalmic",
    "Orthopaedic",
    "Physical medicine",
    "Radiology",
]


class CanadaRecallsFetcher:
    """Fetch and filter Canadian medical device recall data."""

    def __init__(self):
        self._cache: list | None = None
        self._cache_time: datetime | None = None
        self._cache_ttl_minutes = 60  # re-download at most once per hour

    # ── Core fetch ────────────────────────────────────────────────────────────

    def fetch_all_raw(self, force: bool = False) -> list[dict]:
        """
        Download the full bulk JSON from Health Canada.
        Result is cached in-memory for `_cache_ttl_minutes` minutes.
        """
        now = datetime.now()
        if (
            not force
            and self._cache is not None
            and self._cache_time is not None
            and (now - self._cache_time).seconds < self._cache_ttl_minutes * 60
        ):
            return self._cache

        resp = requests.get(BULK_URL, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        self._cache = data
        self._cache_time = now
        return data

    def fetch_medical_devices(self, force: bool = False) -> list[dict]:
        """Return only records where Organization == 'Medical devices'."""
        raw = self.fetch_all_raw(force=force)
        return [r for r in raw if r.get("Organization") == "Medical devices"]

    # ── Filter & search ───────────────────────────────────────────────────────

    def search(
        self,
        product: str = "",
        category: str = "",
        recall_class: str = "",
        issue: str = "",
        date_from: str = "",   # YYYY-MM-DD
        date_to: str = "",     # YYYY-MM-DD
        include_archived: bool = False,
    ) -> pd.DataFrame:
        """
        Filter medical device recalls and return a pandas DataFrame.

        All text filters are case-insensitive substring matches.
        """
        records = self.fetch_medical_devices()

        results = []
        for r in records:
            # Archived filter
            if not include_archived and r.get("Archived", "0") == "1":
                continue

            # Date filter on "Last updated"
            rec_date_str = r.get("Last updated", "")
            if rec_date_str:
                try:
                    rec_date = date.fromisoformat(rec_date_str)
                    if date_from and rec_date < date.fromisoformat(date_from):
                        continue
                    if date_to and rec_date > date.fromisoformat(date_to):
                        continue
                except ValueError:
                    pass

            # Product / title search
            if product:
                haystack = (
                    (r.get("Product") or "") + " " + (r.get("Title") or "")
                ).lower()
                if product.lower() not in haystack:
                    continue

            # Category filter (multi-category records use " - " separator)
            if category:
                if category.lower() not in (r.get("Category") or "").lower():
                    continue

            # Recall class filter
            if recall_class:
                if recall_class != (r.get("Recall class") or "").strip():
                    continue

            # Issue / hazard filter
            if issue:
                if issue.lower() not in (r.get("Issue") or "").lower():
                    continue

            results.append(r)

        if not results:
            return pd.DataFrame()

        df = pd.DataFrame(results)

        # Normalise columns
        df = df.rename(columns={
            "NID":           "recall_id",
            "Title":         "title",
            "URL":           "url",
            "Organization":  "organization",
            "Product":       "product",
            "Issue":         "issue",
            "What you should do": "action",
            "Category":      "category",
            "Recall class":  "recall_class",
            "Last updated":  "last_updated",
            "Archived":      "archived",
        })

        # Sort: most severe class first, then most recent
        df["_class_order"] = df["recall_class"].map(
            lambda x: RECALL_CLASS_ORDER.get(x, 3)
        )
        df["last_updated"] = pd.to_datetime(df["last_updated"], errors="coerce")
        df = df.sort_values(
            ["_class_order", "last_updated"], ascending=[True, False]
        ).drop(columns=["_class_order"])

        return df.reset_index(drop=True)

    # ── Stats helpers ──────────────────────────────────────────────────────────

    def summary_stats(self, df: pd.DataFrame) -> dict:
        if df.empty:
            return {"total": 0, "type_i": 0, "type_ii": 0, "type_iii": 0, "categories": 0}
        return {
            "total":      len(df),
            "type_i":     int((df["recall_class"] == "Type I").sum()),
            "type_ii":    int((df["recall_class"] == "Type II").sum()),
            "type_iii":   int((df["recall_class"] == "Type III").sum()),
            "categories": df["category"].nunique(),
        }