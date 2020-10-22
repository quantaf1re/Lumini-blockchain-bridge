import time
from web3 import Web3, HTTPProvider
import bridgeContractABI
import btcERC20ABI
import txidList
import hashlib
from math import ceil, log
import requests as r
from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException
import binascii
import os
import argparse



# Merkleproof functions. Full credit goes to kyuupichan at https://github.com/kyuupichan/electrumx with minor edits
def sha256(x):
    '''Simple wrapper of hashlib sha256.'''
    return hashlib.sha256(x).digest()


def double_sha256(x):
    '''SHA-256 of SHA-256, as used extensively in bitcoin.'''
    return sha256(sha256(x))


def branch_length(hash_count):
    '''Return the length of a merkle branch given the number of hashes.'''
    if not isinstance(hash_count, int):
        raise TypeError('hash_count must be an integer')
    if hash_count < 1:
        raise ValueError('hash_count must be at least 1')


    return ceil(log(hash_count, 2))


def branch_and_root(hashes, index, length=None):
    '''Return a (merkle branch, merkle_root) pair given hashes, and the
    index of one of those hashes.
    '''
    hashes = list(hashes)
    if not isinstance(index, int):
        raise TypeError('index must be an integer')
    # This also asserts hashes is not empty
    if not 0 <= index < len(hashes):
        raise ValueError('index out of range')
    natural_length = branch_length(len(hashes))
    if length is None:
        length = natural_length
    else:
        if not isinstance(length, int):
            raise TypeError('length must be an integer')
        if length < natural_length:
            raise ValueError('length out of range')

    branch = []
    for _ in range(length):
        if len(hashes) & 1:
            hashes.append(hashes[-1])
        branch.append(hashes[index ^ 1])
        index >>= 1
        hashes = [double_sha256(hashes[n] + hashes[n + 1])
                  for n in range(0, len(hashes), 2)]


    return branch, hashes[0]


def hex_str_to_hash(x):
    '''Convert a displayed hex string to a binary hash.'''
    return bytes(reversed(bytes.fromhex(x)))


def hash_to_hex_str(x):
    '''Convert a big-endian binary hash to displayed hex string.
    Display form of a binary hash is reversed and converted to hex.
    '''
    return bytes(reversed(x)).hex()


def get_merkle_branch(tx_hashes, tx_pos):
    '''Return a merkle branch to a transaction.
    tx_hashes: ordered list of hex strings of tx hashes in a block
    tx_pos: index of transaction in tx_hashes to create branch for
    '''
    hashes = [hex_str_to_hash(hash) for hash in tx_hashes]
    branch, root = branch_and_root(hashes, tx_pos)
    branch = [hash_to_hex_str(hash) for hash in branch]
    return branch


def reverseBytes(str):
    rev = [str[i:i + 2] for i in range(0, len(str), 2)]
    rev.reverse()
    return ''.join(rev)


def generateFinalProof(txidListBE, txidBE, merklerootLE):
    '''Return a hex string of the final merkleproof including the original txid at the beginning and the merkleroot
    at the end, all in little endian (LE)
    txidListBE: a list of txid's in a block in big endian (BE) - supplied by the RPC in this form
    txidBE: the original txid that the proof is being generated for in big endian - supplied by te RPC in this form
    merklerootLE: the merkleroot in little endian - supplied in the block header in this form
    '''

    indexOfTxid = txidListBE.index(txidBE)
    # Get the merkleproof branch
    branchBE = get_merkle_branch(txidListBE, indexOfTxid)
    # Reverse the bytes order to change to little endian
    branchLE = [reverseBytes(hash) for hash in branchBE]
    # Join the list into a string
    branchStringLE = ''.join(branchLE)
    # Add the txid in little endian to the beginning of the proof and the LE merkleproof to the end
    return reverseBytes(txidBE) + branchStringLE + merklerootLE

