import yaml
import logging
import os

base_dir = os.path.abspath(os.path.dirname(__file__))


def get_config(path):
    try:
        with open(path, encoding="utf8") as f:
            config = yaml.safe_load(f)
        return config
    except FileNotFoundError as e:
        logging.error(e)
        logging.error('Please add a config.yml file, you can refer to config.default.yml')
        exit(0)


config_path = base_dir + '/config.yml'
# 获取配置
config = get_config(config_path)

if __name__ == '__main__':
    print(config['log'])
