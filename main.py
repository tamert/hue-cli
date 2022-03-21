from phue import Bridge
from tabulate import tabulate
import click
from colorama import Fore
import math


def get_range_number(percent, min_vol, max_vol):
    total = math.ceil(min_vol + (percent / 100) * (max_vol - min_vol))
    return int(total)


def connect():
    selected = Bridge()
    if selected.connect():
        api = selected.get_api()
        items = []
        for light in api['lights']:
            item = api['lights'][light]
            items.append([light, item["name"], item["state"]['on']])
        print(tabulate(items, headers=['Id', 'Name', 'Status']))
    return selected


@click.group()
def cli():
    pass


@cli.command()
@click.option('--no', '-n', prompt='Open Light?',
              help='Closed of the light to be opened')
def open(no):
    print(bridge.set_light(int(no), 'on', True))


@cli.command()
@click.option('--no', '-n', prompt='Close Light?',
              help='Opened of the light to be closed')
def close(no):
    print(bridge.set_light(int(no), 'on', False))


@cli.command()
@click.option('--no', '-n', prompt='Which Light?',
              help='Opened of the light to be alarm')
def alarm(no):
    print(bridge.alarm(int(no)))


@cli.command()
@click.option('--no', '-n', help='Opened of the light to be alarm')
def status(no):
    print(bridge.get_light(int(no)))


@cli.command()
@click.option('--no', '-n', prompt='Which Light?',
              help='Write the Light ID')
@click.option('--volume', '-v', help='Write 0-100 range of the number')
def bri(no, volume):
    if isinstance(volume, str) and int(volume) in range(0, 100):
        print(bridge.set_light(int(no), 'bri', get_range_number(int(volume), 0, 254)))
    else:
        print(bridge.set_light(int(no), 'bri', 254))


if __name__ == '__main__':
    click.echo(Fore.LIGHTGREEN_EX + """
     __    __   __    __   _______ 
    |  |  |  | |  |  |  | |   ____|
    |  |__|  | |  |  |  | |  |__   
    |   __   | |  |  |  | |   __|  
    |  |  |  | |  `--'  | |  |____ 
    |__|  |__|  \______/  |_______|
    HUE CONTROL       Tamer Agaoglu
       """ + Fore.RESET)
    bridge = connect()
    cli()
