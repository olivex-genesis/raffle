import json
from utils.raffle import RaffleEvent
from utils.raffle import Raffle

# prepare data
opt_out_list = Raffle.get_data('data/Moca-Raffle/opt_out_list.json')
eligible_token = list([key for key, value in Raffle.get_data('data/Moca-Raffle/eligible_list.json')['allRevealed'].items() if value == '1'])
snapshot = Raffle.get_data('data/Moca-Raffle/snapshot_1.json')

# same as onchain raffle name
EVENT_NAME = 'Moca-Giveaway-01'
EVENT_PLACES = 5
# update after onchain random seed raffle
EVENT_SEED = 5458442556912548267338026275094451493338016430765720025401280646515453231041
# following isn't token id
EVENT_PRIZES = ['#2300', '#2304', '#2306', '#2310', '#2320']

raffle = RaffleEvent(EVENT_NAME, EVENT_PLACES, EVENT_SEED)

print('seed use', raffle.get_random_seed())

# calculate weight & participants
all_owners = snapshot['owners']
participants = [user for user in list(all_owners.keys()) if user not in opt_out_list]

user_entries = []
event_participants = []

for participant in participants:
    wishes = all_owners[participant]['wishes']
    pages = sum([token['earned'] for token in all_owners[participant]['token_details'] if token['token_id'] in eligible_token])
    eligible_hold = [token['token_id'] for token in all_owners[participant]['token_details'] if token['token_id'] in eligible_token]

    entries = pages + wishes * 3
    # only user hold at least one eligible token can join raffle
    if len(eligible_hold) > 0:
        event_participants.append(participant)
        user_entries.append(entries)


total = sum(user_entries)

print('all entries ', total)
print('event participants ', len(event_participants))
print('event places ', EVENT_PLACES)

if len(event_participants) < EVENT_PLACES:
    raise Exception("participants ({}) must greater than event places ({})".format(len(event_participants), EVENT_PLACES))

weights = [count / total for count in user_entries]
winners = raffle.get_raffle_result(event_participants, weights)

raffle.export_result({'Winners': winners, 'Prize': EVENT_PRIZES}, './results/')
with open('results/{}.json'.format(EVENT_NAME), 'w+') as fp:
    json.dump(winners.tolist(), fp)