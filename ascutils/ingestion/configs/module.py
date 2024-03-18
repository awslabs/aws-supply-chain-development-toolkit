# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import json
import os
from enum import Enum
from typing import List

from pydantic import BaseModel


class Feature(Enum):
    DEMAND_PLANNING_FORECAST = "Demand Planning - Forecast"
    DEMAND_PLANNING_PRODUCT_LINEAGE = "Demand Planning - Product Lineage"
    DEMAND_PLANNING_SUPPLEMENTARY_TIME_SERIES = "Demand Planning - Supplementary Time Series"
    INSIGHTS_INVENTORY_VISIBILITY = "Insights - Inventory Visibility"
    INSIGHTS_NETWORK_MAP = "Insights - Network Map"
    INSIGHTS_INVENTORY_INSIGHTS = "Insights - Inventory Insights"
    INSIGHTS_REBALANCE_RECOMMENDATIONS = "Insights - Rebalance Recommendations"
    INSIGHTS_LEAD_TIME_INSIGHTS = "Insights - Lead Time Insights"


class FieldRequirement(BaseModel):
    name: str
    requiredFor: List[Feature]


class EntityRequirement(BaseModel):
    name: str
    requiredFor: List[Feature]
    fields: List[FieldRequirement]


class Module(BaseModel):
    module_name: str
    entities: List[EntityRequirement]


def get_all_modules() -> List[Module]:
    output: List[Module] = []

    for root, dirs, file_names in os.walk("."):
        for file_name in file_names:
            if "resources/configs/modules" in root and ".json" in file_name:
                full_path = f"{root}/{file_name}"
                with open(full_path) as file:
                    output.append(Module(**json.load(file)))

    return output