def uploadHeader(rawHeader):
    # Build tx
    txnDict = bridgeContract.functions.parseAndStoreHeader(rawHeader).buildTransaction(
        {
            'chainId': 3,
            'gas': 1000000,
            'gasPrice': w3.toWei(gasPriceGWei, 'gwei'),
            'nonce': w3.eth.getTransactionCount(walletAddress),
        })
    signedTxn = w3.eth.account.signTransaction(txnDict, private_key=walletPrivateKey)
    result = w3.eth.sendRawTransaction(signedTxn.rawTransaction)
    print(result)
    txReceipt = w3.eth.getTransactionReceipt(result)
    print(txReceipt)

    count = 0
    while txReceipt is None and (count < 30):
        print('Attempt {}'.format(count))
        count += 1
        time.sleep(10)

        txReceipt = w3.eth.getTransactionReceipt(result)

    if txReceipt is None:
        return {'status': 'failed', 'error': 'timeout'}

    print('Success')
    processedReceipt = bridgeContract.events.HeaderStored().processReceipt(txReceipt)

    return {'status': 'added', 'processed_receipt': processedReceipt }

def checkAndMint(_tx, _tokenAddress):
    # Build tx
    txnDict = bridgeContract.functions.checkAndMint(_tx, _tokenAddress).buildTransaction(
        {
            'chainId': 3,
            'gas': 1000000,
            'gasPrice': w3.toWei(gasPriceGWei, 'gwei'),
            'nonce': w3.eth.getTransactionCount(walletAddress),
        })
    signedTxn = w3.eth.account.signTransaction(txnDict, private_key=walletPrivateKey)
    result = w3.eth.sendRawTransaction(signedTxn.rawTransaction)
    print(bytes.hex(result))
    txReceipt = w3.eth.getTransactionReceipt(result)
    print(txReceipt)

    count = 0
    while txReceipt is None and (count < 30):
        print('Attempt {}'.format(count))
        count += 1
        time.sleep(10)

        txReceipt = w3.eth.getTransactionReceipt(result)

    if txReceipt is None:
        return {'status': 'failed', 'error': 'timeout'}

    print('Success')
    processedReceipt = bridgeContract.events.Minted().processReceipt(txReceipt)

    return {'status': 'added', 'processed_receipt': processedReceipt }

def approve(_amount):
    # Build tx
    txnDict = btcContract.functions.approve(contractAddress, _amount).buildTransaction(
        {
            'chainId': 3,
            'gas': 1000000,
            'gasPrice': w3.toWei(gasPriceGWei, 'gwei'),
            'nonce': w3.eth.getTransactionCount(walletAddress),
        })
    signedTxn = w3.eth.account.signTransaction(txnDict, private_key=walletPrivateKey)
    result = w3.eth.sendRawTransaction(signedTxn.rawTransaction)
    print(bytes.hex(result))
    txReceipt = w3.eth.getTransactionReceipt(result)
    print(txReceipt)

    count = 0
    while txReceipt is None and (count < 30):
        print('Attempt {}'.format(count))
        count += 1
        time.sleep(10)

        txReceipt = w3.eth.getTransactionReceipt(result)

    if txReceipt is None:
        return {'status': 'failed', 'error': 'timeout'}

    print('Success')
    processedReceipt = btcContract.events.Approval().processReceipt(txReceipt)

    return {'status': 'added', 'processed_receipt': processedReceipt }

def addUTXO(_tx):
    cmd = ' '.join([rpcPrefic, 'zzz ', _tx, ' x'])
    response = os.popen(cmd).read()
    return response

def getblockcount():
    cmd = ' '.join([rpcPrefic, 'getblockcount'])
    response = os.popen(cmd).read()
    return int(response)

def mintAuto(_tx):
    node = AuthServiceProxy(nodeCredentials)
    # Can move this to an in-line if statement later
    val = int(node.decoderawtransaction(_tx, True)['vout'][0]['value'] * 10**18)
    print(val)
    approveResult = approve(val)
    print(approveResult)
    if approveResult['status'] == 'added':
        checkAndMintResult = checkAndMint(_tx, btcContractAddress)
        print(checkAndMintResult)
        if checkAndMintResult['status'] == 'added':
            addUTXO(_tx)
            return True

    return False

