from aws_cdk import core as cdk

import aws_cdk.aws_ec2 as ec2
import aws_cdk.aws_elasticsearch as es
import aws_cdk.aws_msk as msk


class SearchieStack(cdk.Stack):
    def __init__(self, scope: cdk.Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.vpc = ec2.Vpc.from_lookup(
            self, "SharedVPC", vpc_id="vpc-0051b8b7bdff9a7d0"
        )
        # self.elastic_search()
        # self.kafka()

    def kafka(self):
        isolated_subnets = ec2.SubnetSelection(subnet_type=ec2.SubnetType.ISOLATED)
        instance_type = ec2.InstanceType.of(
            ec2.InstanceClass.BURSTABLE3, ec2.InstanceSize.SMALL
        )
        cluster = msk.Cluster(
            self,
            "SearchieKafkaCluster",
            cluster_name="SearchieCluster",
            instance_type=instance_type,
            kafka_version=msk.KafkaVersion.V2_6_1,
            vpc=self.vpc,
            vpc_subnets=isolated_subnets,
        )
        return cluster

    def elastic_search(self):
        default_instance_type = "t3.small.elasticsearch"
        default_data_type = default_instance_type
        default_master_type = default_instance_type

        instances = es.CapacityConfig(
            data_node_instance_type=default_data_type,
            data_nodes=1,
            master_node_instance_type=default_master_type,
            master_nodes=None,
        )

        storage = es.EbsOptions(
            enabled=True,
            iops=None,
            volume_size=100,
            volume_type=ec2.EbsDeviceVolumeType.GP2,
        )

        es_domain = es.Domain(
            self,
            "SearchieElasticDomain",
            version=es.ElasticsearchVersion.V7_1,
            capacity=instances,
            ebs=storage,
        )

        return es_domain
