# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from typing import List

import pandas as pd
from pandas import DataFrame

from ascutils.ingestion.configs.entity import get_all_entities, Entity, EntityFieldType
from ascutils.ingestion.configs.module import get_all_modules, Feature
from ascutils.ingestion.data import BaseData
from ascutils.ingestion.validation.model import Record, Status


def _validate_schema(data: BaseData, target_features: List[Feature]) -> List[Record]:
    output: List[Record] = []

    output += _validate_ingestion_schema(data)
    output += _validate_modules_schema(data, target_features)

    return output


def _validate_ingestion_schema(data: BaseData) -> List[Record]:
    records: List[Record] = []

    for entity in get_all_entities():
        df: DataFrame = data.get(entity.displayName)

        if df is None:
            continue

        records += _validate_columns(
            df=df,
            entity_name=entity.displayName,
            fields=[field.name for field in entity.fields]
        )

        records += _validate_required_fields(
            df=df,
            entity_name=entity.displayName,
            fields=[f.name for f in entity.fields if (f.required or f.primaryKey) and f.name != "connection_id"],
        )

        records += _validate_duplicate_primary_keys(
            df=df,
            entity_name=entity.displayName,
            primary_keys=[f.name for f in entity.fields if f.primaryKey and f.name != "connection_id"],
        )

        records += _validate_type_casting(df=df, entity=entity)

    return records


def _validate_modules_schema(data: BaseData, target_features: List[Feature]) -> List[Record]:
    records: List[Record] = []

    for module in get_all_modules():
        for entity in module.entities:
            df: DataFrame = data.get(entity.name)

            if df is None and _is_required(target_features, entity.requiredFor):
                records.append(
                    Record(
                        entity=entity.name,
                        description=f"File for entity '{entity.name}' is missing",
                    )
                )
                continue
            elif df is None:
                continue

            records += _validate_required_fields(
                df=df,
                entity_name=entity.name,
                fields=[
                    f.name for f in entity.fields if _is_required(target_features, f.requiredFor)
                ],
            )

    return records


def _validate_columns(df: DataFrame, entity_name: str, fields: List[str]) -> List[Record]:
    invalid_columns: List[str] = [column for column in df.columns if column not in fields]
    if invalid_columns:
        record = Record(
            entity=entity_name,
            description=f"The following columns in your input file are unrecognized: {invalid_columns}",
        )
        return [record]
    return []


def _validate_required_fields(df: DataFrame, entity_name: str, fields: List[str]) -> List[Record]:
    records: List[Record] = []

    missing_required_columns: List[str] = [field for field in fields if field not in df.columns]
    if missing_required_columns:
        record = Record(
            entity=entity_name,
            description=f"The following columns are required, but missing in the input file: {missing_required_columns}",
        )
        records += [record]

    required_df: DataFrame = df[[column for column in df.columns if column in fields]]
    null_required_columns: List[str] = [
        column for column in required_df.columns if required_df[column].isnull().any()
    ]
    for column in null_required_columns:
        record = Record(
            entity=entity_name,
            description=f"The following required column was found to have null values: ['{column}']",
            sample_data=required_df[required_df[column].isna()].head(5),
        )
        records += [record]

    return records


def _validate_duplicate_primary_keys(df: DataFrame, entity_name: str, primary_keys: List[str]) -> List[Record]:
    if len([key for key in primary_keys if key in df.columns]) != len(primary_keys):
        return []

    duplicates_df: DataFrame = df[df.duplicated(subset=primary_keys, keep=False)].sort_values(
        primary_keys
    )
    if duplicates_df.shape[0] > 0:
        record = Record(
            entity=entity_name,
            description=f"Input file has duplicate rows with the same primary key(s): {primary_keys}",
            sample_data=duplicates_df.head(5),
        )
        return [record]
    return []


def _validate_type_casting(df: DataFrame, entity: Entity) -> List[Record]:
    records: List[Record] = []

    for field in [field for field in entity.fields if field.name in df.columns]:
        if field.type == EntityFieldType.int or field.name == EntityFieldType.double:
            invalid_df = df[pd.to_numeric(df[field.name], errors="coerce").isna()]
            if invalid_df.shape[0] > 0:
                records.append(
                    Record(
                        status=Status.WARNING,
                        entity=entity.displayName,
                        description=f"Field '{field.name}' has values that do not typecast to a number",
                        sample_data=invalid_df.head(5),
                    )
                )
        if field.type == EntityFieldType.timestamp:
            sample_df = df[
                (~df[field.name].isna())
                & (~df[field.name].astype(str).str.contains("9999-12-31"))
                & (~df[field.name].astype(str).str.contains("1900-01-01"))
            ].head(100)
            import warnings

            warnings.simplefilter(action="ignore")
            invalid_df = sample_df[pd.to_datetime(sample_df[field.name], errors="coerce").isna()]
            if invalid_df.shape[0] > 0:
                records.append(
                    Record(
                        status=Status.WARNING,
                        entity=entity.displayName,
                        description=f"Field '{field.name}' has values that do not typecast to a date",
                        sample_data=invalid_df.head(5),
                    )
                )

    return records


def _is_required(target_features: List[Feature], required_for_features: List[Feature]) -> bool:
    return len([feature for feature in target_features if feature in required_for_features]) > 0
