import json
import pandas as pd
from dataclasses import dataclass
import numpy as np

EVENT_NAME = 'OliveX-SandBox-01'
SEED = 2002

genesis_address = '0xe77694cb06e66c6f33413052c07599173e356d71'
ape_address = '0x3b2f1189b9372c4b6c569a497ad241112d8824c1'
ga_address = '0x92bce4a82f1407c711b889e34fe8cb9b49f02217'


@dataclass
class NftBalance:
    genesis_weight = 3
    ape_weight = 1
    ga_weight = 1

    def __init__(self, genesis: int = 0, ape: int = 0, ga: int = 0):
        self.genesis = genesis
        self.ape = ape
        self.ga = ga

    def get_all_balance(self):
        return self.genesis + self.ape + self.ga

    def dict(self):
        return {'genesis': self.genesis, 'ape': self.ape, 'ga': self.ga}

    def add(self, genesis, ape, ga):
        self.genesis = self.genesis + genesis
        self.ape = self.ape + ape
        self.ga = self.ga + ga

    # 2: Guaranteed, 1: Chance, 0: N/A
    def rewards(self):
        is_holder = self.get_all_balance()
        return {
            'SandboxAsset': 2 if is_holder > 0 else 0,
            'ResourceBundle': 2 if is_holder > 0 else 0,
            'Floppy': 2 if self.genesis > 0 else 0,
            'ApeCoin': 2 if self.genesis > 0 else (1 if self.ape > 0 else 0),
            'Dose': 2 if self.ga > 0 or self.genesis > 0 else 0,
            'GeneralLandRaffle': 1 if is_holder > 0 else 0,
            'GenesisLandRaffle': 1 if self.genesis > 0 else 0,
        }

    def get_general_raffle_weight(self):
        return self.genesis * self.genesis_weight + self.ga * self.ga_weight + self.ape * self.ape_weight

    def get_ape_coin_weight(self):
        return self.genesis * self.genesis_weight + self.ape * self.ape_weight

    def get_dose_weight(self):
        return self.genesis * self.genesis_weight + self.ga * self.ga_weight


def get_balance(path):
    records = pd.read_csv(path, index_col=False)
    balance = {record['HolderAddress'].lower(): record['Quantity'] for index, record in records.iterrows()}
    return balance


def write_result(event_name, results, file_path):
    table = pd.DataFrame(results)
    with open(file_path, "w") as f:
        comment = """# {}\n\n## Congratulations to the winners.\n\n""".format(event_name) + \
                  table.to_markdown() + "\n"
        f.write(comment)


genesis_holder_balance = get_balance('data/Sandbox-Event/export-tokenholders-for-nft-contract-0xe77694cb06e66c6f33413052c07599173e356d71.csv')
ape_holder_balance = get_balance('data/Sandbox-Event/export-tokenholders-for-nft-contract-0x3b2f1189b9372c4b6c569a497ad241112d8824c1.csv')
ga_holder_balance = get_balance('data/Sandbox-Event/export-tokenholders-for-nft-contract-0x92bce4a82f1407c711b889e34fe8cb9b49f02217.csv')


def get_overall_balance(wallet_address):
    return NftBalance(genesis_holder_balance.get(wallet_address, 0), ape_holder_balance.get(wallet_address, 0), ga_holder_balance.get(wallet_address, 0))


IGNORE_IN_PLAYER = {
    # used both reward & staking wallet
    '0x078941339627549c28680587806c6aec6a60c5cf': True,
}

IGNORE_IN_CROSS_WALLET = {
    # two wallet point to same genesis wallet
    '0x22f1cd8dc14a0074d4d104844f508cab82254dc9': True,
    '0xd79835f7ca928826aa5e76fe9070cf8ca8d47bf4': True,
    '0x2378d669b209a7c7af82388e30ef6cdec5b167bf': True
}

SPECIAL_COMBINE_WALLET = {
    '0x61e3cef3bc04e141ea2a03a62cd9293d16c82344': '0x2d5e62c8fb5a0f7832f38bec184ceb9caab4aaf5'
}

