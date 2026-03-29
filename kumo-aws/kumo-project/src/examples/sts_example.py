"""STS assume-role example using Kumo."""

import json

from dotenv import load_dotenv

from ..kumo_compat import KumoSession

load_dotenv()

session = KumoSession()


def assume_role():
    """Demonstrate assuming an IAM role using STS."""
    sts = session.client("sts")
    iam = session.client("iam")

    # Create a role that trusts the current account
    trust_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {"AWS": "arn:aws:iam::000000000000:root"},
                "Action": "sts:AssumeRole",
            }
        ],
    }

    try:
        # Create the IAM role
        role = iam.create_role(
            RoleName="MLModelRole", AssumeRolePolicyDocument=json.dumps(trust_policy)
        )
        print(f"Created role: {role['Role']['Arn']}")

        # Assume the role
        assumed_role = sts.assume_role(
            RoleArn=role["Role"]["Arn"], RoleSessionName="MLModelSession"
        )

        print("\nAssumed role credentials:")
        print(f"Access Key: {assumed_role['Credentials']['AccessKeyId']}")
        print(f"Secret Key: {assumed_role['Credentials']['SecretAccessKey']}")
        print(f"Session Token: {assumed_role['Credentials']['SessionToken']}")
        print(f"Expiration: {assumed_role['Credentials']['Expiration']}")

        return assumed_role["Credentials"]

    except Exception as e:
        print(f"Error: {str(e)}")
        return None


if __name__ == "__main__":
    credentials = assume_role()
    if credentials:
        print("\nSuccessfully assumed role!")
