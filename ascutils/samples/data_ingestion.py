# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import os
import pandas as pd
from datetime import datetime

from ascutils import DataUploader, Feature, from_path, validate

print(r"""
      __          _______      _____                   _            _____ _           _
     /\ \        / / ____|    / ____|                 | |          / ____| |         (_)
    /  \ \  /\  / / (___     | (___  _   _ _ __  _ __ | |_   _    | |    | |__   __ _ _ _ __
   / /\ \ \/  \/ / \___ \     \___ \| | | | '_ \| '_ \| | | | |   | |    | '_ \ / _` | | '_ \
  / ____ \  /\  /  ____) |    ____) | |_| | |_) | |_) | | |_| |   | |____| | | | (_| | | | | |
 /_/    \_\/  \/  |_____/    |_____/ \__,_| .__/| .__/|_|\__, |    \_____|_| |_|\__,_|_|_| |_|
                                          | |   | |       __/ |
                                          |_|   |_|      |___/

                                     Development Toolkit

Using this script, you will be able to run validate sanity checks and to upload your data. 
Before running this script, ensure you have read the README and completed the prerequisites.

""")

# Input data location
data_path = input("Enter the path where your data files are stored: ") or "."

# Load the data
data = from_path(data_path)

# Select features for validation
feature_choices = [
    "Insights: Inventory Visibility",
    "Insights: Network Map",
    "Insights: Inventory Insights",
    "Insights: Rebalance Recommendations",
    "Insights: Lead Time Insights",
    "Demand Planning: Forecast",
    "Demand Planning: Product Lineage",
    "Demand Planning: Supplementary Time Series",
]

print("\nSelect features to use for validation:")
for idx, feature in enumerate(feature_choices, start=1):
    print(f"{idx}. {feature}")

requested_features = input("Enter comma-separated indices or type 'all' to select all features: ")
if requested_features == 'all':
    features = [feature for feature in Feature]
else:
    selected_indices = requested_features.split(",")
    features = [Feature[feature_choices[int(index) - 1].replace(': ', '_').replace(' ', '_').upper()] for index in selected_indices if index.isdigit()]

# Validate data
if features:
    print("Starting validation (this may take a few minutes)...")
    records = validate(data, features)
    if records:
        print("\nValidation Report:\n")
        for record in records:
            record.sample_data = record.sample_data.to_json(orient="records") if record.sample_data is not None else None
            print(f"[{record.status.value}] {record.entity}: {record.description}")
        now = datetime.now().strftime("%Y-%m-%d-%H:%M:%S")
        validation_report_file_name = f"asc-entity-validation-{now}.csv"
        pd.DataFrame(records).to_csv(validation_report_file_name, index=False)
        print(f"\nThe full validation report has been written to '{validation_report_file_name}'")

# Ask whether to upload data
upload = input("\nDo you want to upload the data to your ASC instance? (yes/no): ").lower() == 'yes'

if upload:
    instance_id = input("Enter your ASC instance ID: ")
    uploaded_files_folder = DataUploader().default_flow_uploads(data=data, instance_id=instance_id, output_data=True)
    print(f"\nNote: If this is your first time using this script navigate to the web-app and go through the ingestion setup process. When asked to upload your data, drag and drop the following folder that was generated in your working directory (all following ingestions do not require this step): {os.getcwd()}/{uploaded_files_folder}")

print("\nFlow ingestion quick start script completed.")
