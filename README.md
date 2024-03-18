## AWS Supply Chain Development Toolkit

The AWS Supply Chain (ASC) Development Toolkit provides sample tools and scripts to set up your ASC instance.

### 1. Data Ingestion
Setting up your ASC instance requires hydrating the [_data lake_](https://docs.aws.amazon.com/aws-supply-chain/latest/userguide/what-is-service.html) with your data. The ASC data lake is used to aggregate data from your supply chain systems in one place, using an extensible [data model](https://docs.aws.amazon.com/aws-supply-chain/latest/userguide/data-model-asc.html) built for supply chain management. The `data_ingestion.py` is a sample script that can be used to upload data into ASC via S3, as well as providing some basic sanity checks of your the data. To use the script follow these steps:

0. Clone this repo to your local machine and install the required dependencies by executing `pip3 install boto3 pandas pydantic`. Navigate inside the folder by running `cd aws-supply-chain-development-toolkit`
1. Organize your data files in a folder in the same working directory as the location of the `ascutils` folder. Each file should be named following the pattern `<entity_name>.csv`. For example, `product.csv`, `inventory_policy.csv`, etc. The files you will need is defined by which modules and features you would like to use, full documentation is provided [here](https://docs.aws.amazon.com/aws-supply-chain/latest/userguide/data-model.html). 
2. Obtain AWS CLI access keys with permissions to upload data to your ASC S3 bucket and export them in your terminal as such:

```
  export AWS_DEFAULT_REGION='your_default_region_here' # example: 'us-west-2', 'us-east-1', etc
  export AWS_ACCESS_KEY_ID='your_access_key_id_here'
  export AWS_SECRET_ACCESS_KEY='your_secret_access_key_here'
  export AWS_SESSION_TOKEN='your_session_token_here'  # if necessary
```
3. Run the ingestion script by running the following command and follow the instructions:
```
python3 -m ascutils.samples.data_ingestion
```

Optionally, the data ingestion script supports passing in read configuration overrides to address common issues that might cause ingestion failure. To utilize this feature, create a `config.json` file in the same directory as your data files. Example `config.json`:
```
{
    "default": {
        "delimiter": ",",
        "remove_special_chars": true
    }
}
```

## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## License

This project is licensed under the Apache-2.0 License.

