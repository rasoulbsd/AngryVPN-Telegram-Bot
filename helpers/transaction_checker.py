import requests

transaction_id = 'bf8249412c56ab861a154a55ee8757b75dfc8b77e04c156bd5058262a87c2f9e'
url = f'https://apilist.tronscan.org/api/transaction-info?hash={transaction_id}'

response = requests.get(url)

if response.status_code != 200:
    raise Exception('Failed to get transaction info')

data = response.json()

block_number = data['block']
timestamp = data['timestamp']
sender = data['ownerAddress']
receiver = data['toAddress']
amount = data['contractData']['amount']

print(data['confirmed'])
print(data['contractRet'])
print(data['contractData']['amount'])


# import tronapi
# from collections.abc import Mapping

# # Initialize the Tron API object
# full_node = 'https://api.trongrid.io'
# solidity_node = 'https://api.trongrid.io'
# event_server = 'https://api.trongrid.io'
# private_key = '<your private key>'
# tron = tronapi.Tron(full_node=full_node, solidity_node=solidity_node, event_server=event_server, private_key=private_key)

# # Get the transaction by its ID
# tx_id = 'bf8249412c56ab861a154a55ee8757b75dfc8b77e04c156bd5058262a87c2f9e'
# tx = tron.trx.get_transaction(tx_id)

# # Verify the transaction
# if tx['ret'][0]['contractRet'] == 'SUCCESS':
#     print('Transaction verified')
# else:
#     print('Transaction verification failed')

# wallet = "TUCmhBEiP6QT1jeNcYKfNzTsdXXC2QbBAc"
# transaction_id = "bf8249412c56ab861a154a55ee8757b75dfc8b77e04c156bd5058262a87c2f9e"

