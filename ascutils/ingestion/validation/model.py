# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from dataclasses import dataclass
from enum import Enum
from typing import Optional

from pandas import DataFrame


class Status(Enum):
    ERROR = "ERROR"
    WARNING = "WARNING"


@dataclass
class Record:
    entity: str
    description: str
    sample_data: Optional[DataFrame] = None
    status: Status = Status.ERROR
