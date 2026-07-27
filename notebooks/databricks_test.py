from databricks.connect import DatabricksSession
spark = DatabricksSession.builder.serverless(True).getOrCreate()
df = spark.range(10)
df.show()