# read sb players
all_players = {}
with open('data/Sandbox-Event/sb_quest_records.json') as fp:
    with open('data/Sandbox-Event/sb_quest_additional_records.json') as f:
        user_records = json.load(fp)
        all_players = {record['UserWallet'].lower(): record for record in user_records}
        additional_records = json.load(f)
        additional_players = {record['UserWallet'].lower(): record for record in additional_records}
        for wallet, record in additional_players.items():
            if wallet not in all_players:
                all_players[wallet] = record
print('all players ', len(all_players))

all_holders = {}
# first check all players who are holder
for player in all_players:
    if player in IGNORE_IN_PLAYER:
        continue
    nft_balance = get_overall_balance(player)
    if nft_balance.get_all_balance() > 0:
        all_holders[player] = nft_balance

# cross wallet
# reward wallet -> staking wallet, also in player list
reward_to_genesis_wallet_pair = {}

with open('data/Sandbox-Event/genesis_reward_wallet_pairs.json') as fp:
    with open('data/Sandbox-Event/genesis_sb_cross_wallet.json') as f:
        snapshot = json.load(fp)
        # in case genesis holder use reward wallet to play
        for staking, reward_wallet in snapshot.items():
            if staking == reward_wallet:
                continue
            if reward_wallet not in all_players:
                # ignore
                continue
            if reward_wallet in IGNORE_IN_CROSS_WALLET:
                continue
            reward_to_genesis_wallet_pair[reward_wallet] = staking

        cross_wallet_records = json.load(f)
        for record in cross_wallet_records:
            sb_wallet = record['SandboxWallet'].lower()
            genesis_wallet = record['GenesisWallet'].lower()
            if sb_wallet == genesis_wallet:
                continue
            if sb_wallet not in all_players:
                continue
            if sb_wallet in IGNORE_IN_CROSS_WALLET:
                continue
            if sb_wallet in reward_to_genesis_wallet_pair:
                if genesis_wallet == reward_to_genesis_wallet_pair[sb_wallet]:
                    # duplicated application
                    continue
                else:
                    raise Exception('override')
            else:
                reward_to_genesis_wallet_pair[sb_wallet] = genesis_wallet

        # supposed all wallets are unique
        unique_wallet = {}
        for key, value in reward_to_genesis_wallet_pair.items():
            if key not in unique_wallet:
                unique_wallet[key] = True
            else:
                print(key, ' ', value)
            if value not in unique_wallet:
                unique_wallet[value] = True
            else:
                print(key, ' ', value)
        if len(unique_wallet) != len(reward_to_genesis_wallet_pair) * 2:
            raise Exception('not all wallet is unique')

# add to holder list
for game_wallet, genesis_wallet in reward_to_genesis_wallet_pair.items():
    if game_wallet in all_holders:
        raise Exception('already counted ', game_wallet)
    if genesis_wallet in all_holders:
        raise Exception('already counted ', genesis_wallet)

    nft_balance = get_overall_balance(genesis_wallet)
    if nft_balance.get_all_balance() > 0:
        all_holders[game_wallet] = nft_balance

# combine nft balance
for game_wallet, nft_wallet in SPECIAL_COMBINE_WALLET.items():
    if game_wallet in all_holders and nft_wallet not in all_holders:
        nft_balance = get_overall_balance(nft_wallet)
        if nft_balance.get_all_balance() > 0:
            all_holders[game_wallet].add(nft_balance.genesis, nft_balance.ape, nft_balance.ga)

print('all holders ', len(all_holders))
print('===================')


def save_holders():
    wallet_addresses = []
    genesis_balance_list = []
    ga_balance_list = []
    ape_balance_list = []
    genesis_wallet_list = []

    for address, balances in all_holders.items():
        wallet_addresses.append(address)
        genesis_balance_list.append(balances.genesis)
        ga_balance_list.append(balances.ga)
        ape_balance_list.append(balances.ape)
        if address in reward_to_genesis_wallet_pair:
            genesis_wallet_list.append(reward_to_genesis_wallet_pair[address])
        else:
            genesis_wallet_list.append('NA')

    data = {
        'Wallet': wallet_addresses,
        'GenesisCount': genesis_balance_list,
        'GACount': ga_balance_list,
        'ApePassCount': ape_balance_list,
        'GenesisWallet': genesis_wallet_list
    }

    df = pd.DataFrame(data)
    df.to_csv('tem/sb_event_nft_holders.csv', index=False)


