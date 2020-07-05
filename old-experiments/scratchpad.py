import docker

client = docker.from_env()


client.containers.run('continuumio/miniconda3', detach=True)


container = client.containers.create('continuumio/miniconda3')

client.containers.list()

container.start()

for line in container.logs(stream=True):
    print(line.strip())

res = container.exec_run('conda')
print(res.output.decode('utf-8'))