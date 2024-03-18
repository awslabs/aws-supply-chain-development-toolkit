# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from typing import List, Optional

from ascutils import Feature, Record
from ascutils.ingestion.data import BaseData
from ascutils.ingestion.validation.common import _validate_referential_integrity

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
    ]

    return [record for record in records if record is not None]


def _validate_product_referential_integrity_with_outbound_order_line(
    data: BaseData,
) -> Optional[Record]:
    return _validate_referential_integrity(
        data=data,
        left_entity="product",
        right_entity="outbound_order_line",
        left_on="id",
        right_on="product_id",
    )
