# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from typing import List, Optional

import pandas as pd

from ascutils import Feature, Record
from ascutils.ingestion.data import BaseData
from ascutils.ingestion.validation.common import _validate_referential_integrity, _not_null, _fields_exist
from ascutils.ingestion.validation.model import Status

DEMAND_PLANNING_FEATURES = [
    Feature.DEMAND_PLANNING_FORECAST,
    Feature.DEMAND_PLANNING_PRODUCT_LINEAGE,
    Feature.DEMAND_PLANNING_SUPPLEMENTARY_TIME_SERIES,
]


def _validate_demand_planning(data: BaseData, target_features: List[Feature]) -> List[Record]:
    if list(set(target_features) & set(DEMAND_PLANNING_FEATURES)) == 0:
        return []

    records = [
        _validate_product_referential_integrity_with_outbound_order_line(data),
        _validate_max_forecast_horizon(data)
    ]

    return [record for record in records if record is not None]


def _validate_product_referential_integrity_with_outbound_order_line(data: BaseData) -> Optional[Record]:
    return _validate_referential_integrity(
        data=data,
        left_entity="product",
        right_entity="outbound_order_line",
        left_on="id",
        right_on="product_id",
    )


def _validate_max_forecast_horizon(data: BaseData) -> Optional[Record]:
    outbound_order_line = data.get("outbound_order_line")

    prerequisites_met = all(
        [
            _not_null([outbound_order_line]),
            _fields_exist(outbound_order_line, ["product_id", "order_date"]),
        ]
    )

    if not prerequisites_met:
        return None
    assert outbound_order_line is not None  # Needed for type-checking

    copy_df = outbound_order_line.copy(deep=True)
    copy_df['order_date'] = pd.to_datetime(copy_df['order_date'], errors='coerce')
    min_df = copy_df[["product_id", "order_date"]].groupby("product_id").min().reset_index()
    max_df = copy_df[["product_id", "order_date"]].groupby("product_id").max().reset_index()
    merged_df = min_df.merge(max_df, on='product_id')
    merged_df['longest_range'] = merged_df['order_date_y'] - merged_df['order_date_x']
    max_horizon_days = merged_df['longest_range'].max().days / 4

    return Record(
        status=Status.WARNING,
        entity="outbound_order_line",
        description=f"Your demand planning forecast maximum horizon length is {int(max_horizon_days)} days (or {int(max_horizon_days/7)} weeks, {int(max_horizon_days/30)} months)",
    )
