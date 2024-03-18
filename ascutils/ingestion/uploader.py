# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import os
from datetime import datetime
from typing import Optional

import boto3

from ascutils.ingestion.configs.entity import get_all_entities
from ascutils.ingestion.data import BaseData


class DataUploader:
    def __init__(self):
        self.s3_client = boto3.client("s3")

    def default_flow_uploads(self, data: BaseData, instance_id: str, output_data: bool = False) -> Optional[str]:
        bucket_name = f"aws-supply-chain-data-{instance_id}"
        output_folder = datetime.now().strftime("data_%Y-%m-%d_%H-%M-%S") if output_data else None

        for entity in get_all_entities():
            df = data.get(entity.displayName)
            if df is not None:
                csv_buffer = df.to_csv(index=False)
                object_key = f"othersources/{entity.displayName.lower().replace('-', '').replace('_', '')}/{entity.displayName}.csv"
                print(f"Uploading '{entity.displayName}' to s3://{bucket_name}/{object_key}")
                self.s3_client.put_object(Bucket=bucket_name, Key=object_key, Body=csv_buffer)

                if output_data:
                    directory_path = f"{output_folder}/othersources/{entity.displayName.lower().replace('-', '').replace('_', '')}"
                    os.makedirs(directory_path, exist_ok=True)
                    df.to_csv(f"{output_folder}/{object_key}", index=False)

        return output_folder
