# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

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
        entity_name: str = file_path.stem
        if hasattr(data, entity_name):
            print(f"Reading '{file_path}'")
            setattr(data, entity_name, _read_entity(file_path, entity_name, config))
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
