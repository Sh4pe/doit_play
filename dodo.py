import re
import os
import subprocess
from datetime import datetime

# Map of image_name to Dockerfile path
IMAGES = {'dummy_base': 'docker/base', 
          'dummy_derived': 'docker/derived', 
          'dummy_derived2': 'docker/derived2'}

def get_base_image(dockerfile):
    """Get the base image from a Dockerfile"""
    with open(dockerfile) as f:
        for line in map(lambda x: x.strip(), f):
            match = re.compile('^FROM +([^ ]+)$').match(line)
            if match:
                return match[1]
    raise Exception("{} has no base image".format(dockerfile))

#datetime.datetime.fromtimestamp(os.path.getmtime('/tmp/doit/dodo.py'))

def get_image_creation_datetime(image_name):
    output = subprocess.check_output(['docker', 'inspect', image_name, '-f', '{{.Created}}']).decode('UTF-8').split('.')[0]
    return datetime.strptime(output, '%Y-%m-%dT%H:%M:%S')

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
        print("has_known_base_image({}) = {}".format(dockerfile, has_known_base_image(dockerfile)))
        if not has_known_base_image(dockerfile):
            # In case the base image is not defined by us, we `docker build` it every time. Docker will only rebuild
            # the layers that are not cached in this case
            task_desc['uptodate'] = [False]
            yield task_desc
        else:
            # Otherwise, we rebuild the ...
            base_image = get_base_image(dockerfile)
            task_desc['uptodate'] = [image_newer_than_file(dockerfile, base_image)]
            task_desc['task_dep'] = ['build_image:{}'.format(base_image)]
            yield task_desc