def uploadBurnProof(_blockHash, _merkleProof, _indexOfTxInBlock, _outputIndexOfBurn, _tx):
    # Build tx
    txnDict = bridgeContract.functions.withdrawTokens(
        _blockHash, _merkleProof, _indexOfTxInBlock, _outputIndexOfBurn, _tx).buildTransaction(
        {
            'chainId': 3,
            'gas': 1000000,
            'gasPrice': w3.toWei(gasPriceGWei, 'gwei'),
            'nonce': w3.eth.getTransactionCount(walletAddress),
        })
    signedTxn = w3.eth.account.signTransaction(txnDict, private_key=walletPrivateKey)
    result = w3.eth.sendRawTransaction(signedTxn.rawTransaction)
    print(bytes.hex(result))
    txReceipt = w3.eth.getTransactionReceipt(result)
    print(txReceipt)

    count = 0
    while txReceipt is None and (count < 30):
        print('Attempt {}'.format(count))
        count += 1
        time.sleep(10)

        txReceipt = w3.eth.getTransactionReceipt(result)

    if txReceipt is None:
        return {'status': 'failed', 'error': 'timeout'}

    print('Success')
    processedReceipt = bridgeContract.events.Redeemed().processReceipt(txReceipt)

    return {'status': 'added', 'processed_receipt': processedReceipt}
    

def burnAuto(_tx):
    node = AuthServiceProxy(nodeCredentials)
    node.sendrawtransaction(_tx, True)
    node.generatetoaddress(1, "bcrt1qc9hmvr5p338dtupsgfaj9l2yzwxsp5grgpd5zq")
    bestBlockHash = node.getbestblockhash()
    block = node.getblock(bestBlockHash)
    rawHeader = node.getblockheader(bestBlockHash, False)
    uploadHeaderResult = uploadHeader(rawHeader)
    print(uploadHeaderResult)
    if uploadHeaderResult['status'] == 'added':
        node = AuthServiceProxy(nodeCredentials)
        bestBlockHash = node.getbestblockhash()
        block = node.getblock(bestBlockHash)
        txid = node.decoderawtransaction(_tx, True)['txid']
        merkleRootLE = reverseBytes(block['merkleroot'])
        merkleProof = generateFinalProof(block['tx'], txid, merkleRootLE)
        indexOfTxInBlock = block['tx'].index(txid) + 1
        burnProofResult = uploadBurnProof(block['hash'], merkleProof, indexOfTxInBlock, 0, _tx)
        print(burnProofResult)
        if burnProofResult['status'] == 'added':
            return True

        return False

    
    
sleepTime = 600
contractAddress = 'REPLACE'
btcContractAddress = 'REPLACE'
# This doesn't have any valuable Eth in it....sorry :)
walletPrivateKey = 'REPLACE'   # maybe has to be upper case?
walletAddress = 'REPLACE'
w3 = Web3(HTTPProvider('REPLACE'))           # this being Ropsten is probably why Kovan won't work

w3.eth.enable_unaudited_features()
contractAddress = w3.toChecksumAddress(contractAddress)
btcContractAddress = w3.toChecksumAddress(btcContractAddress)
walletAddress = w3.toChecksumAddress(walletAddress)

bridgeContract = w3.eth.contract(address = contractAddress, abi = bridgeContractABI.ABI)
btcContract = w3.eth.contract(address = btcContractAddress, abi = btcERC20ABI.ABI)
gasPriceGWei = 3

nodeCredentials = "http://user:pass@127.0.0.1:18003"
rpcPrefic = '/home/main/stableunit/btc8/bitcoin/src/bitcoin-cli -conf=/home/main/stableunit/btc8/bitcoin.conf '

parser = argparse.ArgumentParser()
parser.add_argument("-m", "--mintBtc", dest = "mintTx", default = None,
                    help="The transaction whose output will be minted on the btc chain, inputs in it are meaningless and"
                         " will not be needed soon.")
parser.add_argument("-b", "--burnBtc", dest = "burnTx", default = None, help="The transaction containing the burned coins")
args = parser.parse_args()


if args.mintTx is not None:
    print(mintAuto(args.mintTx))
if args.burnTx is not None:
    print(burnAuto(args.burnTx))
