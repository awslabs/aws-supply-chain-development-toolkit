# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import json
import os
from enum import Enum
from pathlib import Path
from typing import Dict, List

from pydantic import BaseModel, Field


class EntityFieldType(Enum):
    string = "string"
    int = "int"
    timestamp = "timestamp"
    double = "double"


class EntityField(BaseModel):
    name: str
    type: EntityFieldType
    required: bool
    primaryKey: bool
    description: str
    foreignKey: Dict[str, str] = Field(default_factory=dict)


class Entity(BaseModel):
    name: str
    displayName: str
    description: str
    entityType: str
    category: str
    fields: List[EntityField]


def get_all_entities() -> List[Entity]:
    output: List[Entity] = []

    for root, dirs, file_names in os.walk(Path(__file__).parent.parent.parent):
        for file_name in file_names:
            if "resources/configs/entity" in root and ".json" in file_name:
                full_path = f"{root}/{file_name}"
                with open(full_path) as file:
                    output.append(Entity(**json.load(file)))

    return output
