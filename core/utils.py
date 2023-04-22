import tomli

def read_config():
    f = open("config.toml", "rb")
    return tomli.load(f)