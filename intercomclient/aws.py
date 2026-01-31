import boto3


class DynamoDBClient:
    def __init__(self, boto3_client):
        self.client = boto3.client("dynamodb")

    def auth_check(self) -> None:
        paginator = self.client.get_paginator("list_tables")
        page_iterator = paginator.paginate(Limit=10)

        # List the tables in the current AWS account
        print("Here are the DynamoDB tables in your account:")

        # Use pagination to list all tables
        table_names = []

        for page in page_iterator:
            for table_name in page.get("TableNames", []):
                print(f"- {table_name}")
                table_names.append(table_name)

        if not table_names:
            print("You don't have any DynamoDB tables in your account.")
        else:
            print(f"\nFound {len(table_names)} tables.")

    def upload_frames(self) -> None:
        pass

    def upload_events(self) -> None:
        pass