save_holders()

# generate random result
rng = np.random.default_rng(seed=SEED)

all_participants = {holder: balance.rewards() for holder, balance in all_holders.items()}


def get_raffle_result(participant_with_weight, prize_amount):
    len(participant_with_weight)
    total_weight = sum(participant_with_weight.values())
    results = rng.choice(list(participant_with_weight.keys()), p=[w / total_weight for w in participant_with_weight.values()], size=prize_amount, replace=False)
    return results


# sandbox asset
sandbox_asset_result = [participant for participant, reward in all_participants.items() if reward['SandboxAsset'] == 2]

# dustland nft
bundle_reward_for_general = ['Small', 'Medium', 'Large']
bundle_reward_amount_for_general = [125, 69, 35]
bundle_reward_for_genesis = 'Large'
bundle_reward_material_type = ['Chipz', 'Plastic Straws', 'Torn Cloth', 'Rubber Fragments', 'Metal Scraps', 'Wood']

each_bundle_count = int(len(all_participants) / len(bundle_reward_material_type))
reminder = len(all_participants) - each_bundle_count * len(bundle_reward_material_type)

# list for reward
material_list = []
for m in range(len(bundle_reward_material_type)):
    material_list.extend([m] * each_bundle_count)

material_list.extend([len(bundle_reward_material_type)-1] * reminder)
rng.shuffle(material_list)

bundle_reward_rarity_result = {}
bundle_reward_result = {}

general_participants = {participant: balance.get_general_raffle_weight() for participant, balance in all_holders.items() if balance.genesis == 0}
genesis_participants = {participant: balance.get_general_raffle_weight() for participant, balance in all_holders.items() if balance.genesis > 0}


for index in reversed(range(len(bundle_reward_amount_for_general))):
    winners = get_raffle_result(general_participants, bundle_reward_amount_for_general[index])
    for winner in winners:
        bundle_reward_rarity_result[winner] = bundle_reward_for_general[index]
        general_participants.pop(winner)

for participant in genesis_participants:
    bundle_reward_rarity_result[participant] = bundle_reward_for_genesis

type_count = 0
for participant, reward in bundle_reward_rarity_result.items():
    bundle_reward_result[participant] = '{} ({})'.format(bundle_reward_material_type[material_list[type_count]], reward)
    type_count = type_count + 1

print('bundle reward participants ', len(all_holders))
print('bundle_reward ', len(bundle_reward_result))
print('===================')

# from uncommon to legendary
floppy_reward_for_genesis = [53, 31, 23, 1]
floppy_reward_name_for_genesis = ['2x Uncommon', 'Rare', 'Epic', 'Legendary']

floppy_reward_result = {}
floppy_reward_participants = {participant: all_holders[participant].genesis for participant, reward in all_participants.items() if reward['Floppy'] == 2}
print('floppy_reward_participants', len(floppy_reward_participants))

for index in reversed(range(len(floppy_reward_for_genesis))):
    winners = get_raffle_result(floppy_reward_participants, floppy_reward_for_genesis[index])
    for winner in winners:
        floppy_reward_result[winner] = floppy_reward_name_for_genesis[index]
        floppy_reward_participants.pop(winner)

print('floppy_reward ', len(floppy_reward_result))
print('===================')

# dose & ape coin reward
ape_reward = [228, 35, 15, 9, 3, 1]
dose_reward = [101, 45, 26, 10, 3, 1]

ape_reward_amount = ['$5', '$10', '$25', '$50', '$100', '$500']
dose_reward_amount = ['$5', '$10', '$25', '$50', '$100', '$500']

