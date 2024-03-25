# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from datetime import datetime, timedelta
from typing import List, Optional

import pandas as pd

from ascutils import Feature, Record
from ascutils.ingestion.data import BaseData
from ascutils.ingestion.validation.common import _fields_exist, _not_null, _validate_referential_integrity
from ascutils.ingestion.validation.model import Status

INSIGHTS_FEATURES = [
    Feature.INSIGHTS_INVENTORY_VISIBILITY,
    Feature.INSIGHTS_NETWORK_MAP,
    Feature.INSIGHTS_INVENTORY_INSIGHTS,
    Feature.INSIGHTS_REBALANCE_RECOMMENDATIONS,
    Feature.INSIGHTS_LEAD_TIME_INSIGHTS,
]


def _validate_insights(data: BaseData, target_features: List[Feature]) -> List[Record]:
    if list(set(target_features) & set(INSIGHTS_FEATURES)) == 0:
        return []

    records = [
        _validate_inventory_level_referential_integrity_with_product(data),
        _validate_inventory_level_referential_integrity_with_site(data),
        _validate_site_referential_integrity_with_geography(data),
        _validate_product_referential_integrity_with_product_hierarchy(data),
        _validate_on_hand_inventory_level_has_non_zero_values(data),
        _validate_inbound_order_line_quantities_are_present(data),
        _validate_inbound_order_line_schedule_quantities_are_present(data),
        _validate_inventory_level_snapshot_date_is_valid_and_before_today(data)
    ]

    return [record for record in records if record is not None]


def _validate_inventory_level_referential_integrity_with_product(data: BaseData) -> Optional[Record]:
    return _validate_referential_integrity(
        data=data,
        left_entity="inventory_level",
        right_entity="product",
        left_on="product_id",
        right_on="id",
    )


def _validate_inventory_level_referential_integrity_with_site(data: BaseData) -> Optional[Record]:
    return _validate_referential_integrity(
        data=data,
        left_entity="inventory_level",
        right_entity="site",
        left_on="site_id",
        right_on="id",
    )


def _validate_site_referential_integrity_with_geography(data: BaseData) -> Optional[Record]:
    return _validate_referential_integrity(
        data=data,
        left_entity="site",
        right_entity="geography",
        left_on="geo_id",
        right_on="id"
    )


def _validate_product_referential_integrity_with_product_hierarchy(
    data: BaseData,
) -> Optional[Record]:
    return _validate_referential_integrity(
        data=data,
        left_entity="product",
        right_entity="product_hierarchy",
        left_on="product_group_id",
        right_on="id",
    )


def _validate_on_hand_inventory_level_has_non_zero_values(data: BaseData) -> Optional[Record]:
    inventory_level_df = data.get("inventory_level")

    prerequisites_met = all(
        [
            _not_null([inventory_level_df]),
            _fields_exist(inventory_level_df, ["on_hand_inventory"]),
        ]
    )

    if not prerequisites_met:
        return None
    assert inventory_level_df is not None  # Needed for type-checking

    inventory_level_df["on_hand_inventory"] = pd.to_numeric(inventory_level_df["on_hand_inventory"], errors="coerce")
    non_zero_inventory_df = inventory_level_df[inventory_level_df["on_hand_inventory"] > 0.0]

    if non_zero_inventory_df.shape[0] > 0:
        return None

    return Record(
        status=Status.WARNING,
        entity="inventory_level",
        description="'inventory_level' file has all zeros for the 'on_hand_inventory' column",
    )


def _validate_inventory_level_snapshot_date_is_valid_and_before_today(data: BaseData) -> Optional[Record]:
    inventory_level_df = data.get("inventory_level")

    prerequisites_met = all(
        [
            _not_null([inventory_level_df]),
            _fields_exist(inventory_level_df, ["snapshot_date"]),
        ]
    )

    if not prerequisites_met:
        return None
    assert inventory_level_df is not None  # Needed for type-checking

    inventory_level_df["snapshot_date"] = pd.to_datetime(inventory_level_df["snapshot_date"])
    max_snapshot_date = inventory_level_df["snapshot_date"].max()
    today = datetime.now()
    two_days_ago = today - timedelta(days=2)
    is_in_past_two_days = two_days_ago <= max_snapshot_date <= today

    if is_in_past_two_days:
        return None

    return Record(
        status=Status.WARNING,
        entity="inventory_level",
        description="There is no 'inventory_level.snapshot_date' with a value within the past two days",
    )


def _validate_inbound_order_line_quantities_are_present(data: BaseData) -> Optional[Record]:
    df = data.get("inbound_order_line")

    prerequisites_met = all(
        [
            _not_null([df]),
        ]
    )

    if not prerequisites_met:
        return None
    assert df is not None  # Needed for type-checking

    quantity_fields = ["quantity_submitted", "quantity_confirmed", "quantity_received"]
    for field in quantity_fields:
        if field in df.columns and df[~df[field].isna()].shape[0] > 0:
            return None

    return Record(
        status=Status.WARNING,
        entity="inbound_order_line",
        description=f"One of the following quantity fields should be set: {quantity_fields}",
    )


def _validate_inbound_order_line_schedule_quantities_are_present(data: BaseData,) -> Optional[Record]:
    df = data.get("inbound_order_line_schedule")

    prerequisites_met = all(
        [
            _not_null([df]),
        ]
    )

    if not prerequisites_met:
        return None
    assert df is not None  # Needed for type-checking

    quantity_fields = ["quantity_submitted", "quantity_confirmed", "quantity_received"]
    for field in quantity_fields:
        if field in df.columns and df[~df[field].isna()].shape[0] > 0:
            return None

    return Record(
        status=Status.WARNING,
        entity="inbound_order_line_schedule",
        description=f"One of the following quantity fields should be set: {quantity_fields}",
    )
