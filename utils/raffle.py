import json
import numpy as np
from eth_account.messages import encode_structured_data
from web3.auto import w3
import pandas as pd


class Raffle:
    @staticmethod
    def get_data(path):
        with open(path) as fp:
            data = json.load(fp)
            return data

    @staticmethod
    def get_private_key(path):
        with open(path) as fp:
            keys = json.load(fp)
            return keys['private_key']

    """
    sign message with signTypedData_v4
    """

    @staticmethod
    def get_signature(event_name, event_places, event_seed, private_key):
        msg_params = {
            'types': {
                'EIP712Domain': [
                    {
                        'name': 'name',
                        'type': 'string'
                    },
                    {
                        'name': 'version',
                        'type': 'string'
                    }
                ],
                'Raffle': [
                    {
                        'name': 'eventName',
                        'type': 'string'
                    },
                    {
                        'name': 'winningPlaces',
                        'type': 'uint256'
                    },
                    {
                        'name': 'seed',
                        'type': 'uint256'
                    }
                ]
            },
            'primaryType': 'Raffle',
            'domain': {
                'name': 'Raffle',
                'version': '1'
            },
            'message': {
                'eventName': event_name,
                'winningPlaces': event_places,
                'seed': event_seed
            }
        }

        message = encode_structured_data(primitive=msg_params)
        return w3.eth.account.sign_message(message, private_key=private_key), msg_params

    """
    random pick unique participant based on the weights
    """

    @staticmethod
    def raffle(seed, participants, weights, places):
        rng = np.random.default_rng(seed=seed)
        random_list = rng.choice(participants, p=weights, size=places, replace=False)
        if len(random_list) != len(set(random_list)):
            raise Exception("No duplicated winner")

        return random_list

    @staticmethod
    def write_result(event_name, results, file_path):
        table = pd.DataFrame(results)
        table.index = pd.RangeIndex(start=1, stop=1 + len(table), step=1)
        with open(file_path, "w") as f:
            comment = """# {}\n\n## Congratulations to the winners.\n\n""".format(event_name) + \
                      table.to_markdown() + "\n"
            f.write(comment)

    """
    convert signature to int
    """

    @staticmethod
    def signature_to_int(signature):
        return int.from_bytes(signature, 'big')


class RaffleEvent:
    """
    for released random seed, use signature to generate a new random seed.
    for live random seed event, use random seed directly
    """

    def __init__(self, event_name, event_places, random_seed, private_key_path=None):
        self.event_name = event_name
        self.event_places = event_places
        self.encrypted_seed = private_key_path is not None
        if private_key_path is None:
            self.random_seed = random_seed
        else:
            key = Raffle.get_private_key(private_key_path)
            signature, msg = Raffle.get_signature(event_name, event_places, random_seed, key)
            self.random_seed = Raffle.signature_to_int(signature.signature)
            self.signature = signature
            self.msg = msg

    def get_random_seed(self):
        return self.random_seed

    """
    random pick unique participant based on the weights
    """

    def get_raffle_result(self, event_participants, weights):
        return Raffle.raffle(self.random_seed, event_participants, weights, self.event_places)

    def export_result(self, results, path):
        Raffle.write_result(self.event_name, results, '{}/{}.md'.format(path, self.event_name))

    def get_signature(self):
        if self.encrypted_seed:
            return self.signature
        else:
            return None
