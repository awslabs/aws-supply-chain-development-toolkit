# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import inspect
import json
import re
from dataclasses import dataclass, make_dataclass, field
from pathlib import Path
from typing import Optional, Dict

import pandas as pd
from pandas import DataFrame
from pydantic import BaseModel, Field

from ascutils.ingestion.configs.entity import get_all_entities


@dataclass
class BaseData:
    def get(self, entity_name: str) -> Optional[DataFrame]:
        try:
            return getattr(self, entity_name)
        except:
            return None

    def entities(self):
        return [
            entity_name
            for entity_name, data_frame in self.__dict__.items()
            if data_frame is not None
        ]


Data = make_dataclass(
    cls_name="Data",
    fields=[
        (it.displayName, type(Optional[DataFrame]), field(default=None))
        for it in get_all_entities()
    ],
    bases=(BaseData,),
)


class ReadConfigOptions(BaseModel):
    delimiter: str = ","
    remove_special_chars: bool = False


class ReadConfig(BaseModel):
    default: ReadConfigOptions = Field(default_factory=ReadConfigOptions)
    entities: Dict[str, ReadConfigOptions] = Field(default_factory=dict)


def from_path(path: str = ".") -> BaseData:
    data = Data()
    config: ReadConfig = _get_read_config(path)

    for file_path in Path(path).glob("*.csv"):
        file_name: str = file_path.stem
        entity_name = _match_entity(file_name)
        if entity_name:
            print(f"Reading '{file_path}'")
            setattr(data, entity_name, _read_entity(file_path, entity_name, config))
    return data


def from_dict(data_dict: Dict[str, DataFrame]) -> BaseData:
    data = Data()

    for entity_name, entity_data in data_dict.items():
        setattr(data, entity_name, entity_data)

    return data


def _read_entity(path: Path, entity_name: str, config: ReadConfig) -> DataFrame:
    options = config.default if entity_name not in config.entities else config.entities[entity_name]

    df = pd.read_csv(path, dtype=str, sep=options.delimiter)
    df.columns = [column.lower() for column in df.columns]

    if options.remove_special_chars:
        df = df.map(
            lambda val: re.sub(r"[^\w\s\-_.!?${}()\[\]/\\@]", "", str(val))
            if not pd.isna(val)
            else None
        )

    return df


def _get_read_config(path: str) -> ReadConfig:
    full_path = f"{path}/config.json"
    try:
        with open(full_path) as file:
            json_str = file.read()
            config_dict = json.loads(json_str)
            config = ReadConfig(**config_dict)
            print(f"Using read configuration from '{full_path}'")
            return config
    except:
        print("Using default read configuration")
        return ReadConfig()


def _match_entity(possible_entity_name: str) -> Optional[str]:
    for actual_entity_name in inspect.getmembers(Data)[0][1].keys():
        if _normalize_entity(actual_entity_name) == _normalize_entity(possible_entity_name):
            return actual_entity_name
    return None


def _normalize_entity(name: str) -> str:
    return re.sub(r"[ \-_]|records", "", name.lower(), flags=re.IGNORECASE)
