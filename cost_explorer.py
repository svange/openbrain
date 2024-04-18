import os

import boto3

os.environ["AWS_PROFILE"] = "personal"

def list_ec2_resources():
    ec2 = boto3.resource('ec2')

    print("Listing EC2 Instances:")
    for instance in ec2.instances.all():
        print(instance.id, instance.state, instance.instance_type)

    print("\nListing EBS Snapshots:")
    ec2_client = boto3.client('ec2')
    snapshots = ec2_client.describe_snapshots(OwnerIds=['self'])
    for snapshot in snapshots['Snapshots']:
        print(snapshot['SnapshotId'], snapshot['VolumeId'], snapshot['VolumeSize'])

    print("\nListing Elastic IPs:")
    elastic_ips = ec2_client.describe_addresses()
    for eip in elastic_ips['Addresses']:
        print(eip['PublicIp'], eip.get('InstanceId', 'Unassociated'))

if __name__ == "__main__":
    list_ec2_resources()
