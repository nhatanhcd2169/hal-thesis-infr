import typing as T
import json
import os

DOCKER_CMD = 'docker compose -f kibana.docker-compose.yml'
TARGET_BIN = 'bin/kibana-keystore'

def json_proc(strs: T.List[str]):
    output = {}
    for text in strs:
        text = text.strip('\n')
        key, val = text.split(': ')
        output[key] = val
    return output

def cmd_(*args):
    return ' '.join(args) + '\n'

with open('./config/kibana/encrypt.txt', 'r') as file:
    output = file.readlines()[-4:-1]
    json_output = json_proc(output)

with open('./config/kibana/encrypt.json', 'w') as file:
    json.dump(json_output, file)

command_text = [
    cmd_("Run Kibana container first"),
    cmd_(DOCKER_CMD, 'up -d'),
    '\n',
    cmd_("Open Kibana terminal"),
    cmd_("docker exec -it kibanana sh"),
    '\n',
    cmd_("Pass these into kibana terminal one by one"),
    '\n',
]

container_commands = [
    cmd_(TARGET_BIN, 'create'),
    *[cmd_(
        'echo', f'"{json_output[key]}"', '|', TARGET_BIN, 'add', '-f', key, ) for key in json_output
    ],
    cmd_('cp config/kibana.keystore temp')
]

container_text = ''.join(container_commands)
with open('./config/kibana/encrypt.sh', 'w') as file:
    file.writelines(container_text)

command_text.append(container_text)

command_text.append(cmd_('exit'))
command_text.append('\n')
command_text.append(cmd_("Stop Kibana container"))
command_text.append(cmd_(DOCKER_CMD, 'down'))
command_text.append('\n')
command_text.append(cmd_("Remove encrypt.json and encrypt.txt"))
command_text.append(cmd_("rm config/kibana/encrypt.* -f"))
command_text.append('\n')
command_text.append(cmd_("Remove this file"))
command_text.append(cmd_("rm keystore-command.txt -f"))
    
# with open('./keystore-command.txt', 'w') as file:
#     file.writelines(command_text)