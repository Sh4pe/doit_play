import re
import os
#import subprocess
import docker
from datetime import datetime
from dockerfile_parse import DockerfileParser

# Map of image_name to Dockerfile path
IMAGES = {'dummy_base': 'docker/base', 
          'dummy_derived': 'docker/derived', 
          'dummy_derived2': 'docker/derived2'}

docker_client = docker.from_env()

def get_base_image(dockerfile):
    return DockerfileParser(dockerfile).baseimage

def get_image_creation_datetime(image_name):
    try:
        creation_timestamp = docker_client.images.get(image_name).history()[0]['Created']
    except docker.errors.ImageNotFound:
        creation_timestamp = 0
    return datetime.fromtimestamp(creation_timestamp)

def task_build_image():
    #print(get_base_image('docker/base/Dockerfile'))
    #print(get_base_image('docker/derived/Dockerfile'))
    #print(get_image_creation_datetime('dummy_derived2'))

    def has_known_base_image(dockerfile):
        return get_base_image(dockerfile) in IMAGES

    def image_newer_than_file(dockerfile, dockerimage):
        file_mtime = datetime.fromtimestamp(os.path.getmtime(dockerfile))
        image_ctime = get_image_creation_datetime(dockerimage)
        return file_mtime > image_ctime

    for image_name, dockerfile_path in IMAGES.items():
        dockerfile = '{}/Dockerfile'.format(dockerfile_path)
        task_desc = {
            'name': image_name,
            'verbosity': 2,
            'actions': ["docker build -t {} ./{}".format(image_name, dockerfile_path)],
        }
        base_image = get_base_image(dockerfile)
        print("has_known_base_image({}) [{}] = {}".format(dockerfile, base_image, has_known_base_image(dockerfile)))
        if not has_known_base_image(dockerfile):
            # In case the base image is not defined by us, we `docker build` it every time. Docker will only rebuild
            # the layers that are not cached in this case
            task_desc['uptodate'] = [False]
            yield task_desc
        else:
            # Otherwise, we rebuild the ...
            task_desc['uptodate'] = [image_newer_than_file(dockerfile, base_image)]
            task_desc['task_dep'] = ['build_image:{}'.format(base_image)]
            yield task_desc