# ApeCoin Raffle
ape_reward_result = {}
ape_reward_participants = {participant: all_holders[participant].get_ape_coin_weight() for participant, reward in all_participants.items() if reward['ApeCoin'] == 2 or reward['ApeCoin'] == 1}
print('ape_reward_participants ', len(ape_reward_participants))

for index in reversed(range(len(ape_reward))):
    winners = get_raffle_result(ape_reward_participants, ape_reward[index])
    for winner in winners:
        ape_reward_result[winner] = ape_reward_amount[index]
        ape_reward_participants.pop(winner)

print('ape_reward ', len(ape_reward_result))
print('===================')

# Dose Raffle
dose_reward_result = {}
dose_reward_participants = {participant: all_holders[participant].get_dose_weight() for participant, reward in all_participants.items() if reward['Dose'] == 2}
print('dose_reward_participants ', len(dose_reward_participants))

for index in reversed(range(len(dose_reward))):
    winners = get_raffle_result(dose_reward_participants, dose_reward[index])
    for winner in winners:
        dose_reward_result[winner] = dose_reward_amount[index]
        dose_reward_participants.pop(winner)

print('dose_reward ', len(dose_reward_result))
print('===================')

# Land Raffle
land_raffle_general_reward = 5
land_raffle_genesis_reward = 30

# general land raffle
land_raffle_general_participants = {participant: all_holders[participant].get_general_raffle_weight() for participant, reward in all_participants.items() if reward['GeneralLandRaffle'] == 1}
land_raffle_general_result = get_raffle_result(land_raffle_general_participants, land_raffle_general_reward)

print('land_raffle_general_participants ', len(land_raffle_general_participants))
print('land_raffle_general ', len(land_raffle_general_result))
print('===================')

land_raffle_genesis_participants = {participant: all_holders[participant].genesis for participant, reward in all_participants.items() if reward['GenesisLandRaffle'] == 1}
land_raffle_genesis_result = get_raffle_result(land_raffle_genesis_participants, land_raffle_genesis_reward)

print('land_raffle_genesis_participants ', len(land_raffle_genesis_participants))
print('land_raffle_genesis ', len(land_raffle_genesis_result))
print('===================')

holders = []
genesis_balances = []
ape_pass_balances = []
ga_balances = []
sb_asset_prizes = []
dustland_bundle_prizes = []
dustland_floppy_prizes = []
dose_prizes = []
ape_prizes = []
land_prizes_5 = []
land_prizes_30 = []

for holder in all_holders.keys():
    holders.append(holder)
    genesis_balances.append(all_holders[holder].genesis)
    ape_pass_balances.append(all_holders[holder].ape)
    ga_balances.append(all_holders[holder].ga)
    # SB asset
    sb_asset_prizes.append('Yes' if holder in sandbox_asset_result else 'No')
    # Dustland NFT
    dustland_bundle_prizes.append(bundle_reward_result[holder] if holder in bundle_reward_result else 'NA')
    dustland_floppy_prizes.append(floppy_reward_result[holder] if holder in floppy_reward_result else 'NA')
    # Dose
    dose_prizes.append(dose_reward_result[holder] if holder in dose_reward_result else 'NA')
    # Ape
    ape_prizes.append(ape_reward_result[holder] if holder in ape_reward_result else 'NA')
    # 5 Land Raffle
    land_prizes_5.append('Yes' if holder in land_raffle_general_result else 'No')
    # 30 Land Raffle
    land_prizes_30.append('Yes' if holder in land_raffle_genesis_result else 'No')

data = {
    'WalletAddress': holders,
    'GenesisCount': genesis_balances,
    'ApePassCount': ape_pass_balances,
    'GACount': ga_balances,
    'SandboxAsset': sb_asset_prizes,
    'DustlandBundle': dustland_bundle_prizes,
    'DustlandFloppy': dustland_floppy_prizes,
    'Dose': dose_prizes,
    'ApeCoin': ape_prizes,
    '5 Land Raffle': land_prizes_5,
    '30 Land Raffle': land_prizes_30
}

df = pd.DataFrame(data)
df.to_csv('results/{}.csv'.format(EVENT_NAME), index=False)