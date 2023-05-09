from mytml.processor import Processor


a = Processor(
    project_id="sample-project-id",
    source=open("mytml/data/aws-with-tz-and-vpc.vsdx", "r"),
    mappings=[open("mytml/data/iriusrisk-visio-aws-mapping.yaml", "r").read()],
)

otm = a.process()

print(otm.json())
