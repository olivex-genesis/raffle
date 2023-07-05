from utils.raffle import Raffle
import numpy as np

EVENT_NAME = 'Styx-Event-01'
EVENT_SEED = 2023

# Mapmaker
EVENT_PRIZES_MAPMAKER = 30

EVENT_PRIZES_FOR_NON_HOLDER_ROLES = {
    'optimist': {
        'prizes': 'Common',
        'amount': 38
    },
    'haruspex': {
        'prizes': 'SerpentKey',
        'amount': 40
    },
    'seeker': {
        'prizes': 'Common',
        'amount': 25
    },
    'paragon': {
        'prizes': 'Silver',
        'amount': 15
    },
    'herald': {
        'prizes': 'GoldenApple',
        'amount': 6
    },
    'monster': {
        'prizes': 'Silver',
        'amount': 8
    },
    'keeper': {
        'prizes': 'Gold',
        'amount': 7
    },
    'coward': {
        'prizes': 'Gold',
        'amount': 7
    },
    'kindly one': {
        'prizes': 'Genesis',
        'amount': 1
    }
}

rng = np.random.default_rng(seed=EVENT_SEED)

mapmaker_raw = Raffle.get_data('data/Styx-Event/mapmaker.json')
non_holders_raw = Raffle.get_data('data/Styx-Event/non-holders.json')

event_participants_mapmaker = [row['wallet_id'].lower() for row in mapmaker_raw]

if len(mapmaker_raw) != len(list(set(event_participants_mapmaker))):
    raise Exception('duplicated wallet found')

rng.shuffle(event_participants_mapmaker)
print('mapmaker participants ', len(event_participants_mapmaker))

mapmaker_winners = rng.choice(event_participants_mapmaker, size=EVENT_PRIZES_MAPMAKER, replace=False)

result_name = EVENT_NAME + "-Mapmaker"
Raffle.write_result(result_name, {'Winner': mapmaker_winners}, 'results/{}.md'.format(result_name))

print('\n----------------------\n')

all_non_holders = []
event_participants_in_roles = {}

for row in non_holders_raw:
    if row['role'] not in event_participants_in_roles:
        event_participants_in_roles[row['role']] = []
    event_participants_in_roles[row['role']].append(row['wallet_id'])
    all_non_holders.append(row['wallet_id'])

if len(non_holders_raw) != len(set(all_non_holders)):
    raise Exception('duplicated wallet found')

print('total non holder ', len(all_non_holders))

for role, prizes in EVENT_PRIZES_FOR_NON_HOLDER_ROLES.items():
    event_participants = event_participants_in_roles[role]
    rng.shuffle(event_participants)
    print('{} participants {}'.format(role, len(event_participants)))
    winners = rng.choice(event_participants, size=prizes['amount'], replace=False)
    result_name = EVENT_NAME + "-" + role.title().replace(' ', '')
    Raffle.write_result(result_name, {'Winner': winners}, 'results/{}.md'.format(result_name))
