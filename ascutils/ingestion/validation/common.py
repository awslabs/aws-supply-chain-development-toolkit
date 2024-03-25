# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from typing import List, Optional
from uuid import uuid4

from pandas import DataFrame

from ascutils.ingestion.data import BaseData
from ascutils.ingestion.validation.model import Record, Status


def _validate_referential_integrity(data: BaseData, left_entity: str, right_entity: str, left_on: str, right_on: str) -> Optional[Record]:
    left_df = data.get(left_entity)
    right_df = data.get(right_entity)

    prerequisites_met = all(
        [
            _not_null([left_df, right_df]),
            _fields_exist(left_df, [left_on]),
            _fields_exist(right_df, [right_on]),
        ]
    )

    if not prerequisites_met:
        return None
    assert left_df is not None  # Needed for type-checking
    assert right_df is not None  # Needed for type-checking

    unique_right_on = f"{right_on}_{uuid4()}"
    selected_left_df = left_df[[left_on]].drop_duplicates()
    selected_right_df = right_df[[right_on]].rename(columns={right_on: unique_right_on}).drop_duplicates()
    merged_df = selected_left_df.merge(selected_right_df, left_on=left_on, right_on=unique_right_on, how="left")
    missing_df = merged_df[merged_df[unique_right_on].isna()]

    if missing_df.empty:
        return None

    return Record(
        status=Status.WARNING,
        entity=left_entity,
        description=f"'{left_entity}.{left_on}' does not have referential integrity with '{right_entity}.{right_on}'",
        sample_data=missing_df[[left_on]].head(),
    )


def _not_null(dfs: List[DataFrame]) -> bool:
    return all([df is not None for df in dfs])


def _fields_exist(df: Optional[DataFrame], fields: List[str]) -> bool:
    if df is None:
        return False
    return all([field in df.columns for field in fields])
