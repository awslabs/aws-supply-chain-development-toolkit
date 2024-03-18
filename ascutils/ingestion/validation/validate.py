# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from typing import List

from ascutils import Feature
from ascutils.ingestion.data import BaseData
from ascutils.ingestion.validation.demand_planning import _validate_demand_planning
from ascutils.ingestion.validation.insights import _validate_insights
from ascutils.ingestion.validation.model import Record
from ascutils.ingestion.validation.schema import _validate_schema


def validate(data: BaseData, target_features: List[Feature]) -> List[Record]:
    output: List[Record] = []

    output += _validate_schema(data, target_features)
    output += _validate_insights(data, target_features)
    output += _validate_demand_planning(data, target_features)

    return filter_unique_records(output)


def filter_unique_records(records: List[Record]) -> List[Record]:
    unique_combinations = {}
    for record in records:
        unique_key = (record.entity, record.description)
        unique_combinations[unique_key] = record
    return list(unique_combinations.values())
