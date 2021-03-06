# Lumini-blockchain-bridge
Lumini is a decentralised, trustless bridge that was intended to be used for transferring tokens between BEAM and ETH in Jan 2019. The project was scrapped because of a lack of funding, but this is the initial work done as a proof of concept between BTC and ETH. You can search for mentions of the project by the BEAM team by searching `"Lumini" "Beam"`, e.g. mentioned here https://medium.com/beam-mw/mimblewimble-beam-roadmap-2019-b2c7f38fc106

Lumini works by locking up or destroying tokens on one blockchain and minting them the another. It would require BEAM nodes to also run lite clients of blockchains it connects to.

Lumini uses a modified version of BTC where Bitcoins can actually be destroyed and minted by any user. "But what's to stop someone from minting 1B coins to themselves?" a full node in this system is both a BTC and ETH node (they can both be lite clients, but both must be run together), such that when a coin is minted on BTC, every node will check whether the corresponding coin was locked up/burned on ETH - nodes and miners will reject blocks that contain BTC transactions which mint coins that don't contain a reference to a valid burn on ETH in an `OP_RETURN` in the same tx, just like they do with double spends in regular BTC.

The verification of BTC transactions works by uploading BTC's block headers into an ETH smart contract. The contract checks the PoW of the headers to ensure they're valid. Once the contract has valid headers, any user can submit a BTC transaction, which the ETH contract will verify exists by checking the merkleproof. Only a specific user is able to 'claim' the burned tokens by referencing an address in the `OP_RETURN` of the burn transaction.

The verification of ETH transactions on BTC happens by locking the tokens in the ETH contract and specifying which BTC address is able to mint that amount. When a user mints BTC, it provides a unique reference to the locked tokens on ETH, and all nodes/miners check the ETH contract (since they're running both nodes necessarily) for that reference to consider tha transaction valid.

`checkAndMint` is the only function that is fuly implemented and tested
